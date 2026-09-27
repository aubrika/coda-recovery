"""Regression tests for conditional baselines, grouped scoring, and transfer."""
import numpy as np

from coda_recovery.predictive_info import held_out_gain, _gain


def _pairs(next_fn, n_units=10, per_unit=80, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for u in range(n_units):
        for _ in range(per_unit):
            a = int(rng.integers(0, 5))
            out.append((f"u{u}", a, next_fn(a, rng)))
    return out


def test_deterministic_next_is_predicted():
    # next = (current + 1) mod 5 — perfectly predictable, and never a self-repeat
    pairs = _pairs(lambda a, rng: (a + 1) % 5)
    (mt, ml, mh), (tt, tl, th), n, V = held_out_gain(pairs)
    assert ml > 0.5, f"total MI lower bound should be well above 0, got {ml}"
    assert tl > 0.0, f"transition-only MI should be positive, got {tl}"


def test_independent_next_is_not_predicted():
    # next drawn independently of current — no predictive information
    pairs = _pairs(lambda a, rng: int(rng.integers(0, 5)))
    (mt, ml, mh), (ct, cl, ch), n, V = held_out_gain(pairs)
    assert ch < 0.1, f"independent changes must not gain from excluding the source: {ch}"
    assert mh < 0.2, f"total MI upper bound should be near 0, got {mh}"


def test_loco_rewards_shared_rule_and_punishes_clan_specific():
    """A rule shared across clans transfers to a held-out clan (positive);
    a per-clan-scrambled rule does not (a foreign model mispredicts)."""
    from coda_recovery.universal_structure import loco_gain

    def build(rule):  # rule(clan, a, rng) -> next token; clans "c0".."c3"
        rng = np.random.default_rng(1)
        pairs = {}
        for k in range(4):
            c = f"c{k}"
            pr = []
            for u in range(8):
                for _ in range(120):
                    a = int(rng.integers(0, 5))
                    pr.append((f"{c}:u{u}", a, rule(k, a, rng)))
            pairs[c] = pr
        return pairs

    shared = build(lambda k, a, rng: (a + 1) % 5)          # same rule in every clan
    specific = build(lambda k, a, rng: (a + 1 + k) % 5)    # each clan shifts differently
    assert loco_gain("c0", shared, transition_only=True) > 0.3
    assert loco_gain("c0", specific, transition_only=True) < 0


def test_balanced_independent_changes_have_zero_gain():
    # The old implementation returned about +0.32 bits solely from filtering a == b.
    pairs = [(str(u), a, b) for u in range(10) for a in range(5) for b in range(5)]
    scores = _gain(pairs[:125], pairs[125:], set(range(5)), transition_only=True)
    assert abs(np.mean(scores)) < 1e-12


def test_nonuniform_independent_changes_have_near_zero_gain():
    pairs = [(str(u), a, b) for u in range(10) for a in range(3) for b in range(3)
             for _ in range((a + 1) * (b + 1) * 20)]
    total, changes, _, _ = held_out_gain(pairs, n_boot=20)
    assert abs(total[0]) < 0.001
    assert abs(changes[0]) < 0.001


def test_binary_changes_carry_no_gain_once_exclusion_is_known():
    pairs = [(str(u), a, 1 - a) for u in range(10) for a in (0, 1)]
    total, changes, _, _ = held_out_gain(pairs, n_boot=20)
    assert total[0] > 0.5
    assert changes == (0.0, 0.0, 0.0)


def test_recording_bootstrap_refits_and_is_reproducible(monkeypatch):
    import coda_recovery.predictive_info as core
    original = core.log_gain_matrix
    fitted = []
    def record_fit(train, *args, **kwargs):
        fitted.append(train.copy())
        return original(train, *args, **kwargs)
    monkeypatch.setattr(core, "log_gain_matrix", record_fit)
    pairs = _pairs(lambda a, rng: int(rng.integers(0, 5)), n_units=20)
    first = held_out_gain(pairs, n_boot=30)
    assert len(fitted) == 31 * 5 * 2
    assert any(not np.array_equal(fitted[0], other) for other in fitted[10::10])
    assert first == held_out_gain(pairs, n_boot=30)
    assert first[0][2] > first[0][1]


def test_folds_keep_recordings_disjoint():
    from coda_recovery.predictive_info import recording_folds
    folds = recording_folds(list(range(23)))
    assert sorted(np.concatenate(folds).tolist()) == list(range(23))
    for i, fold in enumerate(folds):
        assert not set(fold) & set(np.concatenate([f for j, f in enumerate(folds) if j != i]))


def test_insufficient_recordings_and_no_changes():
    import pytest
    with pytest.raises(ValueError, match="two recordings"):
        held_out_gain([("one", 0, 1)])
    _, changes, _, _ = held_out_gain([(str(u), 0, 0) for u in range(10)], n_boot=20)
    assert all(np.isnan(x) for x in changes)


def test_loco_independent_changes_do_not_transfer_artificially():
    from coda_recovery.universal_structure import loco_gain
    pairs = {c: [(str(u), a, b) for u in range(10) for a in range(5) for b in range(5)]
             for c in ("a", "b", "c")}
    assert abs(loco_gain("a", pairs, transition_only=True)) < 1e-12

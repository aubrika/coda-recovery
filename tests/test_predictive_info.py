"""Sanity tests for the held-out mutual-information core (the project's one metric).

A deterministic next-token must show strongly positive cross-validated MI (total
and transition-only); an independent next-token must show ~none. If either flips,
the MI estimator is broken.
"""
import numpy as np

from coda_recovery.predictive_info_sweep import held_out_mi


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
    (mt, ml, mh), (tt, tl, th), n, V = held_out_mi(pairs)
    assert ml > 0.5, f"total MI lower bound should be well above 0, got {ml}"
    assert tl > 0.0, f"transition-only MI should be positive, got {tl}"


def test_independent_next_is_not_predicted():
    # next drawn independently of current — no predictive information
    pairs = _pairs(lambda a, rng: int(rng.integers(0, 5)))
    (mt, ml, mh), _, n, V = held_out_mi(pairs)
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

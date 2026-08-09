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

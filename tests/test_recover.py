"""Correctness tests for the recovery machinery (spec Section 12).

The load-bearing one is test_qap_objective_vs_bruteforce: it proves the scipy
QAP call is actually optimising ||P TA P^T - TB||_F and not its sign-flip.
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import orthogonal_procrustes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coda_recovery.recover import (  # noqa: E402
    qap_recover,
    procrustes_recover,
    frobenius_objective,
    perm_to_matrix,
    frequency_rank_baseline,
    accuracy_at_1,
)


def brute_force_min(TA, TB):
    """Exhaustive min of ||P TA P^T - TB||_F over all permutations."""
    n = TA.shape[0]
    best_obj, best_perm = np.inf, None
    for perm in itertools.permutations(range(n)):
        perm = np.array(perm)
        obj = frobenius_objective(perm_to_matrix(perm), TA, TB)
        if obj < best_obj:
            best_obj, best_perm = obj, perm
    return best_obj, best_perm


@pytest.mark.parametrize("n,seed", [(5, 1), (6, 2), (7, 3)])
def test_qap_objective_vs_bruteforce(n, seed):
    """QAP must find the true global-min objective on a small exact-recoverable
    problem: TB = P_true TA P_true^T, so the minimum objective is 0."""
    rng = np.random.default_rng(seed)
    C = rng.integers(0, 8, size=(n, n)).astype(float)
    TA = (C + 0.5) / (C + 0.5).sum(1, keepdims=True)
    p_true = rng.permutation(n)
    P = perm_to_matrix(p_true)
    TB = P @ TA @ P.T

    bf_obj, _ = brute_force_min(TA, TB)
    assert bf_obj == pytest.approx(0.0, abs=1e-9)

    rec = qap_recover(TA, TB, n_restarts=40, seed=seed)
    # Must recover a zero-objective solution (the sign convention is correct).
    assert rec.objective == pytest.approx(0.0, abs=1e-8)
    # And on a permuted-identical problem that means the exact inverse perm.
    assert np.array_equal(rec.perm, p_true)


def test_qap_matches_bruteforce_on_noisy_problem():
    """With noise there is no zero solution; QAP's best objective must still
    equal the brute-force global minimum (n small enough to enumerate)."""
    n, seed = 6, 11
    rng = np.random.default_rng(seed)
    TA = rng.random((n, n)); TA /= TA.sum(1, keepdims=True)
    TB = rng.random((n, n)); TB /= TB.sum(1, keepdims=True)
    bf_obj, _ = brute_force_min(TA, TB)
    rec = qap_recover(TA, TB, n_restarts=60, seed=seed)
    assert rec.objective >= bf_obj - 1e-9
    assert rec.objective == pytest.approx(bf_obj, abs=1e-6)


def test_procrustes_arm_mechanics_and_beats_random():
    """The Procrustes arm is an APPROXIMATE optimiser (see its docstring): naive
    unsupervised embedding-matching does not reach the QAP global optimum even on
    clean spectra — that fragility is the spec's reason QAP is primary. So we
    test what must hold: it returns a valid permutation, exposes the spectrum,
    and clearly beats a random relabelling. We do NOT assert exact recovery."""
    from coda_recovery.nulls import random_permutation_null

    n, seed = 8, 7
    rng = np.random.default_rng(seed)
    M = rng.random((n, n)); S = M @ M.T
    T = S / S.sum(1, keepdims=True)
    p_true = rng.permutation(n)
    P = perm_to_matrix(p_true)
    TB = P @ T @ P.T

    rec, spec = procrustes_recover(T, TB, d=n - 1, seed=seed)
    assert spec.shape == (n,)
    assert sorted(rec.perm.tolist()) == list(range(n))     # valid permutation
    null = random_permutation_null(T, TB, n=500, seed=seed)
    assert rec.objective < np.percentile(null, 5)          # beats random clearly


def test_orthogonal_procrustes_reference():
    """Sanity-check our Procrustes usage against scipy directly."""
    rng = np.random.default_rng(3)
    X = rng.random((10, 4))
    Q, _ = np.linalg.qr(rng.random((4, 4)))
    Y = X @ Q
    R, _ = orthogonal_procrustes(X, Y)
    assert np.allclose(R, Q, atol=1e-8)


def test_frequency_baseline_is_identity_when_ranks_agree():
    """If both halves share the same frequency ordering, the baseline is the
    identity — this is exactly why it is a strong control (spec 6.1)."""
    n = 6
    diag = np.arange(n, 0, -1)                    # strictly decreasing marginals
    CA = np.diag(diag).astype(float) + 0.0
    CB = CA.copy()
    perm = frequency_rank_baseline(CA, CB)
    assert accuracy_at_1(perm) == 1.0

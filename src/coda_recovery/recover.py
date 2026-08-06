"""Permutation recovery and its metrics (spec Section 5.3, 5.5, 6.1).

Primary arm: QAP graph matching via scipy.optimize.quadratic_assignment.
We seek a permutation P minimising ||P T_A P^T - T_B||_F. scipy's FAQ solves
the *trace* form  min_P trace(A P B^T P^T)  (a maximisation of similarity when
fed similarity matrices). The Frobenius objective expands to

    ||P T_A P^T - T_B||^2 = ||T_A||^2 + ||T_B||^2 - 2 * trace(P T_A P^T T_B^T)

so minimising the Frobenius distance == maximising trace(P T_A P^T T_B^T). scipy
minimises trace(A P B^T P^T); feeding A=T_A, B=T_B and maximize=True gives exactly
our objective. We verify this equivalence against brute force in the tests — do
not trust it on the strength of this comment.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import quadratic_assignment, linear_sum_assignment
from scipy.linalg import orthogonal_procrustes


def frobenius_objective(P: np.ndarray, TA: np.ndarray, TB: np.ndarray) -> float:
    """||P TA P^T - TB||_F, with P a permutation matrix."""
    return float(np.linalg.norm(P @ TA @ P.T - TB))


def perm_to_matrix(perm: np.ndarray) -> np.ndarray:
    n = len(perm)
    P = np.zeros((n, n))
    P[np.arange(n), perm] = 1.0
    return P


@dataclass
class Recovery:
    perm: np.ndarray        # perm[i] = index in B that row i of A maps to
    objective: float
    n_restarts: int
    all_objectives: list[float]   # objective from every restart (restart spread)


def qap_recover(
    TA: np.ndarray,
    TB: np.ndarray,
    n_restarts: int = 30,
    seed: int = 0,
    refine_2opt: bool = True,
) -> Recovery:
    """Recover the relabelling A->B by QAP. FAQ from many random starts, then a
    2opt polish from the best (spec 5.3). Reports the objective of every restart
    so restart sensitivity is visible rather than cherry-picked (trap in 9)."""
    rng = np.random.default_rng(seed)
    best = None
    objs = []
    # scipy FAQ maximises trace(A^T P B P^T) = sum_ij A[i,j] B[sigma(i),sigma(j)].
    # We want sigma minimising ||P TA P^T - TB||, i.e. maximising
    # sum_ij TB[i,j] TA[sigma(i),sigma(j)] -> call with A=TB, B=TA. Verified
    # against brute force in tests (a (TA,TB) call silently returns sigma^-1).
    for r in range(n_restarts):
        P0 = "randomized" if r > 0 else "barycenter"
        res = quadratic_assignment(
            TB, TA, method="faq", options={"maximize": True, "P0": P0, "rng": rng}
        )
        obj = frobenius_objective(perm_to_matrix(res.col_ind), TA, TB)
        objs.append(obj)
        if best is None or obj < best.objective:
            best = Recovery(res.col_ind, obj, n_restarts, [])

    if refine_2opt and best is not None:
        res2 = quadratic_assignment(
            TB, TA, method="2opt",
            options={"maximize": True, "partial_guess": np.c_[np.arange(len(TA)), best.perm]},
        )
        obj2 = frobenius_objective(perm_to_matrix(res2.col_ind), TA, TB)
        if obj2 <= best.objective:
            best = Recovery(res2.col_ind, obj2, n_restarts, objs)
        else:
            best.all_objectives = objs
    else:
        best.all_objectives = objs
    return best


def _spectral_embed(T: np.ndarray, d: int):
    """Symmetrised spectral embedding into d dims, scaled by sqrt(|eigval|).
    Returns (X, full_spectrum_descending)."""
    S = 0.5 * (T + T.T)
    w, V = np.linalg.eigh(S)
    order = np.argsort(w)[::-1]
    w, V = w[order], V[:, order]
    return V[:, :d] * np.sqrt(np.abs(w[:d])), w


def procrustes_recover(
    TA: np.ndarray,
    TB: np.ndarray,
    d: int,
    seed: int = 0,
    n_restarts: int = 12,
    max_iter: int = 60,
) -> tuple[Recovery, np.ndarray]:
    """Secondary arm (spec 5.4): spectral embedding -> Procrustes -> Hungarian.

    Post-embedding the basis is arbitrary so a rotation is legitimate — but the
    correspondence needed to *fit* that rotation is the unknown. So we alternate
    (ICP / unsupervised-Procrustes style): given an assignment, solve the
    orthogonal map on matched pairs; given the map, reassign by Hungarian;
    iterate to a fixed point, from several restarts. The embedding pins node
    identity only up to inversion (XB = P XA D), so each restart is scored on
    both its permutation and that permutation's inverse; the lower Frobenius wins.

    IMPORTANT — this arm is an approximate optimiser, not a global one. On flat
    or near-degenerate spectra (which real coda transitions have) the alternation
    gets trapped in local minima; empirically it does not match FAQ/2opt even on
    clean synthetic problems with well-separated spectra. That fragility is the
    spec's own stated reason (5.3) QAP is the correct primary formulation. Treat
    this arm as the MUSE-analogue comparison, read against QAP, never as ground
    truth. Returns the best recovery and TA's symmetrised eigenvalue spectrum
    (steep vs flat tells you whether a low-d embedding discards much — 5.4 / 8.1)."""
    XA, specA = _spectral_embed(TA, d)
    XB, _ = _spectral_embed(TB, d)
    n = TA.shape[0]
    rng = np.random.default_rng(seed)

    def assign(R):
        cost = np.linalg.norm((XA @ R)[:, None, :] - XB[None, :, :], axis=2)
        row, col = linear_sum_assignment(cost)
        perm = np.empty(n, dtype=int)
        perm[row] = col
        return perm

    best = None
    for r in range(n_restarts):
        perm = np.arange(n) if r == 0 else rng.permutation(n)
        for _ in range(max_iter):
            R, _ = orthogonal_procrustes(XA, XB[perm])  # pair XA[i]<->XB[perm[i]]
            new = assign(R)
            if np.array_equal(new, perm):
                break
            perm = new
        # Embedding fixes identity only up to inversion: score both directions.
        for cand in (perm, np.argsort(perm)):
            obj = frobenius_objective(perm_to_matrix(cand), TA, TB)
            if best is None or obj < best.objective:
                best = Recovery(cand.copy(), obj, n_restarts, [])
    return best, specA


# ---- baselines & metrics -------------------------------------------------

def frequency_rank_baseline(CA: np.ndarray, CB: np.ndarray) -> np.ndarray:
    """THE control (spec 6.1). Match types by marginal-frequency rank: the r-th
    most frequent type in A maps to the r-th most frequent in B. Uses NO
    structural information. Returns perm[i] = B-index that A-index i maps to."""
    fa = CA.sum(axis=1) + CA.sum(axis=0)
    fb = CB.sum(axis=1) + CB.sum(axis=0)
    rank_a = np.argsort(np.argsort(-fa))   # rank of each A type (0 = most frequent)
    order_b = np.argsort(-fb)              # B indices sorted most->least frequent
    perm = np.empty(len(fa), dtype=int)
    for i in range(len(fa)):
        perm[i] = order_b[rank_a[i]]
    return perm


def accuracy_at_1(perm: np.ndarray) -> float:
    """Fraction of types mapped to themselves (ground truth is identity because
    both halves come from the same clan)."""
    return float(np.mean(perm == np.arange(len(perm))))


def freq_weighted_accuracy(perm: np.ndarray, weights: np.ndarray) -> float:
    """accuracy@1 weighted by type frequency (spec 5.5). The gap to unweighted
    accuracy *is* the rare-type story."""
    correct = (perm == np.arange(len(perm))).astype(float)
    return float(np.sum(correct * weights) / np.sum(weights))

"""The three recovery experiments over the factored (rhythm, tempo) tokens
(coda-4d-data-model.md Section 7), all through the same paired real-vs-shuffled
control used elsewhere.

  7.1 JOINT     — QAP over the top-K attested (rhythm, tempo) cells. Directly
                  comparable to the 21-legacy-type run.
  7.3 MARGINAL  — collapse to rhythm alone (top-K rhythms) or tempo alone (5×5).
                  Which AXIS carries the sequence signal? (cheapest; run first)
  7.2 FACTORED  — Kronecker-constrained permutation P = P_rhythm ⊗ P_tempo over a
                  small rhythm×tempo grid. Do the axes occupy SEPARABLE sequential
                  roles? Compared against the unconstrained (joint) recovery on the
                  same grid. The Kronecker optimum is found by exhaustive search
                  over P_rhythm × P_tempo (validated in tests).

Transitions come from single-whale call sequences (consecutive same-speaker codas
≤ 8 s apart — the paper's rule, using Dataset 2's real timestamps). The shuffle
null permutes coda order WITHIN each sequence (composition preserved, order
destroyed). Ground truth is the identity. FIREWALL: only the token identity and
its transitions enter the matcher — never rhythm/tempo/duration as node features.
"""
from __future__ import annotations

import csv
import itertools
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from .coda_model import load, SEQUENCE_GAP_S, N_TEMPO
from .transitions import row_normalise
from .recover import qap_recover, accuracy_at_1, frequency_rank_baseline, frobenius_objective, perm_to_matrix

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "factored_recovery.csv"
NREP = 30
QAP_RESTARTS = 25


def factored_df() -> pd.DataFrame:
    return pd.DataFrame([vars(c) for c in load()])


def single_whale_sequences(df: pd.DataFrame) -> list[list[dict]]:
    """Split into single-whale call sequences (same speaker, consecutive ≤ 8 s)."""
    seqs = []
    for _, g in df.sort_values(["deployment", "speaker", "t_start"]).groupby(
            ["deployment", "speaker"], sort=False):
        rows = g.to_dict("records")
        cur = [rows[0]]
        for prev, row in zip(rows, rows[1:]):
            if row["t_start"] - prev["t_start"] <= SEQUENCE_GAP_S:
                cur.append(row)
            else:
                seqs.append(cur); cur = [row]
        seqs.append(cur)
    return seqs


def _tokfn(mode):
    return {"joint": lambda r: (r["rhythm"], r["tempo"]),
            "rhythm": lambda r: r["rhythm"],
            "tempo": lambda r: r["tempo"]}[mode]


def _pairs(seqs, tokfn, rng=None):
    """Adjacent token pairs within sequences; if rng given, shuffle order first."""
    out = []
    for seq in seqs:
        toks = [tokfn(r) for r in seq]
        if rng is not None:
            rng.shuffle(toks)
        out += list(zip(toks[:-1], toks[1:]))
    return out


def _cmat(pairs, index):
    idx = {t: i for i, t in enumerate(index)}
    n = len(index)
    C = np.zeros((n, n))
    for a, b in pairs:
        if a in idx and b in idx:
            C[idx[a], idx[b]] += 1
    return C


def _norm(C, off_diagonal=False):
    """Row-stochastic transition matrix; optionally zero self-repetition first, so
    only genuine token-A -> different-token-B structure remains (the 'syntax' cut,
    since whales repeat tokens heavily — the diagonal otherwise dominates)."""
    if off_diagonal:
        C = C.copy()
        np.fill_diagonal(C, 0)
    return row_normalise(C, 1.0)


def _token_index(seqs, mode, k):
    tokfn = _tokfn(mode)
    c = Counter(tokfn(r) for seq in seqs for r in seq)
    return [t for t, _ in c.most_common(k)]


def _bootstrap_ci(x, seed=0):
    rng = np.random.default_rng(seed)
    bs = [np.mean(rng.choice(x, len(x), replace=True)) for _ in range(5000)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


# ---- 7.1 joint & 7.3 marginal: paired real-vs-shuffled -------------------

def _dep_split(deps, rng):
    d = np.array(sorted(deps)); rng.shuffle(d)
    return set(d[:len(d) // 2]), set(d[len(d) // 2:])


def paired_recovery(df, mode, k, off_diagonal=False):
    seqs_all = single_whale_sequences(df)
    index = _token_index(seqs_all, mode, k)
    tokfn = _tokfn(mode)
    deps = df["deployment"].unique()
    obs, null, dens = [], [], []
    for r in range(NREP):
        A, B = _dep_split(deps, np.random.default_rng(r))
        sA = [s for s in seqs_all if s[0]["deployment"] in A]
        sB = [s for s in seqs_all if s[0]["deployment"] in B]
        Ca = _cmat(_pairs(sA, tokfn), index); Cb = _cmat(_pairs(sB, tokfn), index)
        dens.append(0.5 * (Ca.sum() + Cb.sum()) / len(index) ** 2)
        obs.append(accuracy_at_1(qap_recover(_norm(Ca, off_diagonal), _norm(Cb, off_diagonal),
                                             n_restarts=QAP_RESTARTS, seed=r).perm))
        Na = _cmat(_pairs(sA, tokfn, np.random.default_rng(100 + r)), index)
        Nb = _cmat(_pairs(sB, tokfn, np.random.default_rng(200 + r)), index)
        null.append(accuracy_at_1(qap_recover(_norm(Na, off_diagonal), _norm(Nb, off_diagonal),
                                              n_restarts=QAP_RESTARTS, seed=r).perm))
    obs, null = np.array(obs), np.array(null)
    diff = obs - null
    lo, hi = _bootstrap_ci(diff)
    return {"experiment": mode, "cut": "syntax" if off_diagonal else "full",
            "k": len(index), "trans_per_cell": round(float(np.mean(dens)), 2),
            "real": round(float(obs.mean()), 4), "shuffled": round(float(null.mean()), 4),
            "paired_diff": round(float(diff.mean()), 4),
            "diff_lo": round(lo, 4), "diff_hi": round(hi, 4), "survives": bool(lo > 0)}


# ---- 7.2 factored: Kronecker P = P_rhythm ⊗ P_tempo ----------------------

def _kron_perms(R, T):
    """All induced token permutations for a (rhythm, tempo) grid of R×T tokens,
    in grid order i = r*T + t, from P_rhythm × P_tempo. Precomputed once."""
    perms = []
    for pr in itertools.permutations(range(R)):
        for pt in itertools.permutations(range(T)):
            p = np.empty(R * T, dtype=int)
            for a in range(R):
                for b in range(T):
                    p[a * T + b] = pr[a] * T + pt[b]
            perms.append(p)
    return np.array(perms)


def factored_recover(TA, TB, R, T, kron_perms=None, rng=None):
    """Exhaustive Kronecker-constrained recovery: best (P_rhythm ⊗ P_tempo). Ties
    (common when the sparse grid has empty/uniform rows) are broken at random, not
    by preferring the identity — otherwise accuracy is trivially inflated to 1.0."""
    P = _kron_perms(R, T) if kron_perms is None else kron_perms
    objs = np.array([np.linalg.norm(TA[np.ix_(p, p)] - TB) for p in P])
    best = objs.min()
    tied = np.where(objs <= best + 1e-9)[0]
    pick = (rng or np.random.default_rng(0)).choice(tied)
    return P[pick], float(best)


def factored_experiment(df, R=4, nrep=20, off_diagonal=False):
    """On a top-R-rhythm × 5-tempo grid: paired real-vs-shuffled recovery for BOTH
    the unconstrained (joint) matcher and the Kronecker-constrained (factored) one.
    If factored tracks joint (similar real−shuffled margins), the (rhythm,tempo)
    factorisation is preserved in sequence; if factored's margin is much smaller,
    sequential roles attach to specific combinations rather than the axes."""
    seqs_all = single_whale_sequences(df)
    rc = Counter(r["rhythm"] for seq in seqs_all for r in seq)
    top_r = [r for r, _ in rc.most_common(R)]
    index = [(r, t) for r in top_r for t in range(N_TEMPO)]   # grid order
    tokfn = lambda row: (row["rhythm"], row["tempo"])
    kron = _kron_perms(R, N_TEMPO)
    deps = df["deployment"].unique()
    jd, fd, dens = [], [], []
    for r in range(nrep):
        A, B = _dep_split(deps, np.random.default_rng(r))
        sA = [s for s in seqs_all if s[0]["deployment"] in A]
        sB = [s for s in seqs_all if s[0]["deployment"] in B]
        Car, Cbr = _cmat(_pairs(sA, tokfn), index), _cmat(_pairs(sB, tokfn), index)
        Cas = _cmat(_pairs(sA, tokfn, np.random.default_rng(100 + r)), index)
        Cbs = _cmat(_pairs(sB, tokfn, np.random.default_rng(200 + r)), index)
        dens.append(0.5 * (Car.sum() + Cbr.sum()) / len(index) ** 2)
        TAr, TBr = _norm(Car, off_diagonal), _norm(Cbr, off_diagonal)
        TAs, TBs = _norm(Cas, off_diagonal), _norm(Cbs, off_diagonal)
        jr = accuracy_at_1(qap_recover(TAr, TBr, n_restarts=QAP_RESTARTS, seed=r).perm)
        js = accuracy_at_1(qap_recover(TAs, TBs, n_restarts=QAP_RESTARTS, seed=r).perm)
        fr = accuracy_at_1(factored_recover(TAr, TBr, R, N_TEMPO, kron, np.random.default_rng(r))[0])
        fs = accuracy_at_1(factored_recover(TAs, TBs, R, N_TEMPO, kron, np.random.default_rng(9 + r))[0])
        jd.append(jr - js); fd.append(fr - fs)
    jd, fd = np.array(jd), np.array(fd)
    jl, jh = _bootstrap_ci(jd); fl, fh = _bootstrap_ci(fd)
    return {"experiment": f"factored({R}x{N_TEMPO})", "cut": "syntax" if off_diagonal else "full",
            "k": len(index), "trans_per_cell": round(float(np.mean(dens)), 2),
            "joint_paired_diff": round(float(jd.mean()), 4), "joint_lo": round(jl, 4), "joint_hi": round(jh, 4),
            "factored_paired_diff": round(float(fd.mean()), 4), "factored_lo": round(fl, 4), "factored_hi": round(fh, 4)}


def main():
    df = factored_df()
    print("Factored-model recovery — Dataset 2, single-whale sequences (≤8s), "
          f"{NREP} paired reps. 'full' includes self-repetition; 'syntax' removes it.\n")
    rows = []
    print("=== 7.3 marginal (which axis?) + 7.1 joint — paired real vs shuffled ===")
    print(f"{'experiment':<10}{'cut':>7}{'k':>4}{'t/cell':>8}{'real':>7}{'shuf':>7}"
          f"{'real−shuf (95% CI)':>23}{'':>4}")
    for mode, k in [("tempo", 5), ("rhythm", 10), ("joint", 15)]:
        for od in (False, True):
            r = paired_recovery(df, mode, k, off_diagonal=od)
            rows.append(r)
            print(f"{r['experiment']:<10}{r['cut']:>7}{r['k']:>4}{r['trans_per_cell']:>8}"
                  f"{r['real']:>7.2f}{r['shuffled']:>7.2f}"
                  + f"{r['paired_diff']:+.3f} [{r['diff_lo']:+.3f},{r['diff_hi']:+.3f}]".rjust(23)
                  + f"{('✓' if r['survives'] else ''):>4}")

    print("\n=== 7.2 factored: does (rhythm,tempo) factorise in sequence? ===")
    for od in (False, True):
        fr = factored_experiment(df, R=4, off_diagonal=od)
        rows.append(fr)
        print(f"  {fr['cut']:>6} grid {fr['experiment']} (t/cell={fr['trans_per_cell']}): "
              f"joint real−shuf={fr['joint_paired_diff']:+.3f}[{fr['joint_lo']:+.3f},{fr['joint_hi']:+.3f}]"
              f"  factored real−shuf={fr['factored_paired_diff']:+.3f}[{fr['factored_lo']:+.3f},{fr['factored_hi']:+.3f}]")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row})
    with OUT.open("w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=keys, restval=""); w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

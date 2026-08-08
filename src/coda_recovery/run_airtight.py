"""Airtight cross-clan test — isolate the CLAN boundary from its confounds.

Cross-clan halves differ in three ways at once: different clans, no shared
repertoires, and (unmatched) different data amounts. To attribute the alignment
failure specifically to the clan boundary, hold the other two constant. Three
rungs, all at the SAME shared type set (K) and the SAME per-matrix token budget
(T), each graded against identity with its own strong (order-shuffled) null:

  within_easy : one clan, random-pair split         (shares sequences)
  within_hard : one clan, disjoint-repertoire split (same clan, no shared reps)
  cross       : two different clans                 (different clans, no shared reps)

within_hard and cross differ ONLY in the clan boundary. If within_hard clears its
null but cross does not, clan-specificity is airtight. If within_hard also fails,
the honest claim is weaker: recovery needs shared sequences, and the cross-clan
failure cannot be pinned on clans specifically.
"""
from __future__ import annotations

import csv
import itertools
from pathlib import Path

import numpy as np

from .hersh import load_hersh, shared_top_types
from .recover import qap_recover, frequency_rank_baseline, accuracy_at_1
from .transitions import row_normalise

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "airtight.csv"

FOCUS = ["REG", "SH", "FP", "PALI", "PO"]   # clans with enough data for budget T
K = 15
T = 500                                     # per-matrix token budget (pairs)
NREP = 25
NULLREP = 25
QAP_RESTARTS = 20


def _pairs_idx(sub, idx):
    """Adjacent same-repertoire contiguous coda-type pairs -> (N,2) index array."""
    s = sub.sort_values(["grpvar", "coda_number"])
    a, b = s.iloc[:-1], s.iloc[1:]
    keep = (a.grpvar.to_numpy() == b.grpvar.to_numpy()) & \
           ((b.coda_number.to_numpy() - a.coda_number.to_numpy()) <= 1)
    A = a.coda_type.to_numpy()[keep]
    B = b.coda_type.to_numpy()[keep]
    if len(A) == 0:
        return np.zeros((0, 2), int)
    return np.array([[idx[x], idx[y]] for x, y in zip(A, B)])


def _cmat(pool, k, rng):
    """Count matrix from T pairs sampled from a pool (bootstrap-up if pool<T)."""
    if len(pool) == 0:
        return np.zeros((k, k))
    replace = len(pool) < T
    sel = rng.choice(len(pool), T, replace=replace)
    C = np.zeros((k, k))
    np.add.at(C, (pool[sel, 0], pool[sel, 1]), 1)
    return C


def _acc(poolA, poolB, k, rng):
    Ca, Cb = _cmat(poolA, k, rng), _cmat(poolB, k, rng)
    rec = qap_recover(row_normalise(Ca, 1.0), row_normalise(Cb, 1.0),
                      n_restarts=QAP_RESTARTS, seed=int(rng.integers(1_000_000)))
    return accuracy_at_1(rec.perm), accuracy_at_1(frequency_rank_baseline(Ca, Cb))


def _shuffle_sub(df, clan, types, rng):
    """Order-shuffled clan subframe (shuffle coda_type within each repertoire).
    Returned as a frame so the SAME split as the observed condition can be
    applied to it — the null must mirror its condition's split, not use an
    easier one."""
    sub = df[(df.clan_name == clan) & (df.coda_type.isin(types))].copy()
    for _, g in sub.groupby("grpvar").groups.items():
        v = sub.loc[g, "coda_type"].to_numpy().copy()
        rng.shuffle(v)
        sub.loc[g, "coda_type"] = v
    return sub


def _shuffle_pool(df, clan, types, idx, rng):
    return _pairs_idx(_shuffle_sub(df, clan, types, rng), idx)


def _ci(x):
    x = np.asarray(x)
    return float(x.mean()), float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))


def within_easy(df, clan, types, idx):
    pool = _pairs_idx(df[(df.clan_name == clan) & (df.coda_type.isin(types))], idx)
    accs, bases, nulls = [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        p = rng.permutation(len(pool))
        a, b = _acc(pool[p[:T]], pool[p[T:2 * T]], len(types), rng)
        accs.append(a); bases.append(b)
    for r in range(NULLREP):
        rng = np.random.default_rng(1000 + r)
        sp = _shuffle_pool(df, clan, types, idx, rng)
        p = rng.permutation(len(sp))
        a, _ = _acc(sp[p[:T]], sp[p[T:2 * T]], len(types), rng)
        nulls.append(a)
    return accs, bases, nulls


def within_hard(df, clan, types, idx):
    reps = df[(df.clan_name == clan)].grpvar.unique()
    accs, bases, nulls = [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        rr = reps.copy(); rng.shuffle(rr)
        g1, g2 = set(rr[:len(rr) // 2]), set(rr[len(rr) // 2:])
        sub = df[(df.clan_name == clan) & (df.coda_type.isin(types))]
        pa = _pairs_idx(sub[sub.grpvar.isin(g1)], idx)
        pb = _pairs_idx(sub[sub.grpvar.isin(g2)], idx)
        a, b = _acc(pa, pb, len(types), rng)
        accs.append(a); bases.append(b)
    for r in range(NULLREP):
        rng = np.random.default_rng(2000 + r)
        rr = reps.copy(); rng.shuffle(rr)
        g1, g2 = set(rr[:len(rr) // 2]), set(rr[len(rr) // 2:])
        ssub = _shuffle_sub(df, clan, types, rng)       # mirror: same disjoint-rep
        pa = _pairs_idx(ssub[ssub.grpvar.isin(g1)], idx)  # split as the observed
        pb = _pairs_idx(ssub[ssub.grpvar.isin(g2)], idx)
        a, _ = _acc(pa, pb, len(types), rng)
        nulls.append(a)
    return accs, bases, nulls


def cross(df, ca, cb, types, idx):
    subA = df[(df.clan_name == ca) & (df.coda_type.isin(types))]
    subB = df[(df.clan_name == cb) & (df.coda_type.isin(types))]
    poolA, poolB = _pairs_idx(subA, idx), _pairs_idx(subB, idx)
    accs, bases, nulls = [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        a, b = _acc(poolA, poolB, len(types), rng)
        accs.append(a); bases.append(b)
    for r in range(NULLREP):
        rng = np.random.default_rng(3000 + r)
        sa = _shuffle_pool(df, ca, types, idx, rng)
        sb = _shuffle_pool(df, cb, types, idx, rng)
        a, _ = _acc(sa, sb, len(types), rng)
        nulls.append(a)
    return accs, bases, nulls


def main():
    df = load_hersh()
    rows = []

    # within conditions: aggregate over focus clans
    for cond, fn in (("within_easy", within_easy), ("within_hard", within_hard)):
        A, B, N = [], [], []
        for clan in FOCUS:
            types = df[df.clan_name == clan].coda_type.value_counts().head(K).index.tolist()
            idx = {t: i for i, t in enumerate(types)}
            a, b, n = fn(df, clan, types, idx)
            A += a; B += b; N += n
        rows.append(_row(cond, A, B, N))

    # cross: aggregate over focus-clan pairs
    A, B, N = [], [], []
    for ca, cb in itertools.combinations(FOCUS, 2):
        types = shared_top_types(df, ca, cb, K)
        idx = {t: i for i, t in enumerate(types)}
        a, b, n = cross(df, ca, cb, types, idx)
        A += a; B += b; N += n
    rows.append(_row("cross", A, B, N))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    print(f"Airtight ladder — K={K} shared types, T={T} pairs/matrix (matched)\n")
    print(f"{'condition':<13}{'QAP (95% CI)':>22}{'baseline':>10}{'null p95':>10}{'clears null?':>14}")
    for r in rows:
        print(f"{r['condition']:<13}"
              f"{r['qap_mean']:.3f} [{r['qap_lo']:.3f},{r['qap_hi']:.3f}]".rjust(22)
              + f"{r['baseline_mean']:>10.3f}{r['null_p95']:>10.3f}"
              + f"{'YES' if r['clears_null'] else 'no':>14}")
    print("\nAirtight logic: within_hard and cross are matched on type set, token")
    print("budget, and 'no shared repertoires' — they differ ONLY in the clan boundary.")
    wh = next(r for r in rows if r['condition'] == 'within_hard')
    cr = next(r for r in rows if r['condition'] == 'cross')
    if wh['clears_null'] and not cr['clears_null']:
        print("VERDICT: within_hard clears its null, cross does NOT -> the clan boundary")
        print("specifically breaks alignment. Clan-specificity claim is AIRTIGHT.")
    elif not wh['clears_null']:
        print("VERDICT: within_hard also fails its null -> cannot pin the failure on")
        print("clans specifically; recovery needs shared sequences. Reframe the claim.")
    else:
        print("VERDICT: both clear null -> cross-clan alignment is NOT clan-specifically broken.")
    print(f"\nwrote {OUT}")


def _row(cond, A, B, N):
    m, lo, hi = _ci(A)
    return {"condition": cond, "qap_mean": round(m, 4), "qap_lo": round(lo, 4),
            "qap_hi": round(hi, 4), "baseline_mean": round(float(np.mean(B)), 4),
            "null_mean": round(float(np.mean(N)), 4),
            "null_p95": round(float(np.percentile(N, 95)), 4),
            "clears_null": bool(lo > np.percentile(N, 95))}


if __name__ == "__main__":
    main()

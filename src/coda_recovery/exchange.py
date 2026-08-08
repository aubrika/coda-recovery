"""Within-whale vs BETWEEN-whale (exchange) transitions — the reconciliation.

Earlier, coda types re-identified within a clan on the Gero data (speaker-pooled,
so it mixed within- and between-whale transitions). In the factored analysis on
Sharma Dataset 2 we used SINGLE-WHALE sequences only, and almost nothing
re-identified. Hypothesis: the recoverable structure lives in the BETWEEN-whale
exchange (turn-taking / coda matching), which single-whale sequences exclude.

Dataset 2 has real onset times (TsTo) and speaker IDs (Whale), so we can build the
paper's exact units and compare, for every tokenization (legacy 21-type, joint
(rhythm,tempo), rhythm, tempo):

  within  — same speaker, consecutive codas <= 8 s apart (single-whale sequence).
  between — different speakers, next onset within 2 s AFTER the previous coda's
            termination (turn-taking, the paper's adjacency rule).
  pooled  — all adjacent-in-time pairs within 2 s (mixes within + between), the
            closest analogue to the old speaker-pooled Gero setup.

Paired real-vs-shuffled recovery (shuffle tokens within the grouping unit),
disjoint-deployment split, 95% bootstrap CI. Needs the Sharma deposit.

Run:  python -m coda_recovery.exchange
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import numpy as np

from .compare_codifications import _load_labelled_dataset2
from .recover_factored import _cmat
from .transitions import row_normalise
from .recover import qap_recover, accuracy_at_1

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "exchange.csv"
NREP = 25


def _pairs(df, mode, tokfn, rng=None):
    """Adjacent token pairs for a transition mode, optional within-unit shuffle."""
    pairs = []
    if mode == "within":
        groups = df.sort_values(["deployment", "speaker", "t_start"]).groupby(
            ["deployment", "speaker"], sort=False)
    else:
        groups = df.sort_values(["deployment", "t_start"]).groupby("deployment", sort=False)
    for _, g in groups:
        toks = [tokfn(r) for r in g.itertuples()]
        ts = g["t_start"].to_numpy()
        te = (g["t_start"] + g["Duration"]).to_numpy()
        spk = g["speaker"].to_numpy()
        if rng is not None:
            rng.shuffle(toks)
        for i in range(len(toks) - 1):
            if mode == "within":
                ok = (ts[i + 1] - ts[i]) <= 8            # onset-to-onset <= 8 s
            else:
                gap = ts[i + 1] - te[i]                  # onset after termination
                ok = (0 <= gap <= 2)
                if mode == "between":
                    ok = ok and (spk[i] != spk[i + 1])
            if ok:
                pairs.append((toks[i], toks[i + 1]))
    return pairs


def recovery(df, mode, tokfn, k):
    index = [t for t, _ in Counter(tokfn(r) for r in df.itertuples()).most_common(k)]
    # restrict token index to the tokens; recompute from the actual pairs' marginals
    idx_counts = Counter()
    for a, b in _pairs(df, mode, tokfn):
        idx_counts[a] += 1; idx_counts[b] += 1
    index = [t for t, _ in idx_counts.most_common(k)]
    deps = np.array(sorted(df["deployment"].unique()), dtype=object)
    obs, null, dens, npairs = [], [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        dd = deps.copy(); rng.shuffle(dd)
        A, B = set(dd[:len(dd) // 2]), set(dd[len(dd) // 2:])
        dfA, dfB = df[df.deployment.isin(A)], df[df.deployment.isin(B)]
        Ca = _cmat(_pairs(dfA, mode, tokfn), index)
        Cb = _cmat(_pairs(dfB, mode, tokfn), index)
        dens.append(0.5 * (Ca.sum() + Cb.sum()) / max(1, len(index) ** 2))
        npairs.append(int(Ca.sum() + Cb.sum()))
        obs.append(accuracy_at_1(qap_recover(row_normalise(Ca, 1.), row_normalise(Cb, 1.),
                                             n_restarts=20, seed=r).perm))
        Na = _cmat(_pairs(dfA, mode, tokfn, np.random.default_rng(100 + r)), index)
        Nb = _cmat(_pairs(dfB, mode, tokfn, np.random.default_rng(200 + r)), index)
        null.append(accuracy_at_1(qap_recover(row_normalise(Na, 1.), row_normalise(Nb, 1.),
                                              n_restarts=20, seed=r).perm))
    diff = np.array(obs) - np.array(null)
    rng = np.random.default_rng(0)
    bs = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(4000)]
    return {"mode": mode, "k": len(index), "pairs": int(np.mean(npairs)),
            "trans_per_cell": round(float(np.mean(dens)), 1),
            "real": round(float(np.mean(obs)), 3), "shuffled": round(float(np.mean(null)), 3),
            "paired_diff": round(float(diff.mean()), 3),
            "diff_lo": round(float(np.percentile(bs, 2.5)), 3),
            "diff_hi": round(float(np.percentile(bs, 97.5)), 3),
            "survives": bool(np.percentile(bs, 2.5) > 0)}


def main():
    df = _load_labelled_dataset2()
    tokens = [("legacy", lambda r: r.legacy, 15),
              ("joint", lambda r: (r.rhythm, r.tempo), 15),
              ("rhythm", lambda r: r.rhythm, 10),
              ("tempo", lambda r: r.tempo, 5)]
    rows = []
    print("Within-whale vs BETWEEN-whale vs pooled (Dataset 2), paired real−shuffled:\n")
    for tname, tf, k in tokens:
        print(f"— token = {tname} —")
        print(f"  {'mode':<9}{'pairs':>7}{'k':>4}{'t/cell':>8}{'real':>6}{'shuf':>6}"
              f"{'real−shuffled (95% CI)':>24}{'':>5}")
        for mode in ("within", "between", "pooled"):
            r = recovery(df, mode, tf, k); r = {"token": tname, **r}
            rows.append(r)
            print(f"  {mode:<9}{r['pairs']:>7}{r['k']:>4}{r['trans_per_cell']:>8}"
                  f"{r['real']:>6.2f}{r['shuffled']:>6.2f}"
                  + f"{r['paired_diff']:+.3f} [{r['diff_lo']:+.3f},{r['diff_hi']:+.3f}]".rjust(24)
                  + f"{('YES' if r['survives'] else ''):>5}")
        print()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

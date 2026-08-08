"""Syntax vs persistence (a reviewer-grade robustness cut).

Sperm whales repeat the same coda a lot (EC1: 79% of adjacent pairs are the same
type). That self-repetition sits on the DIAGONAL of the transition matrix. A
sceptic rightly asks: is the 'sequential signal' just persistence (repeating a
coda), or genuine SYNTAX (coda A tends to be followed by a *different* coda B)?

We answer by re-running the paired real-vs-shuffled test on the OFF-DIAGONAL of
the transition matrix (diagonal zeroed before row-normalising), for both the real
and shuffled data. If the signal survives — indeed strengthens — off the
diagonal, it is genuine who-follows-a-different-coda structure, not repetition.

Run:  python -m coda_recovery.syntax
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .run_reaudit import (
    ec1_dataset, pacific_datasets, _pairs, _cmat, _shuffle_within_sessions,
)
from .transitions import row_normalise
from .recover import qap_recover, accuracy_at_1

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "syntax.csv"
K = 15
NREP = 30


def paired(ds, off_diagonal: bool):
    types = ds.df[ds.typecol].value_counts().head(K).index.tolist()
    idx = {t: i for i, t in enumerate(types)}
    sub = ds.df[ds.df[ds.typecol].isin(types)].copy()
    sessions = sub[ds.session].unique()

    def mat(frame):
        C = _cmat(_pairs(frame, ds, idx), K)
        if off_diagonal:
            np.fill_diagonal(C, 0)      # remove self-repetition
        return row_normalise(C, 1.0)

    obs, null = [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        ss = sessions.copy(); rng.shuffle(ss)
        g1 = set(ss[:len(ss) // 2]); g2 = set(ss[len(ss) // 2:])
        obs.append(accuracy_at_1(qap_recover(
            mat(sub[sub[ds.session].isin(g1)]), mat(sub[sub[ds.session].isin(g2)]),
            n_restarts=20, seed=r).perm))
        sh = _shuffle_within_sessions(sub, ds, rng)
        null.append(accuracy_at_1(qap_recover(
            mat(sh[sh[ds.session].isin(g1)]), mat(sh[sh[ds.session].isin(g2)]),
            n_restarts=20, seed=r).perm))
    diff = np.array(obs) - np.array(null)
    rng = np.random.default_rng(0)
    bs = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(4000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return diff.mean(), lo, hi


def main():
    dss = [ec1_dataset()] + pacific_datasets()
    print(f"Syntax vs persistence — paired real-vs-shuffled, K={K}, {NREP} reps\n")
    print(f"{'clan':<12}{'FULL (with self-repeats)':>30}{'OFF-DIAGONAL (syntax only)':>32}")
    rows = []
    for ds in dss:
        d0, l0, h0 = paired(ds, off_diagonal=False)
        d1, l1, h1 = paired(ds, off_diagonal=True)
        rows.append({"clan": ds.name,
                     "full_diff": round(d0, 4), "full_lo": round(l0, 4), "full_hi": round(h0, 4),
                     "syntax_diff": round(d1, 4), "syntax_lo": round(l1, 4), "syntax_hi": round(h1, 4)})
        print(f"{ds.name:<12}"
              + f"{d0:+.3f} [{l0:+.3f},{h0:+.3f}]".rjust(26) + f"{('✓' if l0>0 else ''):>4}"
              + f"{d1:+.3f} [{l1:+.3f},{h1:+.3f}]".rjust(26) + f"{('✓' if l1>0 else ''):>6}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("\nOFF-DIAGONAL clears zero  -> genuine coda-A→different-coda-B syntax.")
    print("FULL clears but OFF-DIAGONAL does not -> the signal was self-repetition.")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

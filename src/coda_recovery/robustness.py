"""Robustness check for SUMMARY.md: is the EC1 sequential signal just the
dominant coda (1+1+3 / 5R1)? Re-runs the paired real-vs-shuffled test on EC1
(a) with the top-15 types, (b) with the two dominant types removed and the next
tier swapped in, and (c) with the dominant two removed and no replacement.

Result (see SUMMARY.md): the signal is NOT driven by the dominant types — removing
them and keeping 15 types makes it *stronger* — but it IS sensitive to how many
types are included (shrinking to 13 loses significance).

Run:  python -m coda_recovery.robustness
"""
from __future__ import annotations

import numpy as np

from .run_reaudit import ec1_dataset, _pairs, _cmat, _shuffle_within_sessions
from .transitions import row_normalise
from .recover import qap_recover, accuracy_at_1

NREP = 30


def paired_test(ds, types, seed_reps=NREP):
    idx = {t: i for i, t in enumerate(types)}
    sub = ds.df[ds.df[ds.typecol].isin(types)].copy()
    sessions = sub[ds.session].unique()
    obs, null = [], []
    for r in range(seed_reps):
        rng = np.random.default_rng(r)
        ss = sessions.copy(); rng.shuffle(ss)
        g1 = set(ss[:len(ss) // 2]); g2 = set(ss[len(ss) // 2:])
        s1, s2 = sub[sub[ds.session].isin(g1)], sub[sub[ds.session].isin(g2)]
        Ca, Cb = _cmat(_pairs(s1, ds, idx), len(types)), _cmat(_pairs(s2, ds, idx), len(types))
        obs.append(accuracy_at_1(qap_recover(row_normalise(Ca, 1.), row_normalise(Cb, 1.),
                                             n_restarts=20, seed=r).perm))
        sh = _shuffle_within_sessions(sub, ds, rng)
        Na = _cmat(_pairs(sh[sh[ds.session].isin(g1)], ds, idx), len(types))
        Nb = _cmat(_pairs(sh[sh[ds.session].isin(g2)], ds, idx), len(types))
        null.append(accuracy_at_1(qap_recover(row_normalise(Na, 1.), row_normalise(Nb, 1.),
                                              n_restarts=20, seed=r).perm))
    diff = np.array(obs) - np.array(null)
    rng = np.random.default_rng(0)
    bs = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(5000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return np.mean(obs), np.mean(null), diff.mean(), lo, hi, len(types)


def main():
    ds = ec1_dataset()
    freq = ds.df[ds.typecol].value_counts()
    cases = [
        ("top-15 (incl. dominant 1+1+3, 5R1)", freq.head(15).index.tolist()),
        ("dominant two removed, next tier in (ranks 3-17)", freq.index[2:17].tolist()),
        ("dominant two removed, shrunk to 13 (ranks 3-15)", freq.index[2:15].tolist()),
    ]
    print("EC1 dominant-type robustness (paired real-vs-shuffled):\n")
    for label, types in cases:
        real, shuf, d, lo, hi, n = paired_test(ds, types)
        verdict = "SURVIVES" if lo > 0 else "no"
        print(f"  {label:<48} real={real:.3f} shuf={shuf:.3f} "
              f"diff={d:+.3f} [{lo:+.3f},{hi:+.3f}] (of {n}: {d*n:+.1f})  {verdict}")


if __name__ == "__main__":
    main()

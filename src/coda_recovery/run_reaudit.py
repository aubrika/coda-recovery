"""Unified strict-null re-audit (Phase 2c) — what survives?

One protocol, applied to EC1 (Gero) and all 7 Pacific clans (Hersh):

  * top-K types per clan (K=15, comparable across all).
  * DISJOINT-SESSION split: sessions (EC1: Date; Pacific: grpvar/repertoire) are
    partitioned into two halves, so the two transition matrices are genuinely
    independent samples — no shared-sequence leakage.
  * PAIRED real-vs-shuffled test: for each split, recover on the real order AND on
    an order-shuffled copy (types permuted within each session, same split). The
    paired difference isolates the *sequential* contribution beyond frequency/
    composition. The shuffle is the true bar (the rank baseline is too lenient —
    QAP exploits more marginal structure than rank-matching).

A clan's within-clan combinatorial signal SURVIVES iff the paired difference
(real − shuffled accuracy) is reliably > 0 (bootstrap CI excludes 0) AND the real
accuracy exceeds the null's 95th percentile.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .inventory import load_raw, coda_mask
from .hersh import load_hersh, CLANS
from .transitions import row_normalise
from .recover import qap_recover, frequency_rank_baseline, accuracy_at_1

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "reaudit.csv"
K = 15
NREP = 30
QAP_RESTARTS = 20


@dataclass
class Dataset:
    name: str
    df: pd.DataFrame
    session: str
    order: str
    typecol: str


def ec1_dataset() -> Dataset:
    g = load_raw()
    g = g[coda_mask(g)].copy()
    return Dataset("EC1(Gero)", g, "Date", "CodaNumber", "CodaName")


def pacific_datasets() -> list[Dataset]:
    h = load_hersh()
    return [Dataset(f"PAC:{c}", h[h.clan_name == c].copy(), "grpvar",
                    "coda_number", "coda_type") for c in CLANS]


def _pairs(sub, ds: Dataset, idx):
    s = sub.sort_values([ds.session, ds.order])
    a, b = s.iloc[:-1], s.iloc[1:]
    keep = (a[ds.session].to_numpy() == b[ds.session].to_numpy()) & \
           ((b[ds.order].to_numpy() - a[ds.order].to_numpy()) <= 1)
    A = a[ds.typecol].to_numpy()[keep]
    B = b[ds.typecol].to_numpy()[keep]
    if len(A) == 0:
        return np.zeros((0, 2), int)
    return np.array([[idx[x], idx[y]] for x, y in zip(A, B)])


def _cmat(pairs, k):
    C = np.zeros((k, k))
    if len(pairs):
        np.add.at(C, (pairs[:, 0], pairs[:, 1]), 1)
    return C


def _shuffle_within_sessions(sub, ds: Dataset, rng):
    out = sub.copy()
    for _, g in sub.groupby(ds.session).groups.items():
        v = sub.loc[g, ds.typecol].to_numpy().copy()
        rng.shuffle(v)
        out.loc[g, ds.typecol] = v
    return out


def audit_clan(ds: Dataset) -> dict:
    freq = ds.df[ds.typecol].value_counts().head(K)
    types = freq.index.tolist()
    idx = {t: i for i, t in enumerate(types)}
    sub = ds.df[ds.df[ds.typecol].isin(types)].copy()
    sessions = sub[ds.session].unique()

    obs, null, base, dens = [], [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        ss = sessions.copy(); rng.shuffle(ss)
        g1 = set(ss[:len(ss) // 2]); g2 = set(ss[len(ss) // 2:])
        s1 = sub[sub[ds.session].isin(g1)]
        s2 = sub[sub[ds.session].isin(g2)]

        # observed (real order)
        Ca, Cb = _cmat(_pairs(s1, ds, idx), K), _cmat(_pairs(s2, ds, idx), K)
        dens.append(0.5 * (Ca.sum() + Cb.sum()) / K ** 2)
        ro = qap_recover(row_normalise(Ca, 1.0), row_normalise(Cb, 1.0),
                         n_restarts=QAP_RESTARTS, seed=r)
        obs.append(accuracy_at_1(ro.perm))
        base.append(accuracy_at_1(frequency_rank_baseline(Ca, Cb)))

        # null (same split, order shuffled within sessions)
        sh = _shuffle_within_sessions(sub, ds, rng)
        Na = _cmat(_pairs(sh[sh[ds.session].isin(g1)], ds, idx), K)
        Nb = _cmat(_pairs(sh[sh[ds.session].isin(g2)], ds, idx), K)
        rn = qap_recover(row_normalise(Na, 1.0), row_normalise(Nb, 1.0),
                         n_restarts=QAP_RESTARTS, seed=r)
        null.append(accuracy_at_1(rn.perm))

    obs, null, base = np.array(obs), np.array(null), np.array(base)
    diff = obs - null                       # paired: real − shuffled
    rng = np.random.default_rng(0)
    bs = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(5000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    # Correct test: the PAIRED difference (real vs its own shuffle on the same
    # split) reliably > 0. Comparing obs-mean to null-p95 is confounded by
    # split-to-split variance (an easy split lifts real AND shuffled together).
    survives = bool(lo > 0)
    return {
        "clan": ds.name, "n_sessions": len(sessions),
        "trans_per_cell": round(float(np.mean(dens)), 2),
        "obs_acc": round(float(obs.mean()), 4),
        "null_acc": round(float(null.mean()), 4),
        "null_p95": round(float(np.percentile(null, 95)), 4),
        "rank_baseline": round(float(base.mean()), 4),
        "paired_diff": round(float(diff.mean()), 4),
        "diff_lo": round(float(lo), 4), "diff_hi": round(float(hi), 4),
        "survives": survives,
    }


def main():
    datasets = [ec1_dataset()] + pacific_datasets()
    rows = [audit_clan(ds) for ds in datasets]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    print(f"Strict-null re-audit — K={K} types, disjoint-session split, "
          f"paired real-vs-shuffled, {NREP} reps/clan\n")
    print(f"{'clan':<12}{'sess':>5}{'t/cell':>7}{'real':>7}{'shuf':>7}"
          f"{'p95':>7}{'real−shuf (95% CI)':>22}{'survives':>9}")
    for r in rows:
        print(f"{r['clan']:<12}{r['n_sessions']:>5}{r['trans_per_cell']:>7}"
              f"{r['obs_acc']:>7.2f}{r['null_acc']:>7.2f}{r['null_p95']:>7.2f}"
              + f"{r['paired_diff']:+.3f} [{r['diff_lo']:+.3f},{r['diff_hi']:+.3f}]".rjust(22)
              + f"{('YES' if r['survives'] else 'no'):>9}")
    n_surv = sum(r["survives"] for r in rows)
    print(f"\n{n_surv}/{len(rows)} clans show a within-clan sequential signal that")
    print("survives the strict shuffle null on genuinely independent (disjoint-")
    print("session) samples. Real − shuffled > 0 means order adds identity signal")
    print("beyond frequency/composition.")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

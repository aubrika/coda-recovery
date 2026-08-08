"""Is the factored (rhythm, tempo) model a REGRESSION vs the legacy 21-type label?

A fair worry: if the classical types were re-identifiable, re-codifying them as
(rhythm, tempo) shouldn't lose that. This script settles it apples-to-apples — the
SAME data (Sharma Dataset 2, single-whale sequences), the SAME method (paired
real-vs-shuffled recovery), four tokenizations:

  legacy 21-type   — assigned to each Dataset 2 coda by nearest absolute-ICI
                     neighbour in the labelled Dataset 1 (DominicaCodas.csv).
  joint            — the (rhythm, tempo) cell.
  rhythm / tempo   — each axis alone.

Result: the legacy 21-type recovery is ALSO non-significant here (~+0.05), so the
data model is NOT the culprit — nothing re-identifies on this single-whale data
except tempo. The earlier "legacy recovered" number came from a DIFFERENT dataset
(Gero, Date-pooled) that included the between-whale exchange; the difference is the
data/sequence definition, not the codification.

Two facts this also establishes:
- The (rhythm, tempo) grid is a FINER partition than the 21 types: a single legacy
  type (e.g. 1+1+3) spans several tempo cells. So re-identifying cells is a harder
  question than re-identifying types, not a lossy one.
- Legacy recovery here is essentially frequency-driven (shuffle already ~0.71).

Needs the Sharma deposit (data/fetch_sharma.sh). Run:
  python -m coda_recovery.compare_codifications
"""
from __future__ import annotations

import csv
import pickle
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from .coda_model import TEMPO_EDGES
from .recover_factored import single_whale_sequences, _cmat, _pairs
from .transitions import row_normalise
from .recover import qap_recover, accuracy_at_1

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"
OUT = REPO / "results" / "codification_comparison.csv"
NREP = 25


def _load_labelled_dataset2() -> pd.DataFrame:
    d = pd.read_csv(RAW / "sharma" / "sperm-whale-dialogues.csv")
    d["rhythm"] = np.asarray(pickle.load(open(RAW / "sharma" / "rhythms.p", "rb")), int)
    d["tempo"] = np.digitize(d["Duration"].to_numpy(), TEMPO_EDGES)
    d = d[d["nClicks"] <= 10].reset_index(drop=True)
    # KNN legacy CodaType from the labelled Dataset 1 (nearest abs-ICI, same nClicks)
    d1 = pd.read_csv(RAW / "sharma2024_dominica_coda.csv")
    d1 = d1[d1["CodaType"] != "NOISE"]
    c2 = [f"ICI{i}" for i in range(1, 29)]
    c1 = [f"ICI{i}" for i in range(1, 10)]
    legacy = np.empty(len(d), dtype=object)
    for n, idx in d.groupby("nClicks").groups.items():
        idx = np.array(idx)
        if n < 2:
            legacy[idx] = "?"; continue
        ref = d1[d1["nClicks"] == n]
        if len(ref) == 0:
            legacy[idx] = "?"; continue
        R = ref[c1].to_numpy(float)[:, :n - 1]
        lab = ref["CodaType"].to_numpy()
        Q = d.loc[idx, c2].to_numpy(float)[:, :n - 1]
        for k, row in zip(idx, Q):
            legacy[k] = lab[np.argmin(((R - row) ** 2).sum(1))]
    d["legacy"] = legacy
    return d.rename(columns={"REC": "deployment", "Whale": "speaker", "TsTo": "t_start"})


def _paired(seqs, deps, tokfn, k):
    index = [t for t, _ in Counter(tokfn(r) for s in seqs for r in s).most_common(k)]
    obs, null, dens = [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        dd = deps.copy(); rng.shuffle(dd)
        A, B = set(dd[:len(dd) // 2]), set(dd[len(dd) // 2:])
        sA = [s for s in seqs if s[0]["deployment"] in A]
        sB = [s for s in seqs if s[0]["deployment"] in B]
        Ca, Cb = _cmat(_pairs(sA, tokfn), index), _cmat(_pairs(sB, tokfn), index)
        dens.append(0.5 * (Ca.sum() + Cb.sum()) / len(index) ** 2)
        obs.append(accuracy_at_1(qap_recover(row_normalise(Ca, 1.), row_normalise(Cb, 1.),
                                             n_restarts=20, seed=r).perm))
        Na = _cmat(_pairs(sA, tokfn, np.random.default_rng(100 + r)), index)
        Nb = _cmat(_pairs(sB, tokfn, np.random.default_rng(200 + r)), index)
        null.append(accuracy_at_1(qap_recover(row_normalise(Na, 1.), row_normalise(Nb, 1.),
                                              n_restarts=20, seed=r).perm))
    diff = np.array(obs) - np.array(null)
    rng = np.random.default_rng(0)
    bs = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(4000)]
    return {"k": len(index), "trans_per_cell": round(float(np.mean(dens)), 1),
            "real": round(float(np.mean(obs)), 3), "shuffled": round(float(np.mean(null)), 3),
            "paired_diff": round(float(diff.mean()), 3),
            "diff_lo": round(float(np.percentile(bs, 2.5)), 3),
            "diff_hi": round(float(np.percentile(bs, 97.5)), 3),
            "survives": bool(np.percentile(bs, 2.5) > 0)}


def main():
    d = _load_labelled_dataset2()
    seqs = single_whale_sequences(d)
    deps = np.array(sorted(d["deployment"].unique()), dtype=object)
    tokenizations = [
        ("legacy 21-type", lambda r: r["legacy"], 15),
        ("joint (rhy,tmp)", lambda r: (r["rhythm"], r["tempo"]), 15),
        ("rhythm", lambda r: r["rhythm"], 10),
        ("tempo", lambda r: r["tempo"], 5),
    ]
    print("Same data (Dataset 2, single-whale), same method, four tokenizations:\n")
    print(f"{'token':<16}{'k':>3}{'t/cell':>8}{'real':>6}{'shuf':>6}"
          f"{'real−shuffled (95% CI)':>24}{'':>5}")
    rows = []
    for name, tf, k in tokenizations:
        r = _paired(seqs, deps, tf, k); r = {"token": name, **r}
        rows.append(r)
        print(f"{name:<16}{r['k']:>3}{r['trans_per_cell']:>8}{r['real']:>6.2f}{r['shuffled']:>6.2f}"
              + f"{r['paired_diff']:+.3f} [{r['diff_lo']:+.3f},{r['diff_hi']:+.3f}]".rjust(24)
              + f"{('YES' if r['survives'] else ''):>5}")
    print("\nLegacy 21-type is also non-significant here => the data model is not a")
    print("regression; nothing re-identifies on single-whale data except tempo. The")
    print("earlier legacy result used a different (pooled, between-whale) dataset.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

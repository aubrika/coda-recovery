"""Factored re-identification (rhythm / tempo / joint) WITHIN each Pacific clan.

The factored model runs on Sharma's Dataset 2, which is EC1-only. This tests the
spirit of it in the 7 Pacific clans (Hersh 2022), each on its own, for all three
tokenings — answering "does the tempo/rhythm/joint sequential signal replicate
within other clans?".

The Pacific data has no rhythm/tempo labels, so we DERIVE them (the "translate
scalar coda data into (rhythm, tempo)" step):
  rhythm = nearest of the paper's 18 EC1 rhythm templates (mean_codas.p), matched
           on standardized cumulative ICI among templates of the same click count.
  tempo  = 5 per-clan duration QUANTILE classes (balanced, so frequency alone
           gives no recovery — any signal is structural).

CAVEATS (looser than the EC1 test, reported not hidden):
- No speaker IDs in Pacific data -> sequences are per-REPERTOIRE (grpvar, pooled
  speakers), not single-whale.
- Rhythm labels are the nearest EC1 template; a Pacific clan's own rhythms may not
  sit exactly in EC1's space. Consistent WITHIN a clan (what recovery needs).
- Clans where a signal survives tend to be the smaller/more-homogeneous ones, so
  part of the effect reflects how self-similar a clan's two halves are.

Run:  python -m coda_recovery.factored_by_clan
"""
from __future__ import annotations

import csv
import pickle
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from .hersh import load_hersh, CLANS
from .transitions import row_normalise
from .recover import qap_recover, accuracy_at_1

REPO = Path(__file__).resolve().parents[2]
MEAN_CODAS = REPO / "data" / "raw" / "sharma" / "mean_codas.p"
OUT = REPO / "results" / "factored_by_clan.csv"
NREP = 25
ICI_COLS = [f"ICI{i}" for i in range(1, 31)]


def load_templates():
    return [np.asarray(x, float) for x in pickle.load(open(MEAN_CODAS, "rb"))]


def assign_rhythm(sub: pd.DataFrame, templates) -> np.ndarray:
    """Nearest EC1 rhythm template by standardized cumulative ICI, per click count."""
    icis = sub[ICI_COLS].to_numpy(float)
    nclicks = sub["nclicks"].to_numpy(int)
    out = np.full(len(sub), -1, dtype=int)
    by_len = {}
    for j, t in enumerate(templates):
        by_len.setdefault(len(t), []).append((j, t))
    for n in np.unique(nclicks):
        if n not in by_len or n < 2:
            continue
        idx = np.where(nclicks == n)[0]
        cum = np.concatenate([np.zeros((len(idx), 1)), np.cumsum(icis[idx, :n - 1], axis=1)], axis=1)
        tot = cum[:, -1:]
        v = np.divide(cum, tot, out=np.zeros_like(cum), where=tot > 0)
        js = [j for j, _ in by_len[n]]
        T = np.stack([t for _, t in by_len[n]])           # (nt, n)
        d = ((v[:, None, :] - T[None, :, :]) ** 2).mean(axis=2)  # (len(idx), nt)
        out[idx] = np.array(js)[d.argmin(axis=1)]
    return out


def prep_clan(sub: pd.DataFrame, templates) -> pd.DataFrame:
    sub = sub.copy()
    sub["rhythm"] = assign_rhythm(sub, templates)
    sub["tempo"] = pd.qcut(sub["duration"], 5, labels=False, duplicates="drop")
    return sub[(sub["rhythm"] >= 0) & sub["tempo"].notna()]


def _tok(mode):
    return {"rhythm": lambda r: int(r.rhythm), "tempo": lambda r: int(r.tempo),
            "joint": lambda r: (int(r.rhythm), int(r.tempo))}[mode]


def _pairs(frame, tokfn, shuffle_rng=None):
    out = []
    for _, g in frame.sort_values(["grpvar", "coda_number"]).groupby("grpvar"):
        toks = [tokfn(r) for r in g.itertuples()]
        cn = g["coda_number"].to_numpy()
        if shuffle_rng is not None:
            shuffle_rng.shuffle(toks)
        for i in range(len(toks) - 1):
            if cn[i + 1] - cn[i] <= 1:
                out.append((toks[i], toks[i + 1]))
    return out


def _cmat(pairs, index):
    idx = {t: i for i, t in enumerate(index)}
    C = np.zeros((len(index), len(index)))
    for a, b in pairs:
        if a in idx and b in idx:
            C[idx[a], idx[b]] += 1
    return C


def recovery(sub, mode, k):
    tokfn = _tok(mode)
    counts = Counter(tokfn(r) for r in sub.itertuples())
    index = [t for t, _ in counts.most_common(k)]
    reps = sub["grpvar"].unique()
    obs, null, dens = [], [], []
    for r in range(NREP):
        rng = np.random.default_rng(r)
        rr = reps.copy(); rng.shuffle(rr)
        g1, g2 = set(rr[:len(rr) // 2]), set(rr[len(rr) // 2:])
        A, B = sub[sub.grpvar.isin(g1)], sub[sub.grpvar.isin(g2)]
        Ca, Cb = _cmat(_pairs(A, tokfn), index), _cmat(_pairs(B, tokfn), index)
        dens.append(0.5 * (Ca.sum() + Cb.sum()) / max(1, len(index) ** 2))
        obs.append(accuracy_at_1(qap_recover(row_normalise(Ca, 1.), row_normalise(Cb, 1.),
                                             n_restarts=20, seed=r).perm))
        Na = _cmat(_pairs(A, tokfn, np.random.default_rng(100 + r)), index)
        Nb = _cmat(_pairs(B, tokfn, np.random.default_rng(200 + r)), index)
        null.append(accuracy_at_1(qap_recover(row_normalise(Na, 1.), row_normalise(Nb, 1.),
                                              n_restarts=20, seed=r).perm))
    diff = np.array(obs) - np.array(null)
    rng = np.random.default_rng(0)
    bs = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(4000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"clan": sub["clan_name"].iloc[0], "mode": mode, "k": len(index),
            "trans_per_cell": round(float(np.mean(dens)), 1),
            "real": round(float(np.mean(obs)), 3), "shuffled": round(float(np.mean(null)), 3),
            "paired_diff": round(float(diff.mean()), 3),
            "diff_lo": round(float(lo), 3), "diff_hi": round(float(hi), 3),
            "survives": bool(lo > 0)}


def main():
    templates = load_templates()
    h = load_hersh()
    modes = [("tempo", 5), ("rhythm", 10), ("joint", 15)]
    rows = []
    print("Factored re-identification WITHIN each Pacific clan (real − shuffled, 95% CI)")
    print(f"{'clan':<6}{'mode':>8}{'k':>4}{'t/cell':>8}{'real':>6}{'shuf':>6}"
          f"{'real−shuffled (95% CI)':>24}{'':>5}")
    for c in CLANS:
        sub = prep_clan(h[h.clan_name == c], templates)
        for mode, k in modes:
            r = recovery(sub, mode, k)
            rows.append(r)
            print(f"{c:<6}{mode:>8}{r['k']:>4}{r['trans_per_cell']:>8}{r['real']:>6.2f}"
                  f"{r['shuffled']:>6.2f}"
                  + f"{r['paired_diff']:+.3f} [{r['diff_lo']:+.3f},{r['diff_hi']:+.3f}]".rjust(24)
                  + f"{('YES' if r['survives'] else ''):>5}")
        print()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    surv = {m: sum(r["survives"] for r in rows if r["mode"] == m) for m, _ in modes}
    print("survives in (of 7 Pacific clans): " + ", ".join(f"{m}={n}" for m, n in surv.items()))
    print("(EC1 reference: tempo YES +0.16, rhythm no, joint no.)")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

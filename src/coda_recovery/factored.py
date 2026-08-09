"""Factored-model tokenization utilities: put any clan's codas onto the shared
(rhythm, tempo) scheme.

  rhythm = nearest of the paper's 18 EC1 rhythm templates (mean_codas.p), matched
           on standardized cumulative ICI among templates of the same click count.
  tempo  = duration bins — 5 per-clan quantile classes here (balanced, so frequency
           alone gives no signal); the EC1-native pipeline uses fixed edges instead.

Used by every clan that lacks the paper's native labels (the Hersh Pacific clans),
and by `ec1_pacified.py` to put EC1 through the identical treatment.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MEAN_CODAS = REPO / "data" / "raw" / "sharma" / "mean_codas.p"
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
    """Derive (rhythm, tempo) for one clan: nearest-template rhythm + 5 quantile tempos."""
    sub = sub.copy()
    sub["rhythm"] = assign_rhythm(sub, templates)
    sub["tempo"] = pd.qcut(sub["duration"], 5, labels=False, duplicates="drop")
    return sub[(sub["rhythm"] >= 0) & sub["tempo"].notna()]

"""The one uniform pipeline — treat every clan's data identically.

Turns ANY of the 8 clans' raw codas into standardized (rhythm, tempo) tokens and
within-recording pooled sequences, so EC1 (the Caribbean clan, whose data is richer)
is measured *exactly* like the 7 Pacific clans — no clan measured more cleanly than
another. This is the source of truth for the cross-clan comparisons (the universal
within-clan figure and the clan-similarity heatmaps).

  rhythm = nearest EC1 template (`assign_rhythm`)
  tempo  = 5 duration bins — per-clan quantiles ("qcut", for within-clan analysis,
           balanced so frequency alone gives no signal) OR the shared EC1 edges
           ("global", for cross-clan token comparability)
  pairs  = adjacent codas within one recording (grpvar), speakers POOLED
           (EC1 ordered by real onset; Pacific by coda_number, contiguous only)

EC1's richer native data (known speakers, real onset times, ornament/rubato) still
enables three EC1-only SUPPLEMENTS that the Pacific data can't support — single-whale
sequences (`predictive_info.py`), the between-whale exchange (`predictive_info_sweep`),
and the expressive features (`expressive.py`). Those are labelled as supplements, not
part of this cross-clan-comparable pipeline.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .coda_model import TEMPO_EDGES
from .factored import assign_rhythm, load_templates, ICI_COLS
from .hersh import load_hersh, CLANS

REPO = Path(__file__).resolve().parents[2]
EC1_RAW = REPO / "data" / "raw" / "sharma" / "sperm-whale-dialogues.csv"
ALL_CLANS = ["EC1"] + CLANS

_TEMPLATES = None
_HERSH = None


def _templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = load_templates()
    return _TEMPLATES


def _ec1_raw() -> pd.DataFrame:
    """Raw Sharma Dataset 2 with the columns the shared pipeline expects (speakers
    are read but POOLED — used only for ordering, never to segment sequences)."""
    df = pd.read_csv(EC1_RAW)
    df = df[df["nClicks"] <= 10].copy()
    df = df.rename(columns={"REC": "grpvar", "nClicks": "nclicks",
                            "Duration": "duration", "TsTo": "order"})
    for c in ICI_COLS:                                   # pad ICI29/30 (unused at nclicks<=10)
        if c not in df.columns:
            df[c] = 0.0
    return df


def _pacific_raw(clan: str) -> pd.DataFrame:
    global _HERSH
    if _HERSH is None:
        _HERSH = load_hersh()
    df = _HERSH[_HERSH.clan_name == clan].copy()
    df["order"] = df["coda_number"]
    return df


def clan_frame(clan: str, tempo: str = "qcut") -> pd.DataFrame:
    """Standardized (rhythm, tempo) dataframe for any of the 8 clans.

    tempo='qcut'   -> 5 per-clan duration quantiles (within-clan analysis)
    tempo='global' -> shared EC1 duration edges (cross-clan comparability)
    """
    df = _ec1_raw() if clan == "EC1" else _pacific_raw(clan)
    df["rhythm"] = assign_rhythm(df, _templates())
    if tempo == "qcut":
        df["tempo"] = pd.qcut(df["duration"], 5, labels=False, duplicates="drop")
    elif tempo == "global":
        df["tempo"] = np.digitize(df["duration"].to_numpy(), TEMPO_EDGES)
    else:
        raise ValueError(tempo)
    return df[(df["rhythm"] >= 0) & df["tempo"].notna()]


def pooled_pairs(df: pd.DataFrame, tokfn):
    """Adjacent within-recording pairs, speakers pooled. Pacific keeps only
    contiguous coda_number pairs; EC1 (ordered by onset) takes all adjacent."""
    has_cn = "coda_number" in df.columns
    out = []
    for grp, g in df.sort_values(["grpvar", "order"]).groupby("grpvar"):
        rows = list(g.itertuples())
        for a, b in zip(rows, rows[1:]):
            if has_cn and (b.coda_number - a.coda_number) > 1:
                continue
            out.append((grp, tokfn(a), tokfn(b)))
    return out


def token_fn(mode: str):
    return {"tempo": lambda r: int(r.tempo), "rhythm": lambda r: int(r.rhythm),
            "joint": lambda r: (int(r.rhythm), int(r.tempo))}[mode]

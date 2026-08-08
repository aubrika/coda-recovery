"""Pacific multi-clan coda data (Hersh et al. 2022) — the genuine second system.

Unlike the same-clan split, here two *different* clans are aligned. Because
`coda_type` is a global acoustic scheme shared across clans, the ground-truth
correspondence is the identity over the *shared* type index — so cross-clan
recovery is gradeable, yet non-trivial (the clans differ in dialect and usage).

Session = `grpvar` (a repertoire/recording). Order within a session = sort by
`coda_number`; a transition is an adjacent same-session pair with contiguous
coda_number (the CodaNumber-gap substitution, as on the primary set — no
sub-second timestamps here either).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .transitions import row_normalise

REPO = Path(__file__).resolve().parents[2]
HERSH_CSV = REPO / "data" / "raw" / "hersh2022_pacific_coda.csv"
CLANS = ["REG", "SH", "FP", "PALI", "PO", "RI", "SI"]


def load_hersh(path: Path = HERSH_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["coda_type"] = pd.to_numeric(df["coda_type"], errors="coerce")
    df = df.dropna(subset=["coda_type"]).copy()
    df["coda_type"] = df["coda_type"].astype(int)
    df["coda_number"] = pd.to_numeric(df["coda_number"], errors="coerce")
    return df.dropna(subset=["coda_number"])


def shared_top_types(df: pd.DataFrame, clan_a: str, clan_b: str, k: int) -> list[int]:
    """Top-k types by combined frequency among those used by BOTH clans (density
    control — the full 54–85-type vocabulary is too sparse to align)."""
    a = df[df.clan_name == clan_a]
    b = df[df.clan_name == clan_b]
    shared = set(a.coda_type.unique()) & set(b.coda_type.unique())
    freq = (a[a.coda_type.isin(shared)].coda_type.value_counts()
            + b[b.coda_type.isin(shared)].coda_type.value_counts())
    return freq.sort_values(ascending=False).head(k).index.tolist()


def clan_pairs(df: pd.DataFrame, clan: str, types: list[int],
               max_gap: int = 1) -> pd.DataFrame:
    """Adjacent same-repertoire coda-type pairs for one clan, restricted to
    `types`, ordered by coda_number within grpvar."""
    sub = df[(df.clan_name == clan) & (df.coda_type.isin(types))].copy()
    sub = sub.sort_values(["grpvar", "coda_number"])
    a = sub.iloc[:-1]
    b = sub.iloc[1:]
    same_rep = a["grpvar"].to_numpy() == b["grpvar"].to_numpy()
    contig = (b["coda_number"].to_numpy() - a["coda_number"].to_numpy()) <= max_gap
    keep = same_rep & contig
    return pd.DataFrame({"a": a["coda_type"].to_numpy()[keep],
                         "b": b["coda_type"].to_numpy()[keep]})


def clan_transition(df: pd.DataFrame, clan: str, types: list[int],
                    alpha: float = 1.0, max_gap: int = 1):
    idx = {t: i for i, t in enumerate(types)}
    n = len(types)
    C = np.zeros((n, n), dtype=np.int64)
    pr = clan_pairs(df, clan, types, max_gap)
    for a, b in zip(pr["a"], pr["b"]):
        C[idx[a], idx[b]] += 1
    return C, row_normalise(C, alpha)


def shuffle_types_within_repertoire(df: pd.DataFrame, clan: str,
                                    types: list[int], seed: int) -> pd.DataFrame:
    """Strong-null generator: shuffle coda_type within each repertoire of a clan
    (preserve composition & length, destroy order). Returns the clan subset."""
    rng = np.random.default_rng(seed)
    sub = df[(df.clan_name == clan) & (df.coda_type.isin(types))].copy()
    out = sub.copy()
    for _, idx in sub.groupby("grpvar").groups.items():
        v = sub.loc[idx, "coda_type"].to_numpy().copy()
        rng.shuffle(v)
        out.loc[idx, "coda_type"] = v
    return out

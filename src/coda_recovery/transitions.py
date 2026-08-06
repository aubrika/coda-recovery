"""Build transition structures from the coda record (spec Section 5.1-5.2).

A transition is a consecutive pair of codas within a *segment* (a contiguous run
inside a session; see inventory.session_key_codanumber_gaps for why segments are
defined by CodaNumber contiguity rather than a seconds gap on this deposit).

Two speaker modes, always built separately (spec 5.1 — pooling them is measuring
an artefact):
  - "within":  speaker(i) == speaker(i+1)          (both attributed)
  - "between": speaker(i) != speaker(i+1)           (both attributed)
  - "pooled":  all adjacent pairs, ignore speaker   (the only mode with real
               statistical power on this deposit; see inventory)

Count matrix C (n x n), then row-normalise with additive smoothing alpha to T.
alpha is fixed once by the caller and logged; it is NOT tuned per split.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .inventory import (
    coda_mask,
    session_key_codanumber_gaps,
    UNATTRIBUTED_SPEAKER,
)


def coda_type_index(df: pd.DataFrame) -> list[str]:
    """Stable, sorted list of real coda types -> row/col index of the matrices."""
    return sorted(df.loc[coda_mask(df), "CodaName"].unique())


@dataclass
class TransitionSet:
    types: list[str]           # length n, index order of C/T
    C: np.ndarray              # n x n integer counts
    T: np.ndarray              # n x n row-normalised (smoothed) transitions
    n_transitions: int         # total pairs that went into C
    speaker_mode: str
    alpha: float

    @property
    def transitions_per_cell(self) -> float:
        return self.n_transitions / (self.C.shape[0] ** 2)


def adjacent_pairs(
    df: pd.DataFrame,
    session_cols=("Date",),
    max_codanumber_gap: int = 1,
) -> pd.DataFrame:
    """Return a frame of (a_type, b_type, a_spk, b_spk) for every same-segment
    adjacent coda pair, ordered by CodaNumber."""
    codas = df[coda_mask(df)].copy()
    seg = session_key_codanumber_gaps(codas, session_cols, max_codanumber_gap)
    codas = codas.assign(_seg=seg).sort_values("CodaNumber").reset_index(drop=True)

    a = codas.iloc[:-1]
    b = codas.iloc[1:].reset_index(drop=True)
    a = a.reset_index(drop=True)
    same = a["_seg"].to_numpy() == b["_seg"].to_numpy()
    pairs = pd.DataFrame(
        {
            "a_type": a["CodaName"].to_numpy(),
            "b_type": b["CodaName"].to_numpy(),
            "a_spk": a["WhaleID"].to_numpy(),
            "b_spk": b["WhaleID"].to_numpy(),
        }
    )[same].reset_index(drop=True)
    return pairs


def _filter_speaker_mode(pairs: pd.DataFrame, speaker_mode: str) -> pd.DataFrame:
    if speaker_mode == "pooled":
        return pairs
    attr = (pairs["a_spk"] != UNATTRIBUTED_SPEAKER) & (
        pairs["b_spk"] != UNATTRIBUTED_SPEAKER
    )
    p = pairs[attr]
    same_spk = p["a_spk"] == p["b_spk"]
    if speaker_mode == "within":
        return p[same_spk]
    if speaker_mode == "between":
        return p[~same_spk]
    raise ValueError(f"unknown speaker_mode {speaker_mode!r}")


def build_transitions(
    df: pd.DataFrame,
    types: list[str],
    speaker_mode: str = "pooled",
    alpha: float = 1.0,
    session_cols=("Date",),
    max_codanumber_gap: int = 1,
    pairs: pd.DataFrame | None = None,
) -> TransitionSet:
    """Build C and T for one speaker mode over a fixed type index.

    `types` is passed in (not derived) so both halves of a split share an
    identical index — the whole point is that a relabelling is the *only* thing
    that should differ between them.
    """
    if pairs is None:
        pairs = adjacent_pairs(df, session_cols, max_codanumber_gap)
    pairs = _filter_speaker_mode(pairs, speaker_mode)

    idx = {t: i for i, t in enumerate(types)}
    n = len(types)
    C = np.zeros((n, n), dtype=np.int64)
    for a, b in zip(pairs["a_type"], pairs["b_type"]):
        # a/b are always real types (NOISE already dropped in adjacent_pairs).
        C[idx[a], idx[b]] += 1

    T = row_normalise(C, alpha)
    return TransitionSet(
        types=list(types),
        C=C,
        T=T,
        n_transitions=int(C.sum()),
        speaker_mode=speaker_mode,
        alpha=alpha,
    )


def row_normalise(C: np.ndarray, alpha: float) -> np.ndarray:
    """Additive-smoothed row-stochastic matrix. Every row sums to 1 (a fully
    empty row becomes uniform, which is the honest prior under smoothing)."""
    Cs = C.astype(float) + alpha
    return Cs / Cs.sum(axis=1, keepdims=True)

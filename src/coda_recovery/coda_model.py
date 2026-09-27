"""Native EC1 data model and preprocessing for the speaker-level supplement.

Rhythm and ornament labels are read from the source pickles; duration bins
follow the recorded tempo edges. Derived rows are cached in a local CSV.
Run data/fetch.py all --verify before processing the recorded source files.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "sharma"
DERIVED = REPO / "data" / "derived" / "ec1_dataset2.csv"

MAX_CLICKS = 10          # paper: drop codas > 10 clicks (<5% of data)
# Tempo bin edges over coda Duration (s). Verified to reproduce the deposit's
# tempos-dict cluster membership exactly (100% agreement). 5 tempos -> 0..4.
TEMPO_EDGES = [0.392, 0.594, 0.907, 1.0905]
N_RHYTHM, N_TEMPO = 18, 5
SEQUENCE_GAP_S = 8.0     # single-whale call sequence: consecutive codas <= 8 s apart
TURNTAKING_S = 2.0       # cross-speaker adjacency: onset within 2 s of prev termination
RUBATO_CONST_TOL = 0.02  # |Δduration| below this = "constant" (our 3-way threshold;
                         # the paper leaves discrete-vs-continuous open — logged, swept)

RUBATO_INCREASING, RUBATO_DECREASING, RUBATO_CONSTANT, RUBATO_NA = "+", "-", "0", "NA"


@dataclass(frozen=True)
class Coda:
    t_start: float
    speaker: str
    deployment: str
    rhythm: int          # 0..17   (identity — NEVER a matcher input)
    tempo: int           # 0..4    (identity — NEVER a matcher input)
    ornament: bool
    rubato_dir: str
    n_clicks: int
    duration: float

    @property
    def token(self) -> tuple[int, int]:
        """The identity token: the (rhythm, tempo) cell."""
        return (self.rhythm, self.tempo)


def assign_tempo(duration: np.ndarray) -> np.ndarray:
    return np.digitize(np.asarray(duration, float), TEMPO_EDGES)  # 0..4


def build_from_deposit() -> pd.DataFrame:
    """De-pickle the deposit into a plain, columnar DataFrame (and write the CSV).
    Derives tempo (bins) and rubato direction; carries rhythm/ornament verbatim."""
    d = pd.read_csv(RAW / "sperm-whale-dialogues.csv")
    rhythm = pickle.load(open(RAW / "rhythms.p", "rb"))
    ornament = pickle.load(open(RAW / "ornaments.p", "rb"))
    assert len(rhythm) == len(ornament) == len(d), "pickle/row misalignment"

    d = d.rename(columns={"REC": "deployment", "Whale": "speaker", "TsTo": "t_start",
                          "nClicks": "n_clicks", "Duration": "duration"})
    d["rhythm"] = np.asarray(rhythm, int)
    d["ornament"] = np.asarray(ornament, int).astype(bool)
    d["tempo"] = assign_tempo(d["duration"].to_numpy())
    d = d[d["n_clicks"] <= MAX_CLICKS].reset_index(drop=True)   # inherit exclusion
    d["rubato_dir"] = _derive_rubato(d)

    cols = ["deployment", "speaker", "t_start", "n_clicks", "duration",
            "rhythm", "tempo", "ornament", "rubato_dir"]
    out = d[cols].reset_index(drop=True)
    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(DERIVED, index=False)
    return out


def _derive_rubato(d: pd.DataFrame) -> np.ndarray:
    """Rubato direction: sign of duration change vs the preceding same-speaker coda
    of the SAME (rhythm, tempo) within the same single-whale call sequence
    (consecutive same-speaker codas <= SEQUENCE_GAP_S apart). UNDEFINED when there
    is no such predecessor. Three-way with RUBATO_CONST_TOL for 'constant'."""
    out = np.array([RUBATO_NA] * len(d), dtype=object)
    d = d.reset_index()  # keep original positional index in 'index'
    for _, grp in d.sort_values(["deployment", "speaker", "t_start"]).groupby(
            ["deployment", "speaker"], sort=False):
        prev_dur: dict[tuple[int, int], float] = {}
        prev_t = None
        for _, row in grp.iterrows():
            if prev_t is not None and (row.t_start - prev_t) > SEQUENCE_GAP_S:
                prev_dur = {}                      # new sequence: reset rubato memory
            key = (int(row.rhythm), int(row.tempo))
            if key in prev_dur:
                delta = row.duration - prev_dur[key]
                out[row["index"]] = (RUBATO_CONSTANT if abs(delta) < RUBATO_CONST_TOL
                                     else RUBATO_INCREASING if delta > 0 else RUBATO_DECREASING)
            prev_dur[key] = row.duration
            prev_t = row.t_start
    return out


def load() -> list[Coda]:
    """Load Dataset 2 as Coda records (builds the derived CSV on first use)."""
    if not DERIVED.exists():
        build_from_deposit()
    df = pd.read_csv(DERIVED)
    return [Coda(t_start=r.t_start, speaker=str(r.speaker), deployment=str(r.deployment),
                 rhythm=int(r.rhythm), tempo=int(r.tempo), ornament=bool(r.ornament),
                 rubato_dir=str(r.rubato_dir), n_clicks=int(r.n_clicks),
                 duration=float(r.duration)) for r in df.itertuples()]


def attested_cells(codas: list[Coda], min_count: int = 1) -> list[tuple[int, int]]:
    """(rhythm, tempo) cells attested at least `min_count` times, frequency-sorted.
    Rare cells below threshold are DROPPED, never merged (spec 8)."""
    from collections import Counter
    c = Counter(k.token for k in codas)
    return [tok for tok, n in c.most_common() if n >= min_count]

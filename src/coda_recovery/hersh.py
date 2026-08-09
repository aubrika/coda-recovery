"""Pacific multi-clan coda data (Hersh et al. 2022) — the genuine second system.

Provides the raw per-coda table and the clan list; tokenization onto the shared
(rhythm, tempo) scheme lives in `factored.py`. `coda_type` is a global acoustic
scheme shared across clans; session = `grpvar` (a repertoire/recording), order
within a session = `coda_number`.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

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

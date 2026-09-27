"""Compare EC1 native speaker sequences with pooled recording sequences.

Tokenization and sequence construction both change; this is a sensitivity check.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from .coda_model import load
from .predictive_info import evaluate, single_whale_sequences
from .predictive_info import held_out_gain
from .standardize import clan_frame, pooled_pairs, token_fn, ALL_CLANS

REPO = Path(__file__).resolve().parents[2]
SWEEP = REPO / "results" / "predictive_info_sweep.csv"
OUT = REPO / "results" / "ec1_pacified.csv"
TOKENS = ("tempo", "rhythm", "joint")


def native_ec1():
    """EC1 within-clan MI on the native single-whale pipeline (total & transition)."""
    seqs = single_whale_sequences(load())
    deps = np.array(sorted({d for d, _ in seqs}), dtype=object)
    return {t: evaluate(t, seqs, deps) for t in TOKENS}


def standardized_ec1():
    """EC1 within-clan MI on the uniform pipeline (identical to the sweep's EC1 row)."""
    frame = clan_frame("EC1", tempo="qcut")
    out = {}
    for t in TOKENS:
        (mt, ml, mh), (tt, tl, th), n, _ = held_out_gain(pooled_pairs(frame, token_fn(t)))
        out[t] = {"gain_total": mt, "gain_transition": tt, "pairs": n}
    return out


def main():
    nat, std = native_ec1(), standardized_ec1()
    pac = pd.read_csv(SWEEP)
    pac = pac[pac.dataset.isin([f"PAC:{c}" for c in ALL_CLANS[1:]]) & (pac["mode"] == "within")]

    print("EC1: native (richer) vs the uniform pipeline everyone else gets\n")
    print(f"{'token':<8}{'native total':>14}{'uniform total':>15}"
          f"{'native trans':>14}{'uniform trans':>15}{'Pacific total band':>22}")
    rows = []
    for t in TOKENS:
        nt, ntr = nat[t]["gain_bits"], nat[t]["gain_bits_nonself"]
        st, str_ = std[t]["gain_total"], std[t]["gain_transition"]
        band = pac[pac.token == t].gain_total
        print(f"{t:<8}{nt:>+14.2f}{st:>+15.2f}{ntr:>+14.2f}{str_:>+15.2f}"
              + f"{band.min():+.2f}..{band.max():+.2f}".rjust(22))
        rows.append({"token": t, "native_total": round(nt, 3), "uniform_total": round(st, 3),
                     "native_transition": round(ntr, 3), "uniform_transition": round(str_, 3),
                     "pacific_total_min": round(float(band.min()), 3),
                     "pacific_total_max": round(float(band.max()), 3)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

"""Why we standardized: EC1 native (richer) vs EC1 through the uniform pipeline.

EC1 used to be measured more cleanly than the Pacific clans — the paper's native
rhythm/tempo labels and true single-whale sequences (known speakers, real onset
times). That made it look like a large outlier. This script puts EC1 through the
*same* `standardize` pipeline everyone else gets (nearest-template rhythm, quantile
tempo, pooled within-recording pairs) and prints the two side by side, against the
Pacific band, so the size of the measurement effect is on the record.

Finding: EC1's rhythm advantage largely collapses into the Pacific band under the
uniform pipeline; its tempo stays comparatively high (a residual confounded by
pooled between-whale matching + balanced tempo bins). Hence the project now reports
the uniform-pipeline numbers as primary (`predictive_info_sweep.py`), with the native
single-whale view kept only as a labelled supplement (`predictive_info.py`).

Run (after predictive_info_sweep):  python -m coda_recovery.ec1_pacified
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from .coda_model import load
from .predictive_info import evaluate, single_whale_sequences
from .predictive_info_sweep import held_out_mi
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
        (mt, ml, mh), (tt, tl, th), n, _ = held_out_mi(pooled_pairs(frame, token_fn(t)))
        out[t] = {"mi_total": mt, "mi_transition": tt, "pairs": n}
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
        st, str_ = std[t]["mi_total"], std[t]["mi_transition"]
        band = pac[pac.token == t].mi_total
        print(f"{t:<8}{nt:>+14.2f}{st:>+15.2f}{ntr:>+14.2f}{str_:>+15.2f}"
              + f"{band.min():+.2f}..{band.max():+.2f}".rjust(22))
        rows.append({"token": t, "native_total": round(nt, 3), "uniform_total": round(st, 3),
                     "native_transition": round(ntr, 3), "uniform_transition": round(str_, 3),
                     "pacific_total_min": round(float(band.min()), 3),
                     "pacific_total_max": round(float(band.max()), 3)})

    print("\nUnder the uniform pipeline EC1's rhythm advantage collapses toward the Pacific")
    print("band; the tempo residual is confounded (pooled matching + balanced bins). The")
    print("uniform numbers are what the project reports as primary.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

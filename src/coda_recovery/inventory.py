"""M1 inventory: establish what is *actually* in the Gero et al. (2016) EC-1
coda deposit before any analysis code is written (spec Section 4).

The spec is explicit that these deposits are described inconsistently across
papers and that missing timestamps or speaker IDs must be reported "loudly",
because such a gap is a design change, not a detail. This module reads the raw
xlsx and emits a machine-readable inventory (JSON) plus a human report (stdout /
markdown), computing the numbers that decide whether the project is viable at
all: type/speaker/unit coverage, the ordering key, session structure, and a
projected transitions-per-cell under a split-half.

Run:  python -m coda_recovery.inventory
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

# Repo layout: src/coda_recovery/inventory.py -> repo root is two parents up.
REPO = Path(__file__).resolve().parents[2]
RAW_XLSX = REPO / "data" / "raw" / "gero2016_coda_ici.xlsx"
OUT_DIR = REPO / "data" / "inventory"

# Excel stores dates as a serial day count from this epoch (the "1900 system",
# with the well-known -2 day offset already folded into 1899-12-30).
EXCEL_EPOCH = "1899-12-30"

# Non-coda annotation to exclude from the type system.
NON_CODA_LABELS = {"NOISE"}

# WhaleID sentinel for an unattributed coda (no individual assigned).
UNATTRIBUTED_SPEAKER = 0


def load_raw(path: Path = RAW_XLSX) -> pd.DataFrame:
    """Load the single-sheet ICI deposit exactly as deposited (no filtering)."""
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def coda_mask(df: pd.DataFrame) -> pd.Series:
    """True for rows that are real codas (i.e. not NOISE / non-coda markers)."""
    return ~df["CodaName"].isin(NON_CODA_LABELS)


def attributed_mask(df: pd.DataFrame) -> pd.Series:
    """True for codas with a real speaker (WhaleID != 0)."""
    return df["WhaleID"] != UNATTRIBUTED_SPEAKER


@dataclass
class FieldReport:
    present: bool
    detail: str


def _series_dates(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df["Date"], origin=EXCEL_EPOCH, unit="D")


def session_key_codanumber_gaps(
    df: pd.DataFrame, session_cols=("Date",), max_codanumber_gap: int = 1
):
    """Assign a session/segment id to every row.

    CRITICAL DATA FACT (see report): the deposit carries no sub-second
    timestamp, only a day-level ``Date`` and a globally-monotonic ``CodaNumber``
    recording index. So the spec's seconds-based "maximum inter-coda gap" is not
    computable from this deposit. We substitute a *CodaNumber gap*: within a
    session (same ``Date``, optionally same ``Unit``), consecutive codas belong
    to the same exchange while their CodaNumber is contiguous to within
    ``max_codanumber_gap``; a larger jump (an excluded/again-missing coda, or a
    genuine break) starts a new segment. This is a design substitution forced by
    the data and must be reported as such.

    Returns a Series of integer segment ids aligned to df's index.
    """
    d = df.sort_values("CodaNumber")
    seg = np.zeros(len(d), dtype=int)
    seg_id = 0
    prev = None
    prev_key = None
    for i, (_, row) in enumerate(d.iterrows()):
        key = tuple(row[c] for c in session_cols)
        cn = row["CodaNumber"]
        if prev is None:
            pass
        elif key != prev_key or (cn - prev) > max_codanumber_gap:
            seg_id += 1
        seg[i] = seg_id
        prev, prev_key = cn, key
    return pd.Series(seg, index=d.index).reindex(df.index)


def projected_transitions_per_cell(
    df: pd.DataFrame, session_cols=("Date",), max_codanumber_gap: int = 1
) -> dict:
    """Project how thin the transition matrices will be — the single number the
    spec says predicts whether anything works (Section 5.2).

    Counts adjacent same-segment coda pairs (all, and the speaker-attributed
    subset where both endpoints have a real WhaleID), then divides a split-half
    of each across the n^2 cells of the count matrix.
    """
    codas = df[coda_mask(df)].copy()
    n_types = codas["CodaName"].nunique()
    seg = session_key_codanumber_gaps(codas, session_cols, max_codanumber_gap)
    codas = codas.assign(_seg=seg).sort_values("CodaNumber")

    # Adjacent pairs within a segment.
    nxt_seg = codas["_seg"].shift(-1)
    same_seg = codas["_seg"] == nxt_seg
    a_spk = codas["WhaleID"].to_numpy()
    b_spk = codas["WhaleID"].shift(-1).to_numpy()
    both_attr = (a_spk != UNATTRIBUTED_SPEAKER) & (b_spk != UNATTRIBUTED_SPEAKER)

    n_pairs_all = int(same_seg.sum())
    n_pairs_attr = int((same_seg.to_numpy() & both_attr).sum())
    cells = n_types * n_types
    half = 0.5

    def per_cell(n):
        return round(n * half / cells, 3)

    return {
        "n_types": int(n_types),
        "cells_n_squared": int(cells),
        "adjacent_pairs_all": n_pairs_all,
        "adjacent_pairs_both_attributed": n_pairs_attr,
        "transitions_per_cell_split_half_all": per_cell(n_pairs_all),
        "transitions_per_cell_split_half_attributed": per_cell(n_pairs_attr),
        "max_codanumber_gap": max_codanumber_gap,
        "session_cols": list(session_cols),
    }


def build_inventory(df: pd.DataFrame) -> dict:
    codas = df[coda_mask(df)]
    attr = codas[attributed_mask(codas)]
    dates = _series_dates(df)

    types = sorted(codas["CodaName"].unique())
    type_counts = codas["CodaName"].value_counts().to_dict()

    inv = {
        "source_file": str(RAW_XLSX.relative_to(REPO)),
        "n_rows_total": int(len(df)),
        "columns": list(df.columns),
        "required_fields": {
            "timestamp": asdict(
                FieldReport(
                    present=False,
                    detail=(
                        "NO sub-second timestamp. Only day-level 'Date' (Excel "
                        f"serial) spanning {dates.min().date()}..{dates.max().date()} "
                        f"over {df['Date'].nunique()} distinct days. Ordering is "
                        "instead carried by 'CodaNumber', a globally-unique, "
                        "monotonic recording index. => seconds-based inter-coda "
                        "gap (spec 5.1) is NOT computable; substitute a "
                        "CodaNumber-gap (see session_key_codanumber_gaps)."
                    ),
                )
            ),
            "coda_type_label": asdict(
                FieldReport(
                    present=True,
                    detail=(
                        f"'CodaName': {codas['CodaName'].nunique()} real coda "
                        f"types after dropping {sorted(NON_CODA_LABELS)} "
                        f"({int((~coda_mask(df)).sum())} NOISE rows). Matches the "
                        "~21-22 EC-1 types the spec expects."
                    ),
                )
            ),
            "speaker_id": asdict(
                FieldReport(
                    present=True,
                    detail=(
                        f"'WhaleID': {codas['WhaleID'].nunique()} distinct values "
                        f"INCLUDING the 0 sentinel. Only {len(attr)} of "
                        f"{len(codas)} codas ({100*len(attr)/len(codas):.1f}%) are "
                        "speaker-attributed; the rest are WhaleID==0 "
                        "(unattributed). This is the binding constraint: the "
                        "within/between-speaker split (spec 5.1) and the "
                        "by-individual ladder rung (6.4) can only use the "
                        "attributed subset."
                    ),
                )
            ),
        },
        "types": types,
        "type_counts": type_counts,
        "n_units": int(codas["Unit"].nunique()),
        "units": sorted(int(u) for u in codas["Unit"].unique()),
        "n_speakers_including_sentinel": int(codas["WhaleID"].nunique()),
        "n_speakers_real": int(attr["WhaleID"].nunique()),
        "pct_attributed": round(100 * len(attr) / len(codas), 1),
        "date_span": [str(dates.min().date()), str(dates.max().date())],
        "n_distinct_days": int(df["Date"].nunique()),
        "codanumber": {
            "min": int(df["CodaNumber"].min()),
            "max": int(df["CodaNumber"].max()),
            "globally_unique": bool(df["CodaNumber"].is_unique),
            "monotonic_over_rows": bool(df["CodaNumber"].is_monotonic_increasing),
            "n_missing_in_range": int(
                df["CodaNumber"].max() - df["CodaNumber"].min() + 1 - len(df)
            ),
        },
        "power_projection": {
            "by_date_gap1": projected_transitions_per_cell(df, ("Date",), 1),
            "by_date_unit_gap1": projected_transitions_per_cell(
                df, ("Date", "Unit"), 1
            ),
            "by_date_gap3": projected_transitions_per_cell(df, ("Date",), 3),
        },
    }
    return inv


def render_markdown(inv: dict) -> str:
    L = []
    A = L.append
    A("# EC-1 coda deposit — M1 inventory\n")
    A(f"Source: `{inv['source_file']}`  ·  rows: **{inv['n_rows_total']}**\n")
    A("## Required-field verdict (spec Section 4)\n")
    for name, r in inv["required_fields"].items():
        mark = "PRESENT" if r["present"] else "**MISSING / substituted**"
        A(f"- **{name}** — {mark}: {r['detail']}\n")
    A("\n## Coda types\n")
    A(f"{len(inv['types'])} types: {', '.join(inv['types'])}\n")
    A("\nCounts (desc):\n")
    for t, c in sorted(inv["type_counts"].items(), key=lambda kv: -kv[1]):
        A(f"- {t}: {c}")
    A(f"\n## Speakers / units\n")
    A(f"- real speakers: {inv['n_speakers_real']}  ·  attributed: "
      f"{inv['pct_attributed']}%")
    A(f"- units: {inv['n_units']} {inv['units']}")
    A(f"- days: {inv['n_distinct_days']}  span {inv['date_span'][0]}..{inv['date_span'][1]}")
    A(f"- CodaNumber: {inv['codanumber']['min']}..{inv['codanumber']['max']}, "
      f"unique={inv['codanumber']['globally_unique']}, "
      f"missing-in-range={inv['codanumber']['n_missing_in_range']}")
    A("\n## Power projection — transitions per cell (split-half)\n")
    A("The number that predicts whether anything works. n^2 cells; a split-half "
      "roughly halves the pairs available to each matrix.\n")
    for k, p in inv["power_projection"].items():
        A(f"- **{k}**: n={p['n_types']}, cells={p['cells_n_squared']}; "
          f"pairs all={p['adjacent_pairs_all']} "
          f"(→ {p['transitions_per_cell_split_half_all']}/cell), "
          f"pairs both-attributed={p['adjacent_pairs_both_attributed']} "
          f"(→ {p['transitions_per_cell_split_half_attributed']}/cell)")
    return "\n".join(L) + "\n"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_raw()
    inv = build_inventory(df)
    (OUT_DIR / "gero2016_inventory.json").write_text(json.dumps(inv, indent=2))
    md = render_markdown(inv)
    (OUT_DIR / "gero2016_inventory.md").write_text(md)
    print(md)
    print(f"\nwrote {OUT_DIR/'gero2016_inventory.json'}")
    print(f"wrote {OUT_DIR/'gero2016_inventory.md'}")


if __name__ == "__main__":
    main()

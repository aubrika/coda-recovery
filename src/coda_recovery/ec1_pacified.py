"""Send EC1 through the *Pacific* pipeline — treat the richer Caribbean data exactly
like the Hersh clans, to see how much of EC1's large predictive signal is real
structure vs an artefact of measuring it more cleanly than the others.

EC1 is normally measured three ways the Pacific clans are NOT:
  (a) the paper's native rhythm/tempo labels (Pacific: derived — nearest template,
      quantile tempo);
  (b) single-whale sequences via known speakers + real onset times (Pacific: pooled
      within-recording order, speakers mixed, no times);
  (c) it drops the 59% unattributed codas (Pacific: keeps everything, no speaker IDs).

Here we HANDICAP EC1 to the Pacific treatment on all three:
  rhythm = nearest EC1 template (assign_rhythm), tempo = 5 duration quantiles (qcut),
  pairs  = adjacent codas within a recording (REC), speakers POOLED, all codas kept.
Then we measure the same held-out MI and compare to EC1-native and the Pacific band.

If EC1's advantage largely survives the handicap -> candidate clan biology.
If it collapses into the Pacific range -> the advantage was measurement, not clan.

Run:  python -m coda_recovery.ec1_pacified
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from .factored import assign_rhythm, load_templates, ICI_COLS
from .predictive_info_sweep import held_out_mi, _tf
from .hersh import CLANS

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "sharma" / "sperm-whale-dialogues.csv"
SWEEP = REPO / "results" / "predictive_info_sweep.csv"
OUT = REPO / "results" / "ec1_pacified.csv"


def load_ec1_raw() -> pd.DataFrame:
    """Raw Sharma Dataset 2 with the columns the Pacific pipeline expects."""
    df = pd.read_csv(RAW)
    df = df[df["nClicks"] <= 10].copy()                 # same >10-click drop as the main set
    df = df.rename(columns={"REC": "grpvar", "nClicks": "nclicks",
                            "Duration": "duration", "Whale": "speaker", "TsTo": "t_start"})
    for c in ICI_COLS:                                   # pad ICI29/30 (unused for nclicks<=10)
        if c not in df.columns:
            df[c] = 0.0
    return df


def pacify(df: pd.DataFrame) -> pd.DataFrame:
    """The prep_clan transform, applied to EC1: derived rhythm + quantile tempo."""
    df = df.copy()
    df["rhythm"] = assign_rhythm(df, load_templates())
    df["tempo"] = pd.qcut(df["duration"], 5, labels=False, duplicates="drop")
    return df[(df["rhythm"] >= 0) & df["tempo"].notna()]


def pacific_style_pairs(df: pd.DataFrame, tf):
    """Adjacent codas within a recording, ordered by onset, speakers POOLED — the
    Pacific within-repertoire construction (no speaker filter, no time gate)."""
    out = []
    for rec, g in df.sort_values(["grpvar", "t_start"]).groupby("grpvar"):
        rows = list(g.itertuples())
        for a, b in zip(rows, rows[1:]):
            out.append((rec, tf(a), tf(b)))
    return out


def main():
    df = pacify(load_ec1_raw())
    print(f"EC1 through the Pacific pipeline: {len(df)} codas, "
          f"{df.grpvar.nunique()} recordings (speakers pooled)\n")

    rows = []
    print(f"{'token':<8}{'pairs':>7}{'MI total (95% CI)':>26}{'MI transition (95% CI)':>28}")
    for token in ("tempo", "rhythm", "joint"):
        pairs = pacific_style_pairs(df, _tf(token))
        (mt, ml, mh), (tt, tl, th), n, V = held_out_mi(pairs)
        rows.append({"dataset": "EC1_pacified", "mode": "pacific_pipeline", "token": token,
                     "pairs": n, "mi_total": round(mt, 3), "total_lo": round(ml, 3),
                     "total_hi": round(mh, 3), "mi_transition": round(tt, 3),
                     "trans_lo": round(tl, 3), "trans_hi": round(th, 3),
                     "total_pos": bool(ml > 0), "transition_pos": bool(tl > 0)})
        print(f"{token:<8}{n:>7}" + f"{mt:+.3f} [{ml:+.3f},{mh:+.3f}]".rjust(26)
              + f"{tt:+.3f} [{tl:+.3f},{th:+.3f}]".rjust(28))

    # --- side-by-side comparison against native EC1 and the Pacific band ----------
    sw = pd.read_csv(SWEEP)
    ec_within = sw[(sw.dataset == "EC1") & (sw["mode"] == "within")].set_index("token")
    pac = sw[sw.dataset.isin([f"PAC:{c}" for c in CLANS]) & (sw["mode"] == "within")]
    print("\n  total MI (bits/coda), by tempo/rhythm/joint:")
    print(f"    {'EC1 native (single-whale)':<30}"
          + "  ".join(f"{ec_within.loc[t, 'mi_total']:+.2f}" for t in ("tempo", "rhythm", "joint")))
    print(f"    {'EC1 PACIFIED (this test)':<30}"
          + "  ".join(f"{r['mi_total']:+.2f}" for r in rows))
    print(f"    {'Pacific clans (range)':<30}"
          + "  ".join(f"{pac[pac.token == t].mi_total.min():+.2f}..{pac[pac.token == t].mi_total.max():+.2f}"
                      for t in ("tempo", "rhythm", "joint")))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

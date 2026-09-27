"""Within-clan held-out log-likelihood gain, with recording bootstrap intervals."""
from __future__ import annotations

import csv
from pathlib import Path

from .predictive_info import held_out_gain, NBOOT, NFOLDS
from .standardize import clan_frame, pooled_pairs, token_fn, ALL_CLANS

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "predictive_info_sweep.csv"


def main():
    rows = []
    print("Held-out log-likelihood gain. All pairs | changes only (conditional baseline)")
    print("Shared tokenization; speakers pooled within recordings.\n")
    print(f"{'dataset':<10}{'token':<8}{'pairs':>6}"
          f"{'All pairs (95% interval)':>24}{'Changes (95% interval)':>26}")
    for clan in ALL_CLANS:
        label = clan if clan == "EC1" else f"PAC:{clan}"
        frame = clan_frame(clan, tempo="qcut")
        for token in ("tempo", "rhythm", "joint"):
            pairs = pooled_pairs(frame, token_fn(token))
            (mt, ml, mh), (tt, tl, th), n, V = held_out_gain(pairs)
            recordings = len({u for u, _, _ in pairs})
            rows.append({"dataset": label, "mode": "within", "token": token, "pairs": n, "recordings": recordings,
                         "bootstrap_replicates": NBOOT, "cv_folds": min(NFOLDS, recordings),
                         "gain_total": round(mt, 6), "total_lo": round(ml, 6), "total_hi": round(mh, 6),
                         "gain_transition": round(tt, 6), "trans_lo": round(tl, 6), "trans_hi": round(th, 6),
                         "total_pos": bool(ml > 0), "transition_pos": bool(tl > 0)})
            print(f"{label:<10}{token:<8}{n:>6}"
                  + f"{mt:+.3f} [{ml:+.3f},{mh:+.3f}]".rjust(24)
                  + f"{tt:+.3f} [{tl:+.3f},{th:+.3f}]".rjust(26))
        print()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

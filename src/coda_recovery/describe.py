"""Sample sizes per clan, and how often a tempo change is a step to a neighbouring duration bin."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .clan_similarity import CLAN_ORDER, get_pairs
from .standardize import clan_frame

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "data_table.csv"


def neighbour_share_by_frequency(prs):
    """Share of tempo changes that would go to a neighbouring bin if the next tempo were
    drawn from the clan's tempo frequencies, given only that it differs from the current one."""
    freq = Counter(b[1] for _, _, b in prs)
    shares = []
    for _, a, b in prs:
        if a[1] != b[1]:
            rest = {t: v for t, v in freq.items() if t != a[1]}
            shares.append(sum(v for t, v in rest.items() if abs(t - a[1]) == 1) / sum(rest.values()))
    return sum(shares) / len(shares)


def main():
    pairs = get_pairs()
    rows = []
    for c in CLAN_ORDER:
        frame = clan_frame(c, tempo="global")
        prs = pairs[c]
        changed = [(a, b) for _, a, b in prs if a != b]
        tempo_changes = [(a[1], b[1]) for _, a, b in prs if a[1] != b[1]]
        rows.append({
            "clan": c, "ocean": "Caribbean" if c == "EC1" else "Pacific",
            "codas": len(frame), "recordings": frame["grpvar"].nunique(),
            "pairs": len(prs), "pairs_where_coda_changes": len(changed),
            "share_repeats": round(1 - len(changed) / len(prs), 3),
            "coda_types_used": len({t for _, a, b in prs for t in (a, b)}),
            "tempo_changes": len(tempo_changes),
            "share_of_tempo_changes_to_neighbouring_bin":
                round(sum(abs(x - y) == 1 for x, y in tempo_changes) / len(tempo_changes), 3),
            "same_share_expected_from_frequency_alone": round(neighbour_share_by_frequency(prs), 3),
        })
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

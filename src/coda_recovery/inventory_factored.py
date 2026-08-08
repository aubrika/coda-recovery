"""Inventory for the factored (rhythm, tempo, ornament, rubato) model — the first
committed deliverable of the 4-feature data model (coda-4d-data-model.md Section 9).
Reports codas, attested (rhythm, tempo) cells + per-cell counts, ornament rate,
and rubato_dir rates including UNDEFINED. Writes JSON + markdown.

Run:  python -m coda_recovery.inventory_factored
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from .coda_model import load, attested_cells, N_RHYTHM, N_TEMPO, RUBATO_CONST_TOL, SEQUENCE_GAP_S

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data" / "inventory"


def build() -> dict:
    codas = load()
    tok = Counter(k.token for k in codas)
    cells = attested_cells(codas)
    rub = Counter(k.rubato_dir for k in codas)
    n = len(codas)
    grid = np.zeros((N_RHYTHM, N_TEMPO), dtype=int)
    for (r, t), c in tok.items():
        grid[r, t] = c
    return {
        "dataset": "EC1 Dataset 2 (Sharma sperm-whale-dialogues, DTag, ordered)",
        "n_codas": n,
        "n_deployments": len({k.deployment for k in codas}),
        "n_speakers": len({k.speaker for k in codas}),
        "state_space_max": N_RHYTHM * N_TEMPO,
        "n_attested_cells": len(cells),
        "top_cells": [{"rhythm": r, "tempo": t, "count": tok[(r, t)]}
                      for (r, t) in cells[:15]],
        "singleton_cells": sum(1 for c in tok.values() if c == 1),
        "ornament_rate": round(float(np.mean([k.ornament for k in codas])), 4),
        "rubato_rates": {k: round(v / n, 4) for k, v in rub.items()},
        "rubato_const_tol_s": RUBATO_CONST_TOL,
        "sequence_gap_s": SEQUENCE_GAP_S,
        "grid_rhythm_by_tempo": grid.tolist(),
    }


def render(inv: dict) -> str:
    L = [f"# Factored coda inventory — {inv['dataset']}\n",
         f"- codas: **{inv['n_codas']}**  ·  deployments: {inv['n_deployments']}  ·  "
         f"speakers: {inv['n_speakers']}",
         f"- (rhythm × tempo) state space: {inv['state_space_max']} possible; "
         f"**{inv['n_attested_cells']} attested** ({inv['singleton_cells']} singletons)",
         f"- ornament rate: {inv['ornament_rate']}  (paper: ~0.04)",
         f"- rubato rates (tol={inv['rubato_const_tol_s']}s): " +
         ", ".join(f"{k}={v}" for k, v in inv["rubato_rates"].items()),
         "\n## Top attested (rhythm, tempo) cells\n",
         "| rhythm | tempo | codas |", "|---|---|---|"]
    for c in inv["top_cells"]:
        L.append(f"| {c['rhythm']} | {c['tempo']} | {c['count']} |")
    L.append("\n## rhythm × tempo grid (counts)\n")
    L.append("tempo →  " + " ".join(f"{t:>5}" for t in range(N_TEMPO)))
    for r, row in enumerate(inv["grid_rhythm_by_tempo"]):
        L.append(f"rhythm {r:>2}: " + " ".join(f"{v:>5}" for v in row))
    return "\n".join(L) + "\n"


def main():
    inv = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "factored_inventory.json").write_text(json.dumps(inv, indent=2))
    md = render(inv)
    (OUT / "factored_inventory.md").write_text(md)
    print(md)
    print(f"wrote {OUT/'factored_inventory.json'} and .md")


if __name__ == "__main__":
    main()

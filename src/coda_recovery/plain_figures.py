"""Plain-language figures for a general audience (no jargon, high-school level).

This module builds figures 1 (data model) and 2 (universal within-clan); the two
cross-clan heatmaps (3 = grammar doesn't transfer, 4 = grammar geometry) are built by
`clan_similarity.py`, which owns the pair-construction. Run both to refresh the whole
`figures/plain/` set:

    python -m coda_recovery.plain_figures     # figures 1, 2
    python -m coda_recovery.clan_similarity    # figures 3, 4

Color language, used consistently and learned once:
  BLUE   = tempo (duration)  /  a real, positive effect
  ORANGE = rhythm (click pattern)
  GREY   = no effect beyond chance (a reserved neutral, never a category)
Palette validated with the dataviz skill's checks (ported to Python; see
scratchpad): the blue/orange categorical pair clears CVD ΔE 22.8 (target 8),
normal-vision ΔE 28.9 (floor 15), and each mark clears 3:1 contrast on white
(blue 4.7, orange 3.6). Grey is a desaturated null marker — intentionally below
the chroma floor — always disambiguated by position (left of zero) and a label.
Sequential magnitude (figure 1) uses a single light→dark blue ramp.
Every figure's title states the finding in a sentence; the subtitle says how to
read it.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .coda_model import load, TEMPO_EDGES
from .factored import assign_rhythm, load_templates
from .hersh import load_hersh, CLANS

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
FIG = REPO / "figures" / "plain"

BLUE, ORANGE, GREY = "#1f6fb2", "#c66f0e", "#8a8a8a"
INK, MUTED = "#222222", "#666666"

plt.rcParams.update({
    "font.size": 12, "axes.edgecolor": "#cccccc", "axes.linewidth": 1.0,
    "axes.titlesize": 15, "figure.facecolor": "white", "axes.facecolor": "white",
})

CLAN_LABEL = {"EC1": "Caribbean · EC1", "PAC:REG": "Pacific · REG",
              "PAC:SH": "Pacific · SH", "PAC:FP": "Pacific · FP",
              "PAC:PALI": "Pacific · PALI", "PAC:PO": "Pacific · PO",
              "PAC:RI": "Pacific · RI", "PAC:SI": "Pacific · SI"}


def _dress(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUTED)
    ax.set_axisbelow(True)


def _titles(ax, headline, howto, wrap=90):
    """Wrap the subtitle to the axes width so bbox_inches='tight' can't expand the
    canvas (an over-long one-line subtitle otherwise squeezes the axes)."""
    sub = textwrap.fill(howto, width=wrap)
    n = sub.count("\n") + 1
    ax.set_title(headline, loc="left", pad=16 + 13 * n, fontweight="bold", color=INK)
    ax.annotate(sub, xy=(0, 1), xytext=(0, 8), xycoords="axes fraction",
                textcoords="offset points", ha="left", va="bottom",
                fontsize=11, color=MUTED, linespacing=1.3)


# ---------------------------------------------------------------- figure 1
def fig_data_model():
    """Depict the new data: every coda is a rhythm (1 of 18) x a tempo (1 of 5).
    Pools EVERY coda in the study — Caribbean EC1 (the paper's native labels) plus
    all 7 Pacific clans (mapped onto the shared scheme, exactly as figures 4-5 do)
    — so the grid reflects both datasets, not just one. The classic ~21 named types
    live inside this finer grid, and the whales concentrate on a handful of cells."""
    R, T = 18, 5
    M = np.zeros((R, T))
    for c in load():                          # Caribbean EC1 — native rhythm/tempo
        if 0 <= c.rhythm < R and 0 <= c.tempo < T:
            M[c.rhythm, c.tempo] += 1
    templates = load_templates()              # 7 Pacific clans — shared scheme
    h = load_hersh()
    for clan in CLANS:
        sub = h[h.clan_name == clan].copy()
        rh = assign_rhythm(sub, templates)                          # nearest EC1 template
        tp = np.digitize(sub["duration"].to_numpy(), TEMPO_EDGES)   # shared duration bins
        for r_, t_ in zip(rh, tp):
            if 0 <= r_ < R and 0 <= t_ < T:
                M[r_, t_] += 1
    keep = M.sum(1) > 0                       # drop rhythms unused in this clan
    M = M[keep]
    rlabels = [f"Rhythm {i + 1}" for i in range(R) if keep[i]]
    e = TEMPO_EDGES
    tcol = [f"<{e[0]:.2f}s", f"{e[0]:.2f}–{e[1]:.2f}s", f"{e[1]:.2f}–{e[2]:.2f}s",
            f"{e[2]:.2f}–{e[3]:.2f}s", f">{e[3]:.2f}s"]

    fig, ax = plt.subplots(figsize=(7.6, 0.42 * len(rlabels) + 2.4))
    im = ax.imshow(M, aspect="auto", cmap="Blues")
    vmax = M.max()
    for i in range(M.shape[0]):
        for j in range(T):
            v = int(M[i, j])
            if v:
                ax.text(j, i, v, ha="center", va="center", fontsize=9,
                        color="white" if v > 0.5 * vmax else "#39516a")
    ax.set_xticks(range(T)); ax.set_xticklabels(tcol, fontsize=9.5)
    ax.set_yticks(range(len(rlabels))); ax.set_yticklabels(rlabels, fontsize=9.5)
    ax.set_xlabel("Tempo  (how long the whole coda lasts)  →  slower")
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    _titles(ax, "The data model: every coda is a rhythm × a tempo",
            "Each coda is one of 18 rhythms (click patterns) and one of 5 tempos (durations) — a finer "
            "grid than the ~21 classic named types. Every coda in the study (Caribbean EC1 + all 7 Pacific "
            "clans, on the shared scheme); numbers = codas of that kind, darker = more.")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "1_the_data_model.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- figure 2
def fig_universal():
    """The headline, made universal: within every clan, the current coda predicts
    the next beyond frequency AND beyond repetition (transition-only MI). Both dials,
    all 8 clans, land right of zero."""
    d = pd.read_csv(RES / "predictive_info_sweep.csv")
    d = d[d["mode"] == "within"]
    clans = list(CLAN_LABEL)
    tv = {c: d[(d.dataset == c) & (d.token == "tempo")].mi_transition.iloc[0] for c in clans}
    clans = sorted(clans, key=lambda c: tv[c])          # largest tempo at top
    y = np.arange(len(clans))

    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.axvline(0, color="#444", lw=1.2)
    off = 0.18
    for dial, col, dy in [("tempo", BLUE, off), ("rhythm", ORANGE, -off)]:
        for yi, c in zip(y, clans):
            r = d[(d.dataset == c) & (d.token == dial)].iloc[0]
            ax.plot([r.trans_lo, r.trans_hi], [yi + dy, yi + dy], color=col, lw=3,
                    solid_capstyle="round", zorder=2)
            ax.plot(r.mi_transition, yi + dy, "o", color=col, ms=8, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([CLAN_LABEL[c] for c in clans], fontsize=11)
    ax.set_xlabel("Extra information the current coda carries about the next\n(bits per coda, repeats removed)")
    ax.set_xlim(-0.05, 1.12)
    _dress(ax); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "In every clan, the current coda predicts the next — beyond frequency and repetition",
            "Cross-validated extra bits, with whales' self-repeats removed (the conservative test). "
            "Every clan and both dials land right of the zero line — this is a general feature.", wrap=100)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0], [0], marker="o", color="w", markerfacecolor=BLUE,
                              markersize=9, label="Tempo (duration)"),
                       Line2D([0], [0], marker="o", color="w", markerfacecolor=ORANGE,
                              markersize=9, label="Rhythm (click pattern)")],
              loc="lower right", frameon=True, facecolor="white", edgecolor="none", fontsize=10.5)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "2_current_predicts_next.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    fig_data_model(); print("plain/1_the_data_model.png")
    fig_universal(); print("plain/2_current_predicts_next.png")
    print("(run  python -m coda_recovery.clan_similarity  for plain/3 & plain/4)")


if __name__ == "__main__":
    main()

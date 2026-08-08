"""Plain-language figures for a general audience (no jargon, high-school level).

This module builds the four stand-alone figures of the story; the two cross-clan
heatmaps (4 = grammar doesn't transfer, 5 = grammar geometry) are built by
`clan_similarity.py`, which owns the pair-construction. Run both to refresh the
whole `figures/plain/` set:

    python -m coda_recovery.plain_figures     # figures 1, 2, 3, 6
    python -m coda_recovery.clan_similarity    # figures 4, 5

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
from .factored_by_clan import assign_rhythm, load_templates
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
    ax.set_xlim(-0.05, 0.9)
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


# ---------------------------------------------------------------- figure 3
def fig_exchange():
    """The between-whale exchange: when two whales take turns, only the reply's
    tempo is predictable from the first whale's coda (the paper's 'coda matching' /
    duration drift). Reads the EC1 'between' rows of the sweep (total MI)."""
    d = pd.read_csv(RES / "predictive_info_sweep.csv")
    d = d[(d.dataset == "EC1") & (d["mode"] == "between")]
    rows = [("Tempo (duration)", "tempo"), ("Rhythm (click pattern)", "rhythm"),
            ("Full type (rhythm + tempo)", "joint")]
    y = np.arange(len(rows))[::-1]

    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.axvline(0, color="#444", lw=1.2)
    for yi, (_, tok) in zip(y, rows):
        r = d[d.token == tok].iloc[0]
        c = BLUE if r.total_lo > 0.02 else GREY
        ax.plot([r.total_lo, r.total_hi], [yi, yi], color=c, lw=3.5, solid_capstyle="round")
        ax.plot(r.mi_total, yi, "o", color=c, ms=11)
        ax.annotate(f"{r.mi_total:+.2f}", (r.mi_total, yi), xytext=(0, 10),
                    textcoords="offset points", ha="center", fontsize=10, color=INK, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels([lab for lab, _ in rows], fontsize=11)
    ax.set_xlabel("Information the first whale's coda carries about the reply (bits per coda)")
    ax.set_xlim(-0.2, 0.75)
    _dress(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "Whales predict each other's reply — but only its duration",
            "When two whales take turns (reply within 2 s), the reply's tempo is predictable from the "
            "first whale's coda; its rhythm and full type are not. From ~480 turn-taking pairs — read cautiously.")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "3_between_whale_reply.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- figure 6
def fig_expressive():
    """Additive: do ornament/rubato add anything on top of (rhythm,tempo)? Barely.
    Two questions, split by a divider: (top) do they improve prediction of the next
    call's identity, (bottom) do they have their own sequential structure."""
    d = pd.read_csv(RES / "expressive.csv")
    add = d[d.experiment == "predict_next_RT"]
    items = []
    for pred, lab in [("ornament", "Ornament → next call's identity"),
                      ("rubato", "Rubato → next call's identity"),
                      ("ornament_+_rubato", "Both → next call's identity")]:
        r = add[add.predictor == pred].iloc[0]
        items.append((lab, float(r["gain"]), float(r["gain_lo"]), float(r["gain_hi"])))
    for exp, lab in [("predict_next_ornament", "Is the next call's ornament predictable?"),
                     ("predict_next_rubato", "Is the next call's rubato predictable?")]:
        r = d[(d.experiment == exp) & (d.predictor == "RT")].iloc[0]
        items.append((lab, float(r["mi"]), float(r["mi_lo"]), float(r["mi_hi"])))
    labels, val, lo, hi = zip(*[(a, b, c, e) for a, b, c, e in items])
    y = np.arange(len(items))[::-1]

    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.axvline(0, color="#444", lw=1.2)
    ax.axhline(2.5, color="#dddddd", lw=1, ls="--")     # divider between the two questions
    for yi, v, l, h in zip(y, val, lo, hi):
        c = BLUE if l > 0.02 else GREY
        ax.plot([l, h], [yi, yi], color=c, lw=3, solid_capstyle="round")
        ax.plot(v, yi, "o", color=c, ms=9)
        ax.annotate(f"{v:+.2f}", (v, yi), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=9.5, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=10.5)
    ax.set_xlabel("Extra predictive information (bits per coda)")
    ax.set_xlim(-0.45, 0.35); ax.set_ylim(-0.6, 4.6)
    # label the two groups the divider separates, out at the right where it's empty
    ax.text(0.34, 3.5, "add to\nidentity\nprediction?", fontsize=9, color=MUTED,
            style="italic", ha="right", va="center")
    ax.text(0.34, 0.5, "own\nstructure?", fontsize=9, color=MUTED,
            style="italic", ha="right", va="center")
    _dress(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "Do the 'expressive' features (ornament, rubato) add anything? — barely",
            "On top of rhythm + tempo. Blue = a real positive contribution; grey = negligible or "
            "negative. Only rubato's own weak self-structure (bottom) stands out.", wrap=96)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "6_expressive_adds_little.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    fig_data_model(); print("plain/1_the_data_model.png")
    fig_universal(); print("plain/2_current_predicts_next.png")
    fig_exchange(); print("plain/3_between_whale_reply.png")
    fig_expressive(); print("plain/6_expressive_adds_little.png")
    print("(run  python -m coda_recovery.clan_similarity  for plain/4 & plain/5)")


if __name__ == "__main__":
    main()

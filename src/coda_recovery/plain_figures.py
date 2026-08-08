"""Plain-language figures for a general audience (no jargon, high-school level).

Color language, used consistently and learned once:
  BLUE   = "using the back-and-forth patterns" (our method)
  ORANGE = "just guessing by how common each call is"
  GREY   = "pure luck"  (a dashed reference line, never a data series)

Blue/orange is the Okabe-Ito colorblind-safe pair; normal-vision OKLab
separation checked (blue/orange 32.9, each vs grey 16.6). Every figure's title
states the finding in a sentence; a subtitle says how to read it; counts are
"out of 21" rather than fractions, because people read counts, not proportions.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd

from .inventory import load_raw
from .transitions import coda_type_index
from .m4 import confusion_over_splits

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
FIG = REPO / "figures" / "plain"
N_TYPES = 21

BLUE, ORANGE, GREY = "#1f6fb2", "#e08214", "#8a8a8a"
INK, MUTED = "#222222", "#666666"

plt.rcParams.update({
    "font.size": 12, "axes.edgecolor": "#cccccc", "axes.linewidth": 1.0,
    "axes.titlesize": 15, "figure.facecolor": "white", "axes.facecolor": "white",
})


def _dress(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUTED)
    ax.yaxis.grid(True, color="#eeeeee", lw=1)
    ax.set_axisbelow(True)


def _titles(ax, headline, howto):
    ax.set_title(headline, loc="left", pad=26, fontweight="bold", color=INK)
    ax.annotate(howto, xy=(0, 1), xytext=(0, 8), xycoords="axes fraction",
                textcoords="offset points", ha="left", va="bottom",
                fontsize=11, color=MUTED)


def fig_main():
    """Headline: patterns beat guessing, across four increasingly strict tests."""
    d = pd.read_csv(RES / "ladder.csv").set_index("split_type")
    order = ["random", "by_date", "by_individual", "by_unit"]
    labels = ["Easiest test\n(halves mixed\ntogether)", "Split by\nrecording day",
              "Split by\nindividual whale", "Split by\nfamily group"]
    qap = np.array([d.loc[s, "qap_mean"] for s in order]) * N_TYPES
    base = np.array([d.loc[s, "base_mean"] for s in order]) * N_TYPES

    fig, ax = plt.subplots(figsize=(9, 5.6))
    x = np.arange(len(order)); w = 0.38
    b1 = ax.bar(x - w / 2, qap, w, color=BLUE, label="Using the back-and-forth patterns")
    b2 = ax.bar(x + w / 2, base, w, color=ORANGE, label="Just guessing by how common each call is")
    ax.axhline(1.0, ls="--", color=GREY, lw=1.5)
    # place the label in the gap between the last two bar groups so it never
    # crosses a bar
    ax.text(2.5, 1.0, "pure luck ≈ 1 of 21", ha="center", va="center",
            fontsize=10, color=MUTED,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.0f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center",
                        fontsize=11, color=INK, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylabel("Call types correctly identified\n(out of 21)")
    ax.set_ylim(0, 11)
    ax.annotate("harder tests  →", xy=(1, -0.20), xycoords="axes fraction",
                ha="right", fontsize=10, color=MUTED, style="italic")
    _dress(ax)
    _titles(ax, "Whale calls can be identified by their role in sequence — better than guessing",
            "Hide the 21 call types' names, then try to match them between two halves of the recordings. "
            "Taller = more calls correctly identified.")
    ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    fig.subplots_adjust(bottom=0.20)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "1_main_result.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_more_data():
    """More recordings -> better identification; guessing barely moves."""
    d = pd.read_csv(RES / "token_budget.csv")
    x = d.budget.to_numpy()
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.fill_between(x, d.qap_lo * N_TYPES, d.qap_hi * N_TYPES, color=BLUE, alpha=0.15)
    ax.plot(x, d.qap_mean * N_TYPES, "o-", color=BLUE, lw=2.5, ms=8,
            label="Using the back-and-forth patterns")
    ax.plot(x, d.base_mean * N_TYPES, "s--", color=ORANGE, lw=2.5, ms=7,
            label="Just guessing by how common each call is")
    ax.axhline(1.0, ls="--", color=GREY, lw=1.5)
    ax.annotate("pure luck ≈ 1 of 21", xy=(x.max(), 1.0), xytext=(0, 4),
                textcoords="offset points", ha="right", fontsize=10, color=MUTED)
    ax.set_xlabel("Number of back-to-back call pairs analyzed")
    ax.set_ylabel("Call types correctly identified\n(out of 21)")
    ax.set_ylim(0, 15)
    _dress(ax)
    _titles(ax, "The more calls we analyze, the better it works",
            "Each point re-runs the easiest test with a limited amount of data. "
            "The pattern method (blue) keeps climbing; guessing (orange) lags.")
    ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "2_more_data_helps.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_easy_hard(df, types):
    """Per-call reliability, replacing the 21x21 confusion heatmap."""
    M = confusion_over_splits(df, types, n_splits=60)
    acc = np.diag(M)
    o = np.argsort(acc)                       # ascending -> worst at bottom
    acc, labs = acc[o], [types[i] for i in o]
    colors = [BLUE if a >= 0.5 else (ORANGE if a >= 0.2 else GREY) for a in acc]

    fig, ax = plt.subplots(figsize=(9, 7.2))
    y = np.arange(len(types))
    ax.barh(y, acc * 100, color=colors)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.5)
    ax.set_xlabel("How often this call was correctly identified (%)")
    ax.set_xlim(0, 100)
    _dress(ax); ax.xaxis.grid(True, color="#eeeeee"); ax.yaxis.grid(False)
    _titles(ax, "Some calls have a clear role; others blur together",
            "Each bar is one of the 21 call types (researchers' codes). Blue = reliably "
            "identified, orange = sometimes, grey = rarely.")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Reliably identified (≥50%)"),
                       Patch(color=ORANGE, label="Sometimes (20–50%)"),
                       Patch(color=GREY, label="Rarely (<20%)")],
              loc="lower right", frameon=False, fontsize=10)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "3_easy_vs_hard_calls.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_crossclan():
    """Phase-2 headline: identifiable within a clan, not across clans."""
    within = pd.read_csv(RES / "within_pacific.csv")
    cross = pd.read_csv(RES / "crossclan.csv")
    scen = ["Within one clan\n(7 clans)", "Between two\ndifferent clans\n(21 clan pairs)"]
    qap = [within.qap_acc.mean() * 100, cross.qap_acc.mean() * 100]
    base = [within.baseline_acc.mean() * 100, cross.baseline_acc.mean() * 100]

    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    x = np.arange(2); w = 0.38
    b1 = ax.bar(x - w / 2, qap, w, color=BLUE, label="Using the back-and-forth patterns")
    b2 = ax.bar(x + w / 2, base, w, color=ORANGE, label="Just guessing by how common each call is")
    ax.axhline(6, ls="--", color=GREY, lw=1.5)
    ax.text(1.5, 6, "pure luck ≈ 5–7%", ha="center", va="center", fontsize=10,
            color=MUTED, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center",
                        fontsize=12, color=INK, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(scen, fontsize=11)
    ax.set_ylabel("Calls correctly identified (%)")
    ax.set_ylim(0, 75)
    _dress(ax)
    _titles(ax, "Whales share the same calls across clans — but not how they string them together",
            "The sequence patterns identify a call within its own clan (left). "
            "Between two clans they fail completely (right) — even though both use the same calls.")
    ax.legend(loc="upper left", bbox_to_anchor=(0.42, 0.98), frameon=True,
              facecolor="white", edgecolor="none", fontsize=10.5)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "4_within_vs_across_clans.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    fig_main(); print("plain/1_main_result.png")
    fig_more_data(); print("plain/2_more_data_helps.png")
    df = load_raw(); types = coda_type_index(df)
    fig_easy_hard(df, types); print("plain/3_easy_vs_hard_calls.png")
    fig_crossclan(); print("plain/4_within_vs_across_clans.png")


if __name__ == "__main__":
    main()

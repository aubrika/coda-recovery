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
N_TYPES_R = 15   # re-audit uses the top-15 types per clan

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


CLAN_LABEL = {"EC1(Gero)": "Caribbean (EC1)", "PAC:REG": "Pacific · REG",
              "PAC:SH": "Pacific · SH", "PAC:FP": "Pacific · FP",
              "PAC:PALI": "Pacific · PALI", "PAC:PO": "Pacific · PO",
              "PAC:RI": "Pacific · RI", "PAC:SI": "Pacific · SI"}


def fig_order_forest():
    """Honest headline: how much does ORDER help, beyond frequency, per clan.
    Reads the strict re-audit (paired real-vs-shuffled). Effect shown as 'extra
    calls out of 15' (= paired_diff * 15) with 95% CI; a clan 'survives' when the
    whole CI is right of zero."""
    d = pd.read_csv(RES / "reaudit.csv").copy()
    d["eff"] = d.paired_diff * N_TYPES_R
    d["lo"] = d.diff_lo * N_TYPES_R
    d["hi"] = d.diff_hi * N_TYPES_R
    d = d.sort_values("eff")
    y = np.arange(len(d))
    colors = [BLUE if s else GREY for s in d.survives]

    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.axvline(0, color="#444", lw=1.2)
    for yi, (_, r) in zip(y, d.iterrows()):
        c = BLUE if r.survives else GREY
        ax.plot([r.lo, r.hi], [yi, yi], color=c, lw=3, solid_capstyle="round")
        ax.plot(r.eff, yi, "o", color=c, ms=10)
    ax.set_yticks(y)
    ax.set_yticklabels([CLAN_LABEL.get(c, c) for c in d.clan], fontsize=11)
    ax.set_xlabel("Extra calls identified from sequence order alone (out of 15)")
    ax.set_xlim(-1.5, 5)
    _dress(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "Does the ORDER of calls carry identity — beyond how common each call is?",
            "Each clan: extra calls identifiable from sequence order alone (dot), with its "
            "95% confidence range (bar). Blue = the range clears zero, so order genuinely helps.")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Order genuinely helps (range clears zero)"),
                       Patch(color=GREY, label="Not distinguishable from chance")],
              loc="lower left", bbox_to_anchor=(0.40, 0.03), frameon=True,
              facecolor="white", edgecolor="none", fontsize=10)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "4_does_order_help.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_real_vs_shuffled():
    """Make 'real − shuffled' concrete: real vs order-shuffled accuracy per clan.
    Where the two bars are ~equal, order adds nothing; a taller blue bar is the
    (small) sequential signal."""
    d = pd.read_csv(RES / "reaudit.csv").copy().sort_values("paired_diff", ascending=False)
    y = np.arange(len(d)); h = 0.38
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(y + h / 2, d.obs_acc * 100, h, color=BLUE, label="Real order")
    ax.barh(y - h / 2, d.null_acc * 100, h, color=GREY, label="Order scrambled (control)")
    ax.set_yticks(y); ax.set_yticklabels([CLAN_LABEL.get(c, c) for c in d.clan], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Calls correctly identified (%)")
    _dress(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "The test: real order vs the same calls with order scrambled",
            "If the blue (real) bar beats the grey (scrambled) bar, sequence order is "
            "adding identity beyond frequency. For most clans they nearly tie.")
    ax.legend(loc="lower right", frameon=False, fontsize=10.5)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "5_real_vs_scrambled.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


DARKBLUE, LTBLUE = "#16445f", "#79b0d6"


def fig_syntax_vs_repetition():
    """Companion to the forest plot: for each clan, BOTH the full effect (incl.
    self-repetition) and the syntax-only effect (self-repetition removed), so the
    reader sees where repetition hides real syntax (EC1) and where an apparent
    signal was only repetition (PO). Reads results/syntax.csv."""
    d = pd.read_csv(RES / "syntax.csv").copy()
    for c in ["full_diff", "full_lo", "full_hi", "syntax_diff", "syntax_lo", "syntax_hi"]:
        d[c] = d[c] * N_TYPES_R
    d = d.sort_values("syntax_diff")
    y = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.axvline(0, color="#444", lw=1.2)
    for yi, (_, r) in zip(y, d.iterrows()):
        # connector showing the shift from 'with repetition' to 'syntax only'
        ax.plot([r.full_diff, r.syntax_diff], [yi, yi], color="#cccccc", lw=1.5, zorder=1)
        ax.plot([r.full_lo, r.full_hi], [yi, yi], color=LTBLUE, lw=2.5, zorder=2)
        ax.plot(r.full_diff, yi, "s", color=LTBLUE, ms=9, zorder=3)
        ax.plot([r.syntax_lo, r.syntax_hi], [yi, yi], color=DARKBLUE, lw=2.5, zorder=2)
        ax.plot(r.syntax_diff, yi, "o", color=DARKBLUE, ms=10, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([CLAN_LABEL.get(c, c) for c in d.clan], fontsize=11)
    ax.set_xlabel("Extra calls identified from order (out of 15)")
    _dress(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "Repetition vs real syntax: where the sequencing signal actually is",
            "For each clan: all order incl. whales repeating a coda (light square) vs genuine "
            "syntax with self-repetition removed (dark circle). Right of zero = order helps.")
    ax.set_xlim(-2.5, 9.5)
    # callouts for the two instructive clans, placed clear of subtitle/legend
    labs = list(d.clan)
    if "EC1(Gero)" in labs:
        yi = labs.index("EC1(Gero)")
        ax.annotate("repetition was\nhiding the syntax",
                    (d[d.clan == "EC1(Gero)"].syntax_diff.iloc[0], yi),
                    xytext=(-14, -26), textcoords="offset points", ha="right", va="top",
                    fontsize=9, color=MUTED, arrowprops=dict(arrowstyle="->", color=MUTED))
    if "PAC:PO" in labs:
        yi = labs.index("PAC:PO")
        ax.annotate("looked like a signal,\nbut was only repetition",
                    (d[d.clan == "PAC:PO"].syntax_diff.iloc[0], yi),
                    xytext=(55, 14), textcoords="offset points", ha="left", va="bottom",
                    fontsize=9, color=MUTED, arrowprops=dict(arrowstyle="->", color=MUTED))
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0], [0], marker="s", color="w", markerfacecolor=LTBLUE,
                              markersize=10, label="All order (includes self-repetition)"),
                       Line2D([0], [0], marker="o", color="w", markerfacecolor=DARKBLUE,
                              markersize=10, label="Genuine syntax (self-repetition removed)")],
              loc="center left", bbox_to_anchor=(0.45, 0.42), frameon=True,
              facecolor="white", edgecolor="none", fontsize=10)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "6_repetition_vs_syntax.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_factored():
    """Which part of a coda carries sequential order — the factored-model result
    (rhythm vs tempo vs joint, full and syntax-only). Reads factored_recovery.csv."""
    d = pd.read_csv(RES / "factored_recovery.csv")
    d = d[d["real"].notna()].copy()          # marginal/joint rows (skip factored)
    d["eff"] = d["paired_diff"]; d["lo"] = d["diff_lo"]; d["hi"] = d["diff_hi"]
    name = {"tempo": "Tempo (duration)", "rhythm": "Rhythm (click pattern)", "joint": "Full type (rhythm+tempo)"}
    d["label"] = [f"{name[e]}\n— {c}" for e, c in zip(d.experiment, d.cut)]
    d = d.sort_values("eff")
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(9.5, 6))
    ax.axvline(0, color="#444", lw=1.2)
    for yi, (_, r) in zip(y, d.iterrows()):
        c = BLUE if r.survives else GREY
        ax.plot([r.lo, r.hi], [yi, yi], color=c, lw=3, solid_capstyle="round")
        ax.plot(r.eff, yi, "o", color=c, ms=10)
    ax.set_yticks(y); ax.set_yticklabels(d.label, fontsize=10)
    ax.set_xlabel("Sequential signal:  accuracy(real order) − accuracy(scrambled)")
    _dress(ax); ax.yaxis.grid(False); ax.xaxis.grid(True, color="#eeeeee")
    _titles(ax, "Which part of a coda carries sequential order?",
            "Break each coda into rhythm (click pattern) and tempo (duration). Only tempo shows a "
            "signal (blue, clears zero) — consistent with the paper's 'rubato' duration drift.")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Order genuinely helps (clears zero)"),
                       Patch(color=GREY, label="No signal beyond frequency")],
              loc="upper left", bbox_to_anchor=(0.01, 0.60), frameon=True,
              facecolor="white", edgecolor="none", fontsize=10)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "7_which_axis.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_clan_axis_grid():
    """Which dial carries re-identifiable order, per clan: an 8-clan × 3-axis grid.
    EC1 from factored_recovery.csv (full cut); Pacific from factored_by_clan.csv."""
    ec = pd.read_csv(RES / "factored_recovery.csv")
    ec = ec[(ec["cut"] == "full") & ec["real"].notna()].set_index("experiment")
    pac = pd.read_csv(RES / "factored_by_clan.csv")
    clans = ["EC1", "REG", "SH", "FP", "PALI", "PO", "RI", "SI"]
    axes = ["tempo", "rhythm", "joint"]
    diff = np.zeros((len(clans), 3)); surv = np.zeros((len(clans), 3), bool)
    for j, ax_name in enumerate(axes):
        diff[0, j] = ec.loc[ax_name, "paired_diff"]; surv[0, j] = bool(ec.loc[ax_name, "survives"])
    for i, c in enumerate(clans[1:], start=1):
        for j, ax_name in enumerate(axes):
            row = pac[(pac.clan == c) & (pac["mode"] == ax_name)].iloc[0]
            diff[i, j] = row["paired_diff"]; surv[i, j] = bool(row["survives"])

    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    for i in range(len(clans)):
        for j in range(3):
            d, s = diff[i, j], surv[i, j]
            fc = BLUE if s else "#eef2f5"
            ax.add_patch(plt.Rectangle((j, len(clans) - 1 - i), 1, 1, facecolor=fc,
                                       edgecolor="white", lw=2))
            ax.text(j + 0.5, len(clans) - 1 - i + 0.5, f"{d:+.2f}",
                    ha="center", va="center", fontsize=11,
                    color="white" if s else MUTED, fontweight="bold" if s else "normal")
    ax.set_xlim(0, 3); ax.set_ylim(0, len(clans) + 0.9)
    for j, lab in enumerate(["Tempo\n(duration)", "Rhythm\n(click pattern)", "Joint\n(both)"]):
        ax.text(j + 0.5, len(clans) + 0.25, lab, ha="center", va="bottom", fontsize=11)
    ax.set_xticks([])
    ax.set_yticks(np.arange(len(clans)) + 0.5)
    ax.set_yticklabels(clans[::-1], fontsize=11)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    _titles(ax, "Which dial carries re-identifiable order — by clan",
            "Each cell = real − shuffled recovery of that dial in that clan (extra recovery over "
            "the order-scrambled control). Blue = clears zero. Tempo is the most reproducible axis.")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "8_clan_axis_grid.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_predictive_info():
    """The clean, robust result: held-out predictive information (bits/coda) that
    the current (rhythm,tempo) token carries about the next — total and with
    repeats removed. Replaces the QAP re-identification framing entirely."""
    d = pd.read_csv(RES / "predictive_info.csv").set_index("mode")
    order = ["tempo", "rhythm", "joint"]
    labels = ["Tempo\n(duration)", "Rhythm\n(click pattern)", "Both\n(rhythm+tempo)"]
    x = np.arange(len(order)); w = 0.38
    tot = np.array([d.loc[m, "gain_bits"] for m in order])
    tot_e = np.vstack([tot - [d.loc[m, "gain_lo"] for m in order],
                       [d.loc[m, "gain_hi"] for m in order] - tot])
    tr = np.array([d.loc[m, "gain_bits_nonself"] for m in order])
    tr_e = np.vstack([tr - [d.loc[m, "nonself_lo"] for m in order],
                      [d.loc[m, "nonself_hi"] for m in order] - tr])

    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    ax.bar(x - w / 2, tot, w, yerr=tot_e, capsize=4, color=LTBLUE,
           label="All transitions (includes repeats)")
    ax.bar(x + w / 2, tr, w, yerr=tr_e, capsize=4, color=DARKBLUE,
           label="Changes only (repeats removed)")
    for xi, v, hi in zip(x - w / 2, tot, [d.loc[m, "gain_hi"] for m in order]):
        ax.annotate(f"{v:.2f}", (xi, hi), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=10, color=INK, fontweight="bold")
    for xi, v, hi in zip(x + w / 2, tr, [d.loc[m, "nonself_hi"] for m in order]):
        ax.annotate(f"{v:.2f}", (xi, hi), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=10, color=INK, fontweight="bold")
    ax.axhline(0, color="#444", lw=1)
    ax.set_xlim(-0.6, 2.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Predictive information (bits per coda)")
    ax.set_ylim(0, 2.05)
    _dress(ax)
    _titles(ax, "The current coda genuinely predicts the next — beyond frequency",
            "Cross-validated bits of information the current call carries about the next (higher = "
            "more predictable). All bars are reliably above zero — even with repetition removed.")
    ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "9_predictive_information.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    fig_main(); print("plain/1_main_result.png")
    fig_more_data(); print("plain/2_more_data_helps.png")
    df = load_raw(); types = coda_type_index(df)
    fig_easy_hard(df, types); print("plain/3_easy_vs_hard_calls.png")
    fig_order_forest(); print("plain/4_does_order_help.png")
    fig_real_vs_shuffled(); print("plain/5_real_vs_scrambled.png")
    fig_syntax_vs_repetition(); print("plain/6_repetition_vs_syntax.png")
    fig_factored(); print("plain/7_which_axis.png")
    fig_clan_axis_grid(); print("plain/8_clan_axis_grid.png")
    fig_predictive_info(); print("plain/9_predictive_information.png")


if __name__ == "__main__":
    main()

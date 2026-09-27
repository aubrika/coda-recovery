"""Leave-one-clan-out prediction against target-clan training frequencies.

Changes-only models and baselines both exclude the current token. Results are
point estimates for the sampled clans, not a test of a species-wide rule.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .predictive_info import held_out_gain, pair_counts, log_gain_matrix, recording_folds
from .standardize import clan_frame, pooled_pairs, token_fn, ALL_CLANS

REPO = Path(__file__).resolve().parents[2]
FIG = REPO / "figures" / "plain"
OUT = REPO / "results" / "universal_structure.csv"
TOKENS = ("tempo", "rhythm", "joint")

LTBLUE, BLUE, GREY, INK, MUTED = "#79b0d6", "#1f6fb2", "#8a8a8a", "#222222", "#666666"


def loco_gain(held_out, pairs_by_clan, transition_only):
    """Train a bigram on every clan EXCEPT `held_out`, then score the held-out clan's
    codas against its OWN unigram. Mean held-out bits/coda (over CV folds of the
    held-out clan's recordings)."""
    pairs = pairs_by_clan
    vocab = set()
    for pr in pairs.values():
        for _, a, b in pr:
            vocab |= {a, b}
    vocab = sorted(vocab, key=repr)
    foreign = pair_counts([p for c, pr in pairs.items() if c != held_out for p in pr], vocab)
    units = sorted({u for u, _, _ in pairs[held_out]}, key=repr)
    score, count = 0.0, 0.0
    for fold in recording_folds(units):
        te = {units[i] for i in fold}
        trp = [p for p in pairs[held_out] if p[0] not in te]
        tep = [p for p in pairs[held_out] if p[0] in te]
        baseline = pair_counts(trp, vocab)
        test = pair_counts(tep, vocab)
        if transition_only:
            np.fill_diagonal(test, 0)
        score += float(np.sum(test * log_gain_matrix(foreign, transition_only, baseline)))
        count += test.sum()
    return score / count if count else np.nan


def compute():
    frames = {c: clan_frame(c, "global") for c in ALL_CLANS}
    res = {}
    rows = []
    for tok in TOKENS:
        pairs = {c: pooled_pairs(frames[c], token_fn(tok)) for c in ALL_CLANS}
        within, across = {}, {}
        for c in ALL_CLANS:
            (_, _, _), (wt, _, _), _, _ = held_out_gain(pairs[c], n_boot=0)
            within[c] = wt
            across[c] = loco_gain(c, pairs, transition_only=True)   # leave-one-clan-out, transition-only
            rows.append({"token": tok, "clan": c,
                         "within_transition": round(within[c], 4),
                         "across_transition": round(across[c], 4),
                         "across_positive": bool(across[c] > 0)})
        res[tok] = (within, across)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    return res


def figure(res):
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.8), sharey=True)
    for ax, tok in zip(axes, ("tempo", "rhythm")):
        within, across = res[tok]
        y = np.arange(len(ALL_CLANS))
        for i, clan in enumerate(ALL_CLANS):
            ax.plot([within[clan], across[clan]], [i, i], color="#cccccc", zorder=1)
        ax.scatter([within[c] for c in ALL_CLANS], y, color=LTBLUE, label="Within clan", zorder=2)
        ax.scatter([across[c] for c in ALL_CLANS], y, color=BLUE, marker="x", label="Other seven clans", zorder=3)
        ax.axvline(0, color="#666666", linewidth=1)
        ax.set_title(tok.capitalize())
        ax.set_xlabel("Held-out gain (bits per changed pair)")
        ax.set_yticks(y, ALL_CLANS)
        ax.grid(axis="x", color="#eeeeee")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].invert_yaxis()
    axes[1].legend(loc="best", fontsize=9)
    fig.suptitle("Transfer to a held-out clan", fontsize=15, fontweight="bold")
    fig.text(0.5, 0.91, "Point estimates on shared duration bins; both baselines condition on a token change.",
             ha="center", fontsize=10, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "3_shared_vs_clan_specific.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    res = compute()
    print("Leave-one-clan-out: transition-only bits/coda (within each clan | predicting an unseen clan)\n")
    print(f"{'token':<8}{'within (mean)':>16}{'across / LOCO (mean)':>24}{'clans > 0 across':>18}")
    for tok in TOKENS:
        within, across = res[tok]
        wm = np.mean(list(within.values())); am = np.mean(list(across.values()))
        npos = sum(v > 0 for v in across.values())
        print(f"{tok:<8}{wm:>+16.3f}{am:>+24.3f}{f'{npos}/8':>18}")
    figure(res)
    print(f"\nwrote {OUT} and figures/plain/3_shared_vs_clan_specific.png")


if __name__ == "__main__":
    main()

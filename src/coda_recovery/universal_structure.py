"""Is the within-clan sequencing structure SHARED across clans, or clan-specific?

The within-clan test (`predictive_info_sweep.py`) shows that inside every clan the
current coda predicts the next. But that says nothing about whether the *rule* is the
same from clan to clan — "coda + clan predicts" is not "coda predicts regardless of
clan." This module asks the stricter question with a **leave-one-clan-out** test:

  train one bigram on 7 clans, then predict the held-out 8th clan's next coda, scored
  against THAT clan's own base rates.

Because the model never sees the held-out clan, and the baseline is the held-out
clan's own frequencies, the current coda gets *no* credit for revealing which clan you
are in (the clan-identity leakage that inflates a naive pooled analysis). A positive
score therefore means a genuinely CLAN-AGNOSTIC transition rule — structure across all
coda sequences regardless of clan membership.

Result: only **tempo** transfers (positive for all 8 held-out clans) — a universal
duration-drift. **Rhythm** and the joint type do not (a foreign model predicts a new
clan worse than its base rates) — clan-specific dialect. All on the shared tokens.

Run:  python -m coda_recovery.universal_structure
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from math import log2
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .predictive_info import ALPHA
from .predictive_info_sweep import held_out_mi
from .standardize import clan_frame, pooled_pairs, token_fn, ALL_CLANS

REPO = Path(__file__).resolve().parents[2]
FIG = REPO / "figures" / "plain"
OUT = REPO / "results" / "universal_structure.csv"
TOKENS = ("tempo", "rhythm", "joint")
NREP = 25

LTBLUE, BLUE, GREY, INK, MUTED = "#79b0d6", "#1f6fb2", "#8a8a8a", "#222222", "#666666"


def loco_gain(held_out, pairs_by_clan, transition_only):
    """Train a bigram on every clan EXCEPT `held_out`, then score the held-out clan's
    codas against its OWN unigram. Mean held-out bits/coda (over CV folds of the
    held-out clan's recordings)."""
    pairs = pairs_by_clan
    if transition_only:
        pairs = {c: [p for p in pr if p[1] != p[2]] for c, pr in pairs.items()}
    vocab = set()
    for pr in pairs.values():
        for _, a, b in pr:
            vocab |= {a, b}
    V = len(vocab)
    bi = defaultdict(Counter); rs = Counter()               # universal bigram = the other 7 clans
    for c, pr in pairs.items():
        if c == held_out:
            continue
        for _, a, b in pr:
            bi[a][b] += 1; rs[a] += 1
    units = sorted({u for u, _, _ in pairs[held_out]}, key=str)
    rng = np.random.default_rng(0)
    folds = []
    for _ in range(NREP):
        u = np.array(units, dtype=object); rng.shuffle(u)
        te = set(u[:max(1, len(u) // 3)])
        trp = [p for p in pairs[held_out] if p[0] not in te]
        tep = [p for p in pairs[held_out] if p[0] in te]
        uni = Counter(b for _, _, b in trp); Nu = sum(uni.values())
        if not tep or Nu == 0:
            continue
        g = [log2((bi[a][b] + ALPHA) / (rs.get(a, 0) + ALPHA * V))
             - log2((uni[b] + ALPHA) / (Nu + ALPHA * V)) for _, a, b in tep]
        folds.append(float(np.mean(g)))
    return float(np.mean(folds)) if folds else np.nan


def _clan_ci(vals, seed=0):
    """Mean and 95% bootstrap CI over the per-clan point estimates."""
    v = np.array([x for x in vals if np.isfinite(x)])
    rng = np.random.default_rng(seed)
    bs = [np.mean(rng.choice(v, len(v), replace=True)) for _ in range(4000)]
    return float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def compute():
    frames = {c: clan_frame(c, "global") for c in ALL_CLANS}
    res = {}
    rows = []
    for tok in TOKENS:
        pairs = {c: pooled_pairs(frames[c], token_fn(tok)) for c in ALL_CLANS}
        within, across = {}, {}
        for c in ALL_CLANS:
            (_, _, _), (wt, _, _), _, _ = held_out_mi(pairs[c])     # within-clan (self), transition-only
            within[c] = wt
            across[c] = loco_gain(c, pairs, transition_only=True)   # leave-one-clan-out, transition-only
            rows.append({"token": tok, "clan": c,
                         "within_transition": round(within[c], 4),
                         "across_transition": round(across[c], 4),
                         "across_positive": bool(across[c] > 0)})
        res[tok] = (within, across)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return res


def figure(res):
    dials = [("tempo", "Tempo\n(duration)"), ("rhythm", "Rhythm\n(click pattern)")]
    x = np.arange(len(dials)); wbar = 0.38
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    ax.axhline(0, color="#444", lw=1)
    for k, (tok, _) in enumerate(dials):
        within, across = res[tok]
        wm, wl, wh = _clan_ci(list(within.values()))
        am, al, ah = _clan_ci(list(across.values()))
        npos = sum(v > 0 for v in across.values())
        ax.bar(x[k] - wbar / 2, wm, wbar, yerr=[[wm - wl], [wh - wm]], capsize=4,
               color=LTBLUE, label="Within each clan" if k == 0 else None)
        ac = BLUE if al > 0 else GREY
        ax.bar(x[k] + wbar / 2, am, wbar, yerr=[[am - al], [ah - am]], capsize=4,
               color=ac, label="Across clans (a clan the model never saw)" if k == 0 else None)
        ax.annotate(f"{wm:+.2f}", (x[k] - wbar / 2, wh), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=10, color=INK, fontweight="bold")
        if am >= 0:
            ax.annotate(f"{am:+.2f}", (x[k] + wbar / 2, ah), xytext=(0, 4),
                        textcoords="offset points", ha="center", fontsize=10, color=INK, fontweight="bold")
        else:
            ax.text(x[k] + wbar / 2, am / 2, f"{am:+.2f}", ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")
        ax.annotate(f"{npos}/8 clans > 0", (x[k] + wbar / 2, 0), xytext=(6, 12 if am < 0 else -14),
                    textcoords="offset points", ha="left" if am < 0 else "center",
                    va="bottom", fontsize=8.5, color=MUTED)
    ax.set_xticks(x); ax.set_xticklabels([lab for _, lab in dials], fontsize=11)
    ax.set_ylabel("Predictive information, repeats removed\n(bits per coda)")
    ax.set_ylim(-0.95, 0.9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUTED); ax.yaxis.grid(True, color="#eeeeee"); ax.set_axisbelow(True)
    ax.set_title("Only duration-sequencing is shared across clans", loc="left",
                 pad=44, fontweight="bold", color=INK)
    ax.annotate("Within each clan both dials predict the next coda (light). But asked to predict a clan it "
                "has never\nseen (dark), only tempo still beats that clan's own base rates — rhythm's rule is "
                "a local dialect.",
                xy=(0, 1), xytext=(0, 8), xycoords="axes fraction", textcoords="offset points",
                ha="left", va="bottom", fontsize=10.5, color=MUTED, linespacing=1.35)
    ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    fig.tight_layout()
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

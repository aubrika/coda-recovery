"""Does Procrustes distance track how well clans predict each other?

For every pair of clans this compares two numbers that clan_similarity already
computes: the Procrustes distance between their transition embeddings, and how
well each clan's bigram predicts the other's held-out codas (averaged over both
directions). If distance is a usable proxy for drift in sequence structure, pairs
that sit further apart should predict each other worse.

Pairs of clans are not independent observations, because each clan appears in
seven of them. Significance therefore comes from a Mantel test: clan labels are
permuted on one matrix and the correlation recomputed. With eight clans all
40,320 permutations are enumerated, so the p-values are exact.

The token inventory is a likely confound: two clans that use different codas will
both sit far apart and predict each other badly, whatever their ordering. The
partial test asks what is left after the Jensen-Shannon divergence between the
clans' coda frequencies is accounted for.
"""
from __future__ import annotations

import csv
from collections import Counter
from itertools import permutations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import rankdata

from .clan_similarity import CLAN_ORDER, EMB_D, EMB_K, cross_prediction, get_pairs, procrustes_distances

REPO = Path(__file__).resolve().parents[2]
FIG = REPO / "figures" / "plain"
OUT = REPO / "results"

BLUE, ORANGE = "#1f6fb2", "#c66f0e"
INK, MUTED = "#222222", "#666666"


def mutual_loss(T):
    """Bits per coda lost when two clans predict each other, averaged over both directions.

    T[i, j] is clan i's bigram scored on clan j against j's own frequencies, so it
    is negative when the foreign model does worse. The sign is flipped so that a
    larger value means less predictability is preserved.
    """
    return -(T + T.T) / 2


def inventory_divergence(pairs, clans=CLAN_ORDER):
    """Jensen-Shannon divergence (bits) between clans' coda-token frequencies."""
    counts = {c: Counter() for c in clans}
    for c in clans:
        for _, a, b in pairs[c]:
            counts[c][a] += 1
            counts[c][b] += 1
    vocab = sorted({t for c in clans for t in counts[c]})
    P = np.array([[counts[c][t] for t in vocab] for c in clans], dtype=float)
    P /= P.sum(1, keepdims=True)

    def kl(p, q):
        m = p > 0
        return float(np.sum(p[m] * np.log2(p[m] / q[m])))

    n = len(clans)
    J = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mid = (P[i] + P[j]) / 2
            J[i, j] = (kl(P[i], mid) + kl(P[j], mid)) / 2
    return J


def _corr(x, y):
    x = x - x.mean()
    y = y - y.mean()
    return float(x @ y / np.sqrt((x @ x) * (y @ y)))


def _residual(v, z):
    """v with its least-squares fit on z removed."""
    A = np.column_stack([np.ones_like(z), z])
    return v - A @ np.linalg.lstsq(A, v, rcond=None)[0]


def mantel(X, Y, Z=None):
    """Exact Mantel test of the Spearman correlation between two distance matrices.

    X, Y (and Z) are symmetric n-by-n matrices. Returns the observed correlation,
    one-sided p-values for each direction, the two-sided p-value and the number of
    permutations. Every relabelling of the clans on X is enumerated, the identity
    included. With Z, the correlation is the partial one given Z.
    """
    n = X.shape[0]
    iu = np.triu_indices(n, 1)
    y = rankdata(Y[iu])
    z = rankdata(Z[iu]) if Z is not None else None
    if z is not None:
        y = _residual(y, z)

    def stat(order):
        idx = np.asarray(order)
        x = rankdata(X[np.ix_(idx, idx)][iu])
        if z is not None:
            x = _residual(x, z)
        return _corr(x, y)

    observed = stat(range(n))
    null = np.array([stat(p) for p in permutations(range(n))])
    eps = 1e-12
    return {
        "rho": observed,
        "p_positive": float(np.mean(null >= observed - eps)),
        "p_negative": float(np.mean(null <= observed + eps)),
        "p_two_sided": float(np.mean(np.abs(null) >= abs(observed) - eps)),
        "permutations": len(null),
    }


def _sub(M, keep):
    idx = np.asarray(keep)
    return M[np.ix_(idx, idx)]


def analyses(pairs, T, D, J):
    """Main test, the inventory control, and sensitivity checks. Returns CSV rows."""
    L = mutual_loss(T)
    n = len(CLAN_ORDER)
    rows = []

    def add(name, X, Y, Z=None, clans=n):
        r = mantel(X, Y, Z)
        rows.append({"analysis": name, "clans": clans, "pairs": clans * (clans - 1) // 2,
                     **{k: round(v, 6) if isinstance(v, float) else v for k, v in r.items()}})

    add("distance vs loss", D, L)
    add("distance vs inventory divergence", D, J)
    add("loss vs inventory divergence", L, J)
    add("distance vs loss | inventory divergence", D, L, J)

    pacific = [i for i, c in enumerate(CLAN_ORDER) if c != "EC1"]
    add("Pacific only: distance vs loss", _sub(D, pacific), _sub(L, pacific), clans=len(pacific))
    add("Pacific only: distance vs loss | inventory divergence",
        _sub(D, pacific), _sub(L, pacific), _sub(J, pacific), clans=len(pacific))

    for i, c in enumerate(CLAN_ORDER):
        keep = [j for j in range(n) if j != i]
        add(f"without {c}: distance vs loss", _sub(D, keep), _sub(L, keep), clans=n - 1)

    for k in (10, 15, 25):
        for d in (3, 5, 8):
            if (k, d) != (EMB_K, EMB_D):
                add(f"embedding k={k} d={d}: distance vs loss", procrustes_distances(pairs, k, d), L)
    return rows


FIGURE_TEXT = {
    "headline": "Do clans with more different coda patterns predict each other worse?",
    "left": "how different the two clans' patterns are (a pattern is which coda tends to follow which).",
    "middle": "how badly one clan's pattern predicts the other clan's next coda.",
    "left_title": "How different are the two clans?",
    "middle_title": "How badly does one predict the other?",
    "middle_scale": "bits per coda (higher = worse prediction)",
    "y": "How badly one clan predicts the other\n(bits per coda; higher = worse)",
    "control": "which codas each clan uses",
}


def _plain(result):
    """A correlation and its p-value in words a newcomer can read."""
    p = result["p_two_sided"]
    chance = "unlikely to be chance" if p < 0.05 else "could easily be chance"
    return f"ρ = {result['rho']:+.2f} (p = {p:.3f}, {chance})"


def figure(D, L, main, partial, fname="6_distance_vs_predictability.png", text=FIGURE_TEXT):
    """Two heatmaps and a scatter: how different each pair of clans is, how badly they
    predict each other, and one against the other. `text` supplies every label."""
    clans = CLAN_ORDER
    n = len(clans)
    off = ~np.eye(n, dtype=bool)
    fig, axes = plt.subplots(1, 3, figsize=(18, 8.6), gridspec_kw={"width_ratios": [1, 1, 0.9]})

    def heat(ax, M, cmap, title, fmt, label):
        shown = np.where(off, M, np.nan)
        lo, hi = M[off].min(), M[off].max()
        # start the scale a little below the smallest value so that cell is not drawn white
        im = ax.imshow(shown, cmap=cmap, vmin=lo - 0.15 * (hi - lo), vmax=hi)
        ax.set_xticks(range(n)); ax.set_xticklabels(clans, fontsize=10)
        ax.set_yticks(range(n)); ax.set_yticklabels(clans, fontsize=10)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                r, g, b, _ = im.cmap(im.norm(M[i, j]))
                dark = 0.299 * r + 0.587 * g + 0.114 * b < 0.5
                ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center", fontsize=8.5,
                        color="white" if dark else INK)
        ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=10)
        ax.set_xlabel(label, color=MUTED, fontsize=10, labelpad=8)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cb.outline.set_visible(False)

    heat(axes[0], D, "Purples", text["left_title"], "{:.2f}",
         "Procrustes distance (0 = identical; higher = more different)")
    axes[2].set_box_aspect(1)
    heat(axes[1], L, "Blues", text["middle_title"], "{:.2f}", text["middle_scale"])

    ax = axes[2]
    iu = np.triu_indices(n, 1)
    ec1 = np.array([clans[i] == "EC1" or clans[j] == "EC1" for i, j in zip(*iu)])
    ax.scatter(D[iu][~ec1], L[iu][~ec1], s=64, color=BLUE, edgecolor="white", linewidth=1.5,
               label="both clans are from the Pacific", zorder=3)
    ax.scatter(D[iu][ec1], L[iu][ec1], s=64, color=ORANGE, marker="D", edgecolor="white",
               linewidth=1.5, label="one clan is the Caribbean clan (EC1)", zorder=3)
    ax.set_xlabel("How different the two clans are (Procrustes distance)")
    ax.set_ylabel(text["y"])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors=MUTED)
    ax.grid(True, color="#eeeeee"); ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.1), frameon=False, fontsize=10)
    ax.set_title("Each dot is one pair of clans", loc="left", fontsize=12.5, fontweight="bold",
                 color=INK, pad=52)
    ax.annotate(f"Strength of the relationship: {_plain(main)}\n"
                f"After removing the effect of {text['control']}:\n{_plain(partial)}",
                xy=(0, 1), xytext=(0, 6), xycoords="axes fraction", textcoords="offset points",
                ha="left", va="bottom", fontsize=10, color=MUTED, linespacing=1.35)

    fig.suptitle(text["headline"], x=0.03, y=0.985, ha="left", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.03, 0.935,
             "A coda is one whale call: a short burst of clicks. A clan is a group of whales that share a set of "
             "codas. EC1 is the Caribbean clan; the other seven are from the Pacific.\n"
             f"Left: {text['left']}\n"
             f"Middle: {text['middle']}\n"
             "Right: the same 28 pairs of clans, with the left measure against the middle one. If more different "
             "clans predicted each other worse, the dots would rise from left to right.\n"
             "ρ measures that rise on a scale from -1 to +1, where 0 means no relationship.",
             ha="left", va="top", fontsize=11, color=MUTED, linespacing=1.45)
    fig.subplots_adjust(left=0.05, right=0.985, top=0.69, bottom=0.15, wspace=0.3)
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    pairs = get_pairs()
    T = cross_prediction(pairs)
    D = procrustes_distances(pairs)
    J = inventory_divergence(pairs)
    L = mutual_loss(T)
    rows = analyses(pairs, T, D, J)

    OUT.mkdir(exist_ok=True)
    with (OUT / "drift.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with (OUT / "drift_pairs.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["A", "B", "procrustes_distance", "predictability_lost_bits", "inventory_js_bits"])
        for i, j in zip(*np.triu_indices(len(CLAN_ORDER), 1)):
            w.writerow([CLAN_ORDER[i], CLAN_ORDER[j], round(D[i, j], 4), round(L[i, j], 4), round(J[i, j], 4)])

    for r in rows:
        print(f"{r['analysis']:<58} n={r['clans']} rho={r['rho']:+.3f} "
              f"p(two-sided)={r['p_two_sided']:.4f} p(+)={r['p_positive']:.4f}")
    figure(D, L, rows[0], rows[3])
    print("\nwrote results/drift.csv, results/drift_pairs.csv, figures/plain/6_distance_vs_predictability.png")


if __name__ == "__main__":
    main()

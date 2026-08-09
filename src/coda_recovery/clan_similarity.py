"""How similar are clans' sequencing 'grammars'? Two measures over a shared global
(rhythm, tempo) token space (rhythm = nearest EC1 template; tempo = EC1 duration
bins — so tokens mean the same thing across clans).

1. CROSS-PREDICTION (interpretable, MI-native): train the bigram P(next|current)
   on clan A, and score clan B's held-out codas against B's OWN frequency baseline.
   transfer[A→B] (bits/coda) = how much A's grammar predicts B beyond B's base
   rates. Diagonal = within-clan predictive information. Off-diagonal > 0 = shared
   grammar. Asymmetry is informative.

2. PROCRUSTES on PMI embeddings (the MUSE version): embed each clan's shared tokens
   via SVD of its pointwise-mutual-information matrix, orthogonally align two clans
   (tokens correspond, since the scheme is global), and read the residual as a
   rotation-invariant structural DISTANCE. Small = similar geometry of associations.

Run:  python -m coda_recovery.clan_similarity
"""
from __future__ import annotations

import csv
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import orthogonal_procrustes

from .predictive_info import ALPHA
from .standardize import clan_frame, pooled_pairs, ALL_CLANS

REPO = Path(__file__).resolve().parents[2]
FIG = REPO / "figures" / "plain"
OUT = REPO / "results"
CLAN_ORDER = ALL_CLANS
NREP = 15
EMB_K, EMB_D = 15, 5


def get_pairs():
    """clan -> list of (cv_unit, (rhythm,tempo), (rhythm,tempo)) over shared global
    tokens, every clan through the SAME uniform pipeline (EC1 included — no special
    native treatment), so cross-clan comparison is apples-to-apples."""
    tok = lambda r: (int(r.rhythm), int(r.tempo))
    return {clan: pooled_pairs(clan_frame(clan, tempo="global"), tok) for clan in ALL_CLANS}


def cross_prediction(pairs):
    clans = CLAN_ORDER
    vocab = set()
    for pr in pairs.values():
        for _, a, b in pr:
            vocab |= {a, b}
    V = len(vocab)
    acc = defaultdict(list)
    for rep in range(NREP):
        rng = np.random.default_rng(rep)
        train, test = {}, {}
        for c in clans:
            units = sorted({u for u, _, _ in pairs[c]}, key=str)
            u = np.array(units, dtype=object); rng.shuffle(u)
            te = set(u[:max(1, len(u) // 3)])
            train[c] = [p for p in pairs[c] if p[0] not in te]
            test[c] = [p for p in pairs[c] if p[0] in te]
        bi, rowsum, uni, Nu = {}, {}, {}, {}
        for c in clans:
            b = defaultdict(Counter); rs = Counter(); un = Counter()
            for _, x, y in train[c]:
                b[x][y] += 1; rs[x] += 1; un[y] += 1
            bi[c], rowsum[c], uni[c], Nu[c] = b, rs, un, sum(un.values())
        for i, A in enumerate(clans):
            for j, B in enumerate(clans):
                g = []
                for _, x, y in test[B]:
                    p_uni = (uni[B][y] + ALPHA) / (Nu[B] + ALPHA * V)
                    p_bi = (bi[A][x][y] + ALPHA) / (rowsum[A].get(x, 0) + ALPHA * V)
                    g.append(np.log2(p_bi) - np.log2(p_uni))
                acc[(i, j)].append(np.mean(g) if g else np.nan)
    n = len(clans)
    return np.array([[np.nanmean(acc[(i, j)]) for j in range(n)] for i in range(n)])


def procrustes_distances(pairs):
    cnt = Counter()
    for pr in pairs.values():
        for _, a, b in pr:
            cnt[a] += 1; cnt[b] += 1
    index = [t for t, _ in cnt.most_common(EMB_K)]
    idx = {t: i for i, t in enumerate(index)}
    emb = {}
    for c, pr in pairs.items():
        C = np.full((EMB_K, EMB_K), 0.5)
        for _, a, b in pr:
            if a in idx and b in idx:
                C[idx[a], idx[b]] += 1
        P = C / C.sum()
        pi = P.sum(1, keepdims=True); pj = P.sum(0, keepdims=True)
        PMI = np.log(P / (pi * pj))
        U, S, _ = np.linalg.svd(PMI)
        emb[c] = U[:, :EMB_D] * np.sqrt(S[:EMB_D])
    # Scale each embedding to unit Frobenius norm BEFORE aligning, so the distance
    # is symmetric (D[A,B] == D[B,A]) and scale-free. Dividing the residual by the
    # target's norm — as an earlier version did — broke symmetry, because clans'
    # embeddings differ in magnitude. The rotation-aligned residual between two
    # unit-norm matrices is symmetric by construction.
    en = {c: e / np.linalg.norm(e) for c, e in emb.items()}
    clans = CLAN_ORDER
    D = np.zeros((len(clans), len(clans)))
    for i, A in enumerate(clans):
        for j, B in enumerate(clans):
            R, _ = orthogonal_procrustes(en[A], en[B])
            D[i, j] = np.linalg.norm(en[A] @ R - en[B])
    return D


def _heatmap(M, title, sub, fname, cmap, fmt="{:+.2f}", norm=None,
             xlabel="predicted clan (B)", ylabel="model clan (A)"):
    clans = CLAN_ORDER
    fig, ax = plt.subplots(figsize=(7.6, 6.6))
    im = ax.imshow(M, cmap=cmap, norm=norm)
    ax.set_xticks(range(len(clans))); ax.set_xticklabels(clans, fontsize=10)
    ax.set_yticks(range(len(clans))); ax.set_yticklabels(clans, fontsize=10)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    for i in range(len(clans)):
        for j in range(len(clans)):
            v = M[i, j]
            r, g, b, _ = im.cmap(im.norm(v))      # text color from the actual cell color
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=8,
                    color="white" if lum < 0.5 else "#222")
    if sub:
        if "$" not in sub:                       # math subtitles arrive pre-wrapped
            sub = textwrap.fill(sub, width=74)    # (textwrap would split $...$ spans)
        ax.set_title(title, loc="left", fontweight="bold", pad=16 + 13 * (sub.count("\n") + 1),
                     color="#222")
        ax.annotate(sub, xy=(0, 1), xytext=(0, 8), xycoords="axes fraction",
                    textcoords="offset points", fontsize=10, color="#666", linespacing=1.3)
    else:
        ax.set_title(title, loc="left", fontweight="bold", pad=12, color="#222")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout(); FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / fname, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    pairs = get_pairs()
    print("clan pairs:", {c: len(p) for c, p in pairs.items()})

    T = cross_prediction(pairs)
    print("\nCROSS-PREDICTION transfer[A->B] (bits/coda; diagonal = within-clan MI):")
    print("        " + "".join(f"{c:>7}" for c in CLAN_ORDER))
    for i, A in enumerate(CLAN_ORDER):
        print(f"{A:>7} " + "".join(f"{T[i, j]:>7.2f}" for j in range(len(CLAN_ORDER))))

    D = procrustes_distances(pairs)
    print("\nPROCRUSTES distance between clan token-embeddings (0 = identical geometry):")
    print("        " + "".join(f"{c:>7}" for c in CLAN_ORDER))
    for i, A in enumerate(CLAN_ORDER):
        print(f"{A:>7} " + "".join(f"{D[i, j]:>7.2f}" for j in range(len(CLAN_ORDER))))

    # off-diagonal transfer as a fraction of the target clan's own within-clan MI
    self_mi = np.diag(T)
    off = T.copy(); np.fill_diagonal(off, np.nan)
    print(f"\nmean within-clan MI (diagonal): {self_mi.mean():.2f} bits")
    print(f"mean cross-clan transfer (off-diagonal): {np.nanmean(off):.2f} bits "
          f"({100*np.nanmean(off)/self_mi.mean():.0f}% of within-clan)")

    OUT.mkdir(exist_ok=True)
    with (OUT / "clan_similarity.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["measure", "A"] + CLAN_ORDER)
        for i, A in enumerate(CLAN_ORDER):
            w.writerow(["cross_prediction_bits", A] + [round(T[i, j], 4) for j in range(len(CLAN_ORDER))])
        for i, A in enumerate(CLAN_ORDER):
            w.writerow(["procrustes_distance", A] + [round(D[i, j], 4) for j in range(len(CLAN_ORDER))])

    from matplotlib.colors import TwoSlopeNorm
    # cross-prediction is diverging around a meaningful zero (positive = shared
    # grammar, negative = actively mis-predicts): two hues, neutral (white) at 0.
    tnorm = TwoSlopeNorm(vmin=float(np.nanmin(T)), vcenter=0.0, vmax=float(np.nanmax(T)))
    _heatmap(T, "Does one clan's sequence structure predict another's next coda?",
             "Each cell (bits/coda) = average over clan B's codas of\n"
             r"$\log_{2}\,P_A(\mathrm{next}\mid\mathrm{current})\;-\;\log_{2}\,F_B(\mathrm{next})$,"
             "\n"
             r"where $P_A$ = clan A's transition probability and $F_B$ = clan B's overall coda frequency.",
             "4_grammar_is_clan_specific.png", "RdBu_r", norm=tnorm)
    # Procrustes distance is sequential magnitude (0 = identical): one hue, light→dark.
    _heatmap(D, "Each clan's sequencing has its own distinct shape",
             "Each cell = Procrustes distance: the smallest ‖A·R − B‖ over rotations R, where A and B "
             "are the two clans' unit-normalized (rhythm,tempo) transition embeddings "
             "(0 = the two clans' transition patterns are identical; larger = more different).",
             "5_grammar_geometry.png", "Purples", fmt="{:.2f}", xlabel="clan", ylabel="clan")
    print("\nwrote results/clan_similarity.csv, figures plain/4 & plain/5")


if __name__ == "__main__":
    main()

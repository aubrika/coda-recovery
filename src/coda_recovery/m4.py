"""M4 diagnostics & views (spec 8).

Static PNG (matplotlib): confusion matrix, transition triptych, null histogram.
Interactive HTML (plotly): the volumetric structural embedding (GATED on the
spectrum — it is decoration here, 26.6% variance in 3 dims, and labelled so) and
the acoustic-vs-structural contrast (8.2, "the comparison is the point").
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .inventory import load_raw, coda_mask
from .transitions import coda_type_index, build_transitions
from .pipeline import build_split_sets
from .recover import qap_recover, perm_to_matrix, frobenius_objective
from .nulls import shuffle_within_segments, random_permutation_null

REPO = Path(__file__).resolve().parents[2]
FIG = REPO / "figures"
ALPHA = 1.0


def _spectral3(T):
    S = 0.5 * (T + T.T)
    w, V = np.linalg.eigh(S)
    order = np.argsort(w)[::-1]
    w, V = w[order], V[:, order]
    # drop the trivial Perron mode (index 0); take next 3 structural dims
    return V[:, 1:4] * np.sqrt(np.abs(w[1:4])), w


def confusion_over_splits(df, types, n_splits=60):
    """M[i,j] = # of random splits where QAP maps type i -> j. Diagonal is
    correct recovery; off-diagonal mass marks structurally degenerate types
    (the direct read-out of effective structural resolution, spec 8.3)."""
    n = len(types)
    M = np.zeros((n, n))
    for s in range(n_splits):
        A, B = build_split_sets(df, types, "random", "pooled", ALPHA, s)
        r = qap_recover(A.T, B.T, n_restarts=20, seed=s)
        for i, j in enumerate(r.perm):
            M[i, j] += 1
    return M / n_splits


def fig_confusion(df, types):
    M = confusion_over_splits(df, types)
    freq = build_transitions(df, types, "pooled", ALPHA).C
    order = np.argsort(-(freq.sum(0) + freq.sum(1)))          # by frequency
    Mo = M[np.ix_(order, order)]
    labs = [types[i] for i in order]
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(Mo, cmap="magma", vmin=0, vmax=1)
    ax.set_xticks(range(len(types))); ax.set_xticklabels(labs, rotation=90, fontsize=7)
    ax.set_yticks(range(len(types))); ax.set_yticklabels(labs, fontsize=7)
    ax.set_xlabel("recovered as"); ax.set_ylabel("true type")
    diag = np.diag(Mo).mean()
    ax.set_title(f"Recovery confusion over 60 random splits\n"
                 f"(types ordered by frequency; mean diagonal = {diag:.2f})")
    fig.colorbar(im, label="fraction of splits", fraction=0.046)
    fig.tight_layout(); FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "confusion.png", dpi=140); plt.close(fig)
    return diag


def fig_triptych(df, types):
    A, B = build_split_sets(df, types, "random", "pooled", ALPHA, 1)
    r = qap_recover(A.T, B.T, n_restarts=30, seed=1)
    P = perm_to_matrix(r.perm)
    freq = A.C.sum(0) + A.C.sum(1) + B.C.sum(0) + B.C.sum(1)
    o = np.argsort(-freq)
    mats = [A.T[np.ix_(o, o)], B.T[np.ix_(o, o)], (P @ A.T @ P.T)[np.ix_(o, o)]]
    titles = ["T_A", "T_B", "P·T_A·Pᵀ (A relabelled → B)"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4))
    for ax, m, t in zip(axes, mats, titles):
        ax.imshow(m, cmap="viridis"); ax.set_title(t, fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Transition triptych — types ordered by frequency "
                 "(middle should resemble right if recovery worked)", fontsize=11)
    fig.tight_layout(); FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "triptych.png", dpi=140); plt.close(fig)


def fig_null_histogram(df, types):
    A, B = build_split_sets(df, types, "random", "pooled", ALPHA, 1)
    obs = qap_recover(A.T, B.T, n_restarts=30, seed=1).objective
    rand_null = random_permutation_null(A.T, B.T, n=3000, seed=1)
    strong = []
    for i in range(120):
        sh = shuffle_within_segments(df, seed=3000 + i)
        nA, nB = build_split_sets(sh, types, "random", "pooled", ALPHA, 1)
        strong.append(qap_recover(nA.T, nB.T, n_restarts=8, seed=1,
                                  refine_2opt=False).objective)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.hist(rand_null, bins=40, alpha=0.5, color="#999", label="random-perm null")
    ax.hist(strong, bins=25, alpha=0.6, color="#b8860b", label="strong null (recovered)")
    ax.axvline(obs, color="#1b6ca8", lw=2.5, label=f"observed QAP = {obs:.3f}")
    ax.set_xlabel("recovered objective ‖P·T_A·Pᵀ − T_B‖_F"); ax.set_ylabel("count")
    ax.set_title("Observed recovery vs nulls (lower = better match)")
    ax.legend(fontsize=9); fig.tight_layout(); FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "null_histogram.png", dpi=140); plt.close(fig)


def _type_acoustics(df, types):
    codas = df[coda_mask(df)]
    rows = []
    for t in types:
        sub = codas[codas["CodaName"] == t]
        icis = sub[[f"ICI{i}" for i in range(1, 10)]].to_numpy()
        icis = np.where(icis > 0, icis, np.nan)
        cv = np.nanstd(icis, axis=1) / (np.nanmean(icis, axis=1) + 1e-9)
        rows.append({"type": t, "nclicks": sub["nClicks"].mean(),
                     "duration": sub["Length"].mean(), "rhythm": np.nanmean(cv),
                     "freq": len(sub)})
    return pd.DataFrame(rows)


def html_volumetric(df, types):
    """3D structural embedding, both halves aligned. LABELLED DECORATION: the
    spectrum is flat (26.6% variance in 3 dims), so proximity here is only
    weakly meaningful — see caption baked into the title."""
    A, B = build_split_sets(df, types, "random", "pooled", ALPHA, 1)
    r = qap_recover(A.T, B.T, n_restarts=30, seed=1)
    XA, w = _spectral3(A.T)
    XB, _ = _spectral3(B.T)
    # align B's embedding to A via the recovered correspondence (Procrustes)
    from scipy.linalg import orthogonal_procrustes
    R, _ = orthogonal_procrustes(XB[r.perm], XA)
    XBa = XB @ R
    freq = A.C.sum(0) + A.C.sum(1)
    var3 = np.abs(w[1:4]).sum() / np.abs(w[1:]).sum()
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=XA[:, 0], y=XA[:, 1], z=XA[:, 2], mode="markers+text",
        text=types, textposition="top center", name="half A",
        marker=dict(size=6 + 14 * freq / freq.max(), color="#1b6ca8")))
    fig.add_trace(go.Scatter3d(x=XBa[r.perm, 0], y=XBa[r.perm, 1], z=XBa[r.perm, 2],
        mode="markers", name="half B (aligned)",
        marker=dict(size=5, color="#b8860b", symbol="diamond")))
    for i in range(len(types)):
        j = r.perm[i]
        fig.add_trace(go.Scatter3d(
            x=[XA[i, 0], XBa[j, 0]], y=[XA[i, 1], XBa[j, 1]], z=[XA[i, 2], XBa[j, 2]],
            mode="lines", line=dict(color="#ccc", width=2), showlegend=False))
    fig.update_layout(title=f"Structural embedding (DECORATION — flat spectrum, "
                      f"only {var3*100:.0f}% variance in these 3 dims; short "
                      f"segments = correct correspondences)",
                      margin=dict(l=0, r=0, t=40, b=0))
    FIG.mkdir(exist_ok=True)
    fig.write_html(str(FIG / "volumetric.html"), include_plotlyjs="cdn")


def html_acoustic(df, types):
    """Types in acoustic space (clicks, duration/tempo, rhythm), coloured by a
    structural coordinate. If acoustic neighbours are structural neighbours,
    form and combinatorial role are entangled; if they cross-cut, separable."""
    ac = _type_acoustics(df, types)
    ts = build_transitions(df, types, "pooled", ALPHA)
    X, _ = _spectral3(ts.T)
    struct_axis = X[:, 0]                       # 1st non-trivial structural dim
    fig = go.Figure(go.Scatter3d(
        x=ac["nclicks"], y=ac["duration"], z=ac["rhythm"], mode="markers+text",
        text=ac["type"], textposition="top center",
        marker=dict(size=6 + 14 * ac["freq"] / ac["freq"].max(),
                    color=struct_axis, colorscale="RdBu", showscale=True,
                    colorbar=dict(title="structural<br>axis")),
    ))
    fig.update_layout(title="Acoustic space coloured by structural position — "
                      "do colours cluster (entangled) or cross-cut (separable)?",
                      scene=dict(xaxis_title="click count", yaxis_title="duration (s)",
                                 zaxis_title="rhythm (ICI CV)"),
                      margin=dict(l=0, r=0, t=40, b=0))
    FIG.mkdir(exist_ok=True)
    fig.write_html(str(FIG / "acoustic.html"), include_plotlyjs="cdn")


def main():
    df = load_raw(); types = coda_type_index(df)
    diag = fig_confusion(df, types)
    print(f"confusion.png  (mean diagonal = {diag:.3f})")
    fig_triptych(df, types); print("triptych.png")
    fig_null_histogram(df, types); print("null_histogram.png")
    html_volumetric(df, types); print("volumetric.html (labelled decoration)")
    html_acoustic(df, types); print("acoustic.html")


if __name__ == "__main__":
    main()

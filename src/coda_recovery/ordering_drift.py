"""Does ordering carry over between clans once inventory is taken out?

drift.py found that Procrustes distance and cross-prediction both follow which
codas a clan uses. This module rebuilds both measures so that inventory cannot
drive them, and asks the question again of ordering alone.

Tokens. Each feature is analysed on the tokens every clan uses: the duration bins,
or the rhythm classes, with at least MIN_CODAS codas in every clan. Pairs touching
any other token are dropped. The combined rhythm-and-tempo token is left out,
because no combined token reaches that count in all eight clans.

Transfer. Which coda follows which has two parts: how common each coda is (the
margins of the transition table) and how the table departs from what those
frequencies alone would give (its odds ratios). The odds ratios are the ordering.
To predict clan B from clan A, A's transition table is rescaled by iterative
proportional fitting until its margins equal B's. That keeps A's odds ratios and
takes every frequency from B. It is scored on B's held-out recordings against the
table with B's margins and no association at all. A's coda frequencies never
enter, so a different inventory costs nothing: if A's ordering says nothing about
B's, the gain is zero, not negative. "Ordering lost" for a pair is each clan's own
gain minus the gain from the other clan's ordering, averaged both ways.

Distance. Procrustes distance between PMI embeddings built on the same shared
token set, so no cell stands for a coda that a clan does not use.

The primary analysis scores only pairs where the coda changes, with both models
told that it changes, because repetition is shared by every clan. The all-pairs
version is reported alongside.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.linalg import orthogonal_procrustes

from .clan_similarity import CLAN_ORDER, EMB_D, NREP, get_pairs
from .drift import _sub, figure, mantel
from .predictive_info import ALPHA

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results"
MIN_CODAS = 20
FEATURES = {"tempo": lambda t: t[1], "rhythm": lambda t: t[0]}


def shared_tokens(pairs, feature, min_codas=MIN_CODAS):
    """Tokens of one feature with at least min_codas codas in every clan."""
    key = FEATURES[feature]
    counts = {c: Counter() for c in pairs}
    for c, pr in pairs.items():
        for _, a, b in pr:
            counts[c][key(a)] += 1
            counts[c][key(b)] += 1
    every = set.union(*(set(v) for v in counts.values()))
    # each coda inside a recording is counted once as a source and once as a destination
    return sorted(t for t in every if all(counts[c][t] >= 2 * min_codas for c in pairs))


def project(pairs, feature, tokens):
    """Recording pairs reduced to one feature, as indices into the shared token set."""
    key, idx = FEATURES[feature], {t: i for i, t in enumerate(tokens)}
    return {c: [(u, idx[key(a)], idx[key(b)]) for u, a, b in pr if key(a) in idx and key(b) in idx]
            for c, pr in pairs.items()}


def count_matrix(prs, k):
    N = np.zeros((k, k))
    for _, a, b in prs:
        N[a, b] += 1
    return N


def smoothed(N, changes):
    """Counts plus the usual pseudo-count; a repeat is impossible when scoring changes only."""
    M = N + ALPHA
    if changes:
        np.fill_diagonal(M, 0.0)
    return M


def rake(M, rows, cols, iterations=500, tol=1e-10):
    """Iterative proportional fitting: rescale M to the given margins, keeping its odds ratios.

    Zero cells stay zero, so a blanked diagonal survives.
    """
    M = M.astype(float).copy()
    for _ in range(iterations):
        M *= (rows / M.sum(1))[:, None]
        M *= (cols / M.sum(0))[None, :]
        if np.abs(M.sum(1) - rows).max() < tol * rows.sum():
            break
    return M


def predictions(N_source, N_target, changes):
    """P(next | current) for the target clan: the source's odds ratios on the target's margins.

    With N_source=None the table has no association at all, which is the baseline.
    """
    target = smoothed(N_target, changes)
    start = smoothed(N_source, changes) if N_source is not None else (target > 0).astype(float)
    M = rake(start, target.sum(1), target.sum(0))
    return M / M.sum(1, keepdims=True)


def transfer_gain(N_source, N_train, N_test, changes):
    """Bits per scored pair gained on the target's test pairs by adding the source's
    ordering to the target's own frequencies."""
    Q = predictions(N_source, N_train, changes)
    F = predictions(None, N_train, changes)
    T = N_test.copy()
    if changes:
        np.fill_diagonal(T, 0.0)
    scored = T > 0
    return float(np.sum(T[scored] * (np.log2(Q[scored]) - np.log2(F[scored]))) / T.sum())


def transfer_matrix(proj, k, changes, nrep=NREP):
    """G[i, j]: gain on clan j's held-out recordings using clan i's ordering.

    The diagonal is each clan's own gain. Recordings are split as in clan_similarity:
    a third held out, repeated nrep times with fixed seeds.
    """
    clans = CLAN_ORDER
    acc = np.zeros((nrep, len(clans), len(clans)))
    for rep in range(nrep):
        rng = np.random.default_rng(rep)
        train, test = {}, {}
        for c in clans:
            units = np.array(sorted({u for u, _, _ in proj[c]}, key=str), dtype=object)
            rng.shuffle(units)
            held = set(units[:max(1, len(units) // 3)])
            train[c] = count_matrix([p for p in proj[c] if p[0] not in held], k)
            test[c] = count_matrix([p for p in proj[c] if p[0] in held], k)
        for i, a in enumerate(clans):
            for j, b in enumerate(clans):
                acc[rep, i, j] = transfer_gain(train[a], train[b], test[b], changes)
    return acc.mean(0)


def ordering_lost(G):
    """Own gain minus the gain from the other clan's ordering, averaged both ways."""
    own = np.diag(G)
    lost = own[None, :] - G          # lost[i, j]: predicting j with i's ordering
    return (lost + lost.T) / 2


def embedding_distance(proj, k, changes, d=EMB_D):
    """Procrustes distance between clans' PMI embeddings on the shared token set."""
    emb = {}
    for c in CLAN_ORDER:
        C = smoothed(count_matrix(proj[c], k), changes)
        # expected counts with the same margins and no association
        expected = rake((C > 0).astype(float), C.sum(1), C.sum(0))
        ratio = np.divide(C, expected, out=np.ones_like(C), where=C > 0)
        PMI = np.log(ratio)                      # zero on a blanked diagonal
        U, S, _ = np.linalg.svd(PMI)
        e = U[:, :d] * np.sqrt(S[:d])
        emb[c] = e / np.linalg.norm(e)
    n = len(CLAN_ORDER)
    D = np.zeros((n, n))
    for i, a in enumerate(CLAN_ORDER):
        for j, b in enumerate(CLAN_ORDER):
            R, _ = orthogonal_procrustes(emb[a], emb[b])
            D[i, j] = np.linalg.norm(emb[a] @ R - emb[b])
    return D


def frequency_divergence(proj, k):
    """Jensen-Shannon divergence (bits) between clans' frequencies on the shared tokens."""
    P = np.array([count_matrix(proj[c], k).sum(0) + count_matrix(proj[c], k).sum(1) for c in CLAN_ORDER])
    P = P / P.sum(1, keepdims=True)

    def kl(p, q):
        m = p > 0
        return float(np.sum(p[m] * np.log2(p[m] / q[m])))

    n = len(CLAN_ORDER)
    J = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mid = (P[i] + P[j]) / 2
            J[i, j] = (kl(P[i], mid) + kl(P[j], mid)) / 2
    return J


def sample_size(proj):
    """Minus the log of the smaller clan's pair count: larger means less data in the pair."""
    n = np.array([len(proj[c]) for c in CLAN_ORDER], dtype=float)
    return -np.log(np.minimum(n[:, None], n[None, :]))


def run(pairs, feature, changes, min_codas=MIN_CODAS):
    tokens = shared_tokens(pairs, feature, min_codas)
    proj = project(pairs, feature, tokens)
    k = len(tokens)
    G = transfer_matrix(proj, k, changes)
    return {"tokens": tokens, "proj": proj, "G": G, "L": ordering_lost(G),
            "D": embedding_distance(proj, k, changes),
            "J": frequency_divergence(proj, k), "S": sample_size(proj)}


def main():
    pairs = get_pairs()
    n = len(CLAN_ORDER)
    off = ~np.eye(n, dtype=bool)
    pacific = [i for i, c in enumerate(CLAN_ORDER) if c != "EC1"]
    rows, pair_rows, primary, summary = [], [], {}, []

    def add(feature, scoring, name, res, X, Y, Z=None, keep=None):
        if keep is not None:
            X, Y, Z = _sub(X, keep), _sub(Y, keep), (None if Z is None else _sub(Z, keep))
        m = mantel(X, Y, Z)
        rows.append({"feature": feature, "scoring": scoring, "analysis": name,
                     "tokens": len(res["tokens"]), "clans": X.shape[0],
                     **{k_: round(v, 6) if isinstance(v, float) else v for k_, v in m.items()}})
        return m

    for feature in FEATURES:
        for changes in (True, False):
            scoring = "changes only" if changes else "all pairs"
            res = run(pairs, feature, changes)
            G, L, D, J, Sz = res["G"], res["L"], res["D"], res["J"], res["S"]
            main_test = add(feature, scoring, "distance vs ordering lost", res, D, L)
            given_freq = add(feature, scoring, "distance vs ordering lost | frequency divergence", res, D, L, J)
            add(feature, scoring, "distance vs ordering lost | sample size", res, D, L, Sz)
            add(feature, scoring, "distance vs frequency divergence", res, D, J)
            add(feature, scoring, "ordering lost vs frequency divergence", res, L, J)
            add(feature, scoring, "Pacific only: distance vs ordering lost", res, D, L, keep=pacific)
            own = np.diag(G)
            print(f"\n{feature}, {scoring}: {len(res['tokens'])} shared tokens {res['tokens']}")
            print(f"  own gain {own.min():+.3f} to {own.max():+.3f} bits, mean {own.mean():+.3f}; "
                  f"foreign ordering helps in {(G[off] > 0).sum()} of {off.sum()} ordered pairs, "
                  f"mean {G[off].mean():+.3f} bits")
            summary.append([feature, scoring, len(res["tokens"]), min(len(proj_) for proj_ in res["proj"].values()),
                            round(own.min(), 4), round(own.max(), 4), round(own.mean(), 4),
                            int((own > 0).sum()), int((G[off] > 0).sum()), int(off.sum()),
                            round(G[off].mean(), 4)])
            print(f"  distance vs ordering lost: rho={main_test['rho']:+.3f} p={main_test['p_two_sided']:.4f}; "
                  f"given frequency divergence: rho={given_freq['rho']:+.3f} p={given_freq['p_two_sided']:.4f}")
            for i in range(n):
                for j in range(n):
                    pair_rows.append([feature, scoring, CLAN_ORDER[i], CLAN_ORDER[j], round(G[i, j], 4),
                                      round(D[i, j], 4), round(L[i, j], 4), round(J[i, j], 4)])
            if changes:
                primary[feature] = (D, L, main_test, given_freq)

    OUT.mkdir(exist_ok=True)
    with (OUT / "ordering_drift.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with (OUT / "ordering_transfer.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["feature", "scoring", "shared_tokens", "fewest_pairs_in_a_clan", "own_gain_min",
                    "own_gain_max", "own_gain_mean", "clans_with_positive_own_gain",
                    "ordered_pairs_helped", "ordered_pairs", "foreign_gain_mean"])
        w.writerows(summary)
    with (OUT / "ordering_drift_pairs.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["feature", "scoring", "source", "target", "transfer_gain_bits",
                    "procrustes_distance", "ordering_lost_bits", "frequency_js_bits"])
        w.writerows(pair_rows)

    plain = {"tempo": "tempo (how long a coda lasts)", "rhythm": "rhythm (the pattern of gaps between clicks)"}
    for num, feature in ((7, "tempo"), (8, "rhythm")):
        D, L, main_test, given_freq = primary[feature]
        figure(D, L, main_test, given_freq, fname=f"{num}_ordering_{feature}.png", text={
            "headline": f"{feature.capitalize()} only: do clans with a more different order of {feature}s "
                        "predict each other worse?",
            "left": f"how different the two clans are in which {feature} tends to follow which. "
                    f"This looks at {plain[feature]} alone, not the whole coda.",
            "middle": f"how much worse a clan's next {feature} is predicted when the other clan's order is used "
                      f"instead of its own. Only pairs of codas where the {feature} changes are counted.",
            "left_title": f"How different is the order of {feature}s?",
            "middle_title": "How much worse than a clan's own order?",
            "middle_scale": "bits per pair of codas (higher = worse; 0 = just as good)",
            "y": "Worse than the clan's own order by\n(bits per pair of codas)",
            "control": f"how common each {feature} is in each clan",
        })
    print("\nwrote results/ordering_drift.csv, ordering_transfer.csv, ordering_drift_pairs.csv, figures 7 and 8")


if __name__ == "__main__":
    main()

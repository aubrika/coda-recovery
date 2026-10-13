"""Do clans order whole codas differently, once inventory is accounted for?

A coda here is a rhythm class together with a duration bin. Clans share too few
whole coda types to compare their transition tables directly, so each clan's
ordering is described by a factored model instead.

Model. Counts are kept as a four-way table N[r, t, r', t']: current rhythm and
tempo, next rhythm and tempo. The model is log-linear, fitted by iterative
proportional fitting to these margins of the table:

    (r, t)    how common each coda is as the current one      inventory
    (r', t')  how common each coda is as the next one         inventory
    (r, r')   rhythm to rhythm                                ordering
    (t, t')   tempo to tempo                                  ordering
    (r, t')   rhythm to next tempo                            ordering
    (t, r')   tempo to next rhythm                            ordering

The two inventory margins say which codas a clan uses. The four ordering margins
say how the next coda depends on the current one. Each is a small, dense table, so
the model can speak about a coda type a clan rarely uses, as long as the clan uses
its rhythm and its tempo.

Carrying ordering over. To predict clan B from clan A, A's fitted table is rescaled
until its two inventory margins equal B's. That keeps every odds ratio between
current and next coda from A and takes every coda frequency from B. It is scored on
B's held-out recordings against the table with B's inventory and no dependence of
next on current. If A's ordering says nothing about B's, the gain is zero.

Distance. Each clan's fitted table is rescaled to one common inventory (all clans
pooled), so that tables differ only in ordering. Its standardized residuals from
independence are embedded by singular value decomposition, and embeddings are
compared by Procrustes distance.

Changes-only scoring, the primary analysis, makes a repeat of the same coda a
structural zero in every table.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy.linalg import orthogonal_procrustes

from .clan_similarity import CLAN_ORDER, EMB_D, NREP, get_pairs
from .drift import _sub, figure, inventory_divergence, mantel
from .predictive_info import ALPHA

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results"

INVENTORY = [(0, 1), (2, 3)]
ORDERING = {"rhythm→rhythm": (0, 2), "tempo→tempo": (1, 3),
            "rhythm→tempo": (0, 3), "tempo→rhythm": (1, 2)}
MODELS = {
    "tempo→tempo only": ["tempo→tempo"],
    "rhythm→rhythm only": ["rhythm→rhythm"],
    "both, no cross terms": ["rhythm→rhythm", "tempo→tempo"],
    "factored": list(ORDERING),
}


def shape_of(pairs):
    tokens = [t for pr in pairs.values() for _, a, b in pr for t in (a, b)]
    return max(r for r, _ in tokens) + 1, max(t for _, t in tokens) + 1


def count_table(prs, R, T):
    N = np.zeros((R, T, R, T))
    for _, (r, t), (r2, t2) in prs:
        N[r, t, r2, t2] += 1
    return N


def allowed(R, T, changes):
    """1 where a transition can occur; a repeat of the same coda cannot under changes-only."""
    A = np.ones((R, T, R, T))
    if changes:
        r, t = np.meshgrid(np.arange(R), np.arange(T), indexing="ij")
        A[r, t, r, t] = 0.0
    return A


def smoothed(N, changes):
    """Counts plus a uniform prior worth ALPHA pseudo-pairs per rhythm-to-rhythm cell."""
    R, T = N.shape[:2]
    A = allowed(R, T, changes)
    return N * A + A * (ALPHA * R * R / A.sum())


def margin(X, axes):
    return X.sum(tuple(i for i in range(X.ndim) if i not in axes), keepdims=True)


def fit(X, margins, start, iterations=2000, tol=1e-9):
    """Iterative proportional fitting of `start` to the given margins of X.

    Zero cells of `start` stay zero. Returns the table of the log-linear model whose
    only interactions are the fitted margins.
    """
    targets = [(axes, margin(X, axes)) for axes in margins]
    M = start * (X.sum() / start.sum())
    for _ in range(iterations):
        worst = 0.0
        for axes, target in targets:
            current = margin(M, axes)
            worst = max(worst, float(np.abs(current - target).max()))
            M = M * np.divide(target, current, out=np.zeros_like(target), where=current > 0)
        if worst < tol * X.sum():
            break
    return M


def fit_model(N, changes, terms):
    """A clan's table under the model with the named ordering terms."""
    X = smoothed(N, changes)
    return fit(X, INVENTORY + [ORDERING[t] for t in terms], allowed(*N.shape[:2], changes))


def with_inventory(M, target):
    """Rescale table M to the inventory margins of `target`, keeping M's ordering."""
    return fit(target, INVENTORY, M)


def gain(Q, F, N_test):
    """Bits per scored pair: log2 of predicted P(next | current) under Q, minus under F."""
    k = Q.shape[0] * Q.shape[1]
    q, f, t = Q.reshape(k, k), F.reshape(k, k), N_test.reshape(k, k) * (F.reshape(k, k) > 0)
    q = q / q.sum(1, keepdims=True)
    f = f / f.sum(1, keepdims=True)
    scored = t > 0
    return float(np.sum(t[scored] * (np.log2(q[scored]) - np.log2(f[scored]))) / t.sum())


def split(pairs, rep):
    """Train and test count tables per clan: a third of recordings held out, seeded by rep."""
    R, T = shape_of(pairs)
    rng = np.random.default_rng(rep)
    train, test = {}, {}
    for c in CLAN_ORDER:
        units = np.array(sorted({u for u, _, _ in pairs[c]}, key=str), dtype=object)
        rng.shuffle(units)
        held = set(units[:max(1, len(units) // 3)])
        train[c] = count_table([p for p in pairs[c] if p[0] not in held], R, T)
        test[c] = count_table([p for p in pairs[c] if p[0] in held], R, T)
    return train, test


def evaluate(pairs, changes, nrep=NREP):
    """Held-out gains for every model, from a clan's own ordering and from each other clan's.

    Returns G[model][i, j], the gain on clan j using clan i's ordering (the diagonal is
    a clan's own), the spread of the factored model's gains over splits, and the own
    gain of the unfactored bigram over whole codas, for reference.
    """
    n = len(CLAN_ORDER)
    G = {m: np.zeros((nrep, n, n)) for m in MODELS}
    full = np.zeros((nrep, n))
    for rep in range(nrep):
        train, test = split(pairs, rep)
        A = allowed(*shape_of(pairs), changes)
        base = {c: fit(smoothed(train[c], changes), INVENTORY, A) for c in CLAN_ORDER}
        for m, terms in MODELS.items():
            fitted = {c: fit_model(train[c], changes, terms) for c in CLAN_ORDER}
            for j, b in enumerate(CLAN_ORDER):
                for i, a in enumerate(CLAN_ORDER):
                    Q = fitted[b] if a == b else with_inventory(fitted[a], smoothed(train[b], changes))
                    G[m][rep, i, j] = gain(Q, base[b], test[b])
        for j, b in enumerate(CLAN_ORDER):
            full[rep, j] = gain(smoothed(train[b], changes), base[b], test[b])
    return {m: v.mean(0) for m, v in G.items()}, G["factored"].std(0), full.mean(0)


def bootstrap(pairs, changes, replicates=200, seed=0):
    """Recording-bootstrap intervals for the mean own gain and mean foreign gain of each model.

    Each replicate holds out a fresh third of every clan's recordings and resamples the
    held-out recordings with replacement. Models are refitted on the training recordings,
    which are not resampled: resampling them leaves about a third fewer distinct
    recordings to learn from and pushes every gain down, so the intervals no longer
    surround the estimates. The intervals therefore cover which recordings are held out
    and scored, not sampling of the training set.
    Returns {model: {"own": [...], "foreign": [...], "helped": [...]}} over replicates.
    """
    R, T = shape_of(pairs)
    n = len(CLAN_ORDER)
    off = ~np.eye(n, dtype=bool)
    per_unit = {}
    for c in CLAN_ORDER:
        by_unit = {}
        for p in pairs[c]:
            by_unit.setdefault(p[0], []).append(p)
        per_unit[c] = [count_table(prs, R, T) for _, prs in sorted(by_unit.items(), key=lambda kv: str(kv[0]))]
    A = allowed(R, T, changes)
    rng = np.random.default_rng(seed)
    out = {m: {"own": [], "foreign": [], "helped": []} for m in MODELS}
    for _ in range(replicates):
        train, test = {}, {}
        for c in CLAN_ORDER:
            order = rng.permutation(len(per_unit[c]))
            cut = max(1, len(order) // 3)
            held, kept = order[:cut], order[cut:]
            test[c] = sum(per_unit[c][i] for i in rng.choice(held, len(held)))
            train[c] = sum(per_unit[c][i] for i in kept)
        base = {c: fit(smoothed(train[c], changes), INVENTORY, A) for c in CLAN_ORDER}
        for m, terms in MODELS.items():
            fitted = {c: fit_model(train[c], changes, terms) for c in CLAN_ORDER}
            G = np.zeros((n, n))
            for j, b in enumerate(CLAN_ORDER):
                if test[b].sum() == 0 or (changes and (test[b] * A).sum() == 0):
                    G[:, j] = np.nan
                    continue
                for i, a in enumerate(CLAN_ORDER):
                    Q = fitted[b] if a == b else with_inventory(fitted[a], smoothed(train[b], changes))
                    G[i, j] = gain(Q, base[b], test[b])
            out[m]["own"].append(np.nanmean(np.diag(G)))
            out[m]["foreign"].append(np.nanmean(G[off]))
            out[m]["helped"].append(int(np.nansum(G[off] > 0)))
    return out


def shared_ordering_null(pairs, sims=5, seed=0):
    """What the analysis reports when every clan truly has the same ordering.

    One factored model is fitted to all clans pooled and put on each clan's own
    inventory. Each clan's recordings are then redrawn from it, keeping every
    recording's number of pairs. Returns simulated datasets in the format of `pairs`.
    """
    R, T = shape_of(pairs)
    tables = {c: count_table(pairs[c], R, T) for c in CLAN_ORDER}
    shared = fit_model(sum(tables.values()), False, MODELS["factored"])
    rng = np.random.default_rng(seed)
    cells = [((r, t), (r2, t2)) for r in range(R) for t in range(T) for r2 in range(R) for t2 in range(T)]
    out = []
    for _ in range(sims):
        sim = {}
        for c in CLAN_ORDER:
            truth = with_inventory(shared, smoothed(tables[c], False)).ravel()
            truth = truth / truth.sum()
            sizes = {}
            for u, _, _ in pairs[c]:
                sizes[u] = sizes.get(u, 0) + 1
            sim[c] = [(u, *cells[i]) for u, k in sizes.items() for i in rng.choice(len(cells), k, p=truth)]
        out.append(sim)
    return out


def ordering_lost(G):
    """Own gain minus the gain from the other clan's ordering, averaged both ways."""
    lost = np.diag(G)[None, :] - G
    return (lost + lost.T) / 2


def ordering_distance(pairs, changes, d=EMB_D):
    """Procrustes distance between clans' ordering, each put on the pooled inventory."""
    R, T = shape_of(pairs)
    k = R * T
    tables = {c: count_table(pairs[c], R, T) for c in CLAN_ORDER}
    pooled = smoothed(sum(tables.values()), changes)
    independent = fit(pooled, INVENTORY, allowed(R, T, changes)).reshape(k, k)
    emb = {}
    for c in CLAN_ORDER:
        M = with_inventory(fit_model(tables[c], changes, MODELS["factored"]), pooled).reshape(k, k)
        S = np.divide(M - independent, np.sqrt(independent), out=np.zeros_like(M), where=independent > 0)
        U, sv, _ = np.linalg.svd(S)
        e = U[:, :d] * np.sqrt(sv[:d])
        emb[c] = e / np.linalg.norm(e)
    n = len(CLAN_ORDER)
    D = np.zeros((n, n))
    for i, a in enumerate(CLAN_ORDER):
        for j, b in enumerate(CLAN_ORDER):
            Rot, _ = orthogonal_procrustes(emb[a], emb[b])
            D[i, j] = np.linalg.norm(emb[a] @ Rot - emb[b])
    return D


def main():
    pairs = get_pairs()
    n = len(CLAN_ORDER)
    off = ~np.eye(n, dtype=bool)
    pacific = [i for i, c in enumerate(CLAN_ORDER) if c != "EC1"]
    J = inventory_divergence(pairs)
    tests, model_rows, pair_rows, boot_rows, null_rows, primary = [], [], [], [], [], None
    simulated = shared_ordering_null(pairs)

    for changes in (True, False):
        scoring = "changes only" if changes else "all pairs"
        by_model, G_sd, full = evaluate(pairs, changes)
        G = by_model["factored"]
        D, L = ordering_distance(pairs, changes), ordering_lost(G)

        def add(name, X, Y, Z=None, keep=None):
            if keep is not None:
                X, Y, Z = _sub(X, keep), _sub(Y, keep), (None if Z is None else _sub(Z, keep))
            m = mantel(X, Y, Z)
            tests.append({"scoring": scoring, "analysis": name, "clans": X.shape[0],
                          **{k: round(v, 6) if isinstance(v, float) else v for k, v in m.items()}})
            return m

        main_test = add("distance vs ordering lost", D, L)
        given = add("distance vs ordering lost | inventory divergence", D, L, J)
        add("distance vs inventory divergence", D, J)
        add("ordering lost vs inventory divergence", L, J)
        add("Pacific only: distance vs ordering lost", D, L, keep=pacific)
        for i, c in enumerate(CLAN_ORDER):
            add(f"without {c}: distance vs ordering lost", D, L, keep=[j for j in range(n) if j != i])

        for m, Gm in by_model.items():
            own, foreign = np.diag(Gm), np.array([Gm[off[:, j], j].mean() for j in range(n)])
            model_rows.append([scoring, m, "own"] + [round(x, 4) for x in own] + [round(own.mean(), 4), ""])
            model_rows.append([scoring, m, "another clan's, mean of seven"] + [round(x, 4) for x in foreign]
                              + [round(Gm[off].mean(), 4), int((Gm[off] > 0).sum())])
        model_rows.append([scoring, "full table", "own"] + [round(x, 4) for x in full] + [round(full.mean(), 4), ""])
        for i in range(n):
            for j in range(n):
                pair_rows.append([scoring, CLAN_ORDER[i], CLAN_ORDER[j], round(G[i, j], 4), round(G_sd[i, j], 4),
                                  round(D[i, j], 4), round(L[i, j], 4), round(J[i, j], 4)])

        print(f"\n{scoring}")
        for m, Gm in by_model.items():
            print(f"  {m:<22} own {np.diag(Gm).mean():+.3f} ({np.diag(Gm).min():+.3f} to {np.diag(Gm).max():+.3f}); "
                  f"another clan's {Gm[off].mean():+.3f}, helps in {(Gm[off] > 0).sum()} of {off.sum()}")
        print(f"  {'full table':<22} own {full.mean():+.3f} ({full.min():+.3f} to {full.max():+.3f})")
        boot = bootstrap(pairs, changes)
        for m, b in boot.items():
            own_b, foreign_b = np.array(b["own"]), np.array(b["foreign"])
            q = lambda v: [round(float(x), 4) for x in np.percentile(v, [2.5, 97.5])]
            boot_rows.append([scoring, m, len(own_b), *q(own_b), *q(foreign_b), *q(own_b - foreign_b),
                              round(float(np.mean(foreign_b < 0)), 4), *np.percentile(b["helped"], [2.5, 97.5]).astype(int)])
            print(f"  {m:<22} 95% intervals: own {q(own_b)}, another clan's {q(foreign_b)}, "
                  f"difference {q(own_b - foreign_b)}")
        null = [evaluate(sim, changes, nrep=5)[0] for sim in simulated]
        for m in MODELS:
            own_n = [np.diag(g[m]).mean() for g in null]
            foreign_n = [g[m][off].mean() for g in null]
            helped_n = [int((g[m][off] > 0).sum()) for g in null]
            null_rows.append([scoring, m, len(null), round(float(np.mean(own_n)), 4), round(float(np.mean(foreign_n)), 4),
                              round(float(min(foreign_n)), 4), round(float(max(foreign_n)), 4), min(helped_n), max(helped_n)])
            print(f"  {m:<22} if ordering were shared: own {np.mean(own_n):+.3f}, another clan's "
                  f"{np.mean(foreign_n):+.3f} ({min(foreign_n):+.3f} to {max(foreign_n):+.3f}), helps in {min(helped_n)}-{max(helped_n)}")
        print(f"  distance vs ordering lost: rho={main_test['rho']:+.3f} p={main_test['p_two_sided']:.4f}; "
              f"given inventory divergence: rho={given['rho']:+.3f} p={given['p_two_sided']:.4f}")
        if changes:
            primary = (D, L, main_test, given)

    OUT.mkdir(exist_ok=True)
    with (OUT / "coda_ordering.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tests[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(tests)
    with (OUT / "coda_ordering_models.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["scoring", "model", "ordering_from"] + CLAN_ORDER + ["mean", "comparisons_helped_of_56"])
        w.writerows(model_rows)
    with (OUT / "coda_ordering_bootstrap.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["scoring", "model", "replicates", "own_lo", "own_hi", "foreign_lo", "foreign_hi",
                    "own_minus_foreign_lo", "own_minus_foreign_hi", "share_of_replicates_foreign_below_zero",
                    "helped_lo", "helped_hi"])
        w.writerows(boot_rows)
    with (OUT / "coda_ordering_shared_null.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["scoring", "model", "simulations", "own_mean", "foreign_mean", "foreign_min", "foreign_max",
                    "helped_min", "helped_max"])
        w.writerows(null_rows)
    with (OUT / "coda_ordering_pairs.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["scoring", "source", "target", "transfer_gain_bits", "transfer_gain_sd_over_splits",
                    "ordering_distance", "ordering_lost_bits", "inventory_js_bits"])
        w.writerows(pair_rows)
    figure(*primary, fname="9_ordering_coda.png", text={
        "headline": "Whole codas: do clans with a more different order of codas predict each other worse?",
        "left": "how different the two clans are in which coda tends to follow which, after setting aside "
                "that they use different codas.",
        "middle": "how much worse a clan's next coda is predicted when the other clan's order is used instead "
                  "of its own. Only pairs where the coda changes are counted.",
        "left_title": "How different is the order of codas?",
        "middle_title": "How much worse than a clan's own order?",
        "middle_scale": "bits per pair of codas (higher = worse; 0 = just as good)",
        "y": "Worse than the clan's own order by\n(bits per pair of codas)",
        "control": "which codas each clan uses",
    })
    print("\nwrote results/coda_ordering.csv, coda_ordering_models.csv, coda_ordering_pairs.csv, figure 9")


if __name__ == "__main__":
    main()

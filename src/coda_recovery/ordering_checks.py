"""Checks on the ordering results: what would they look like with no ordering, or one shared ordering?

Three questions a sceptical reader asks of coda_ordering and the within-clan sweep.

1. Is it order at all? Recordings differ in which codas they contain, so the current
   coda says something about which recording this is, and that alone can beat a
   clan-wide frequency baseline. The control shuffles the codas inside every recording.
   Each recording keeps exactly the codas it had, and any order is destroyed.

2. Would shared ordering look like this? Every recording is redrawn from one ordering
   common to all clans, keeping that recording's own coda counts, with the ordering's
   strength set so that a clan's own gain matches the gain observed in the real data.
   If the real transfer between clans is as good as in these simulations, the data do
   not show that clans differ.

3. Is the distance more than noise? A clan's recordings are split into random halves
   and the Procrustes distance between the two halves is compared with the distances
   between different clans.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .clan_similarity import CLAN_ORDER, get_pairs
from .coda_ordering import (INVENTORY, MODELS, allowed, count_table, evaluate, fit, fit_model,
                            ordering_distance, ordering_embeddings, procrustes, shape_of, smoothed)
from .predictive_info import held_out_gain
from .standardize import ALL_CLANS, clan_frame, token_fn

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results"
FIG = REPO / "figures" / "plain"
ORANGE, INK, MUTED = "#c66f0e", "#222222", "#666666"
NO_ORDER, SHARED = "#d5d5d5", "#b5d3ec"
ROWS = [("tempo→tempo only", "Tempo order only\n(how long a coda lasts)"),
        ("rhythm→rhythm only", "Rhythm order only\n(the pattern of its clicks)"),
        ("both, no cross terms", "Whole coda\n(rhythm and tempo together)")]
SHUFFLES_WITHIN = 200
SHUFFLES_TRANSFER = 40
SIMULATIONS = 40
SPLITS = 20
NREP = 5


def sequences(clan, tempo, token):
    """Each recording as (name, tokens in order, links); links[i] says tokens i and i+1 form a pair.

    Mirrors standardize.pooled_pairs: in the Pacific data a gap in coda number breaks the pair.
    """
    df = clan_frame(clan, tempo=tempo)
    tokfn = token_fn(token)
    numbered = "coda_number" in df.columns
    out = []
    for grp, g in df.sort_values(["grpvar", "order"]).groupby("grpvar"):
        rows = list(g.itertuples())
        links = [not (numbered and (b.coda_number - a.coda_number) > 1) for a, b in zip(rows, rows[1:])]
        out.append((grp, [tokfn(r) for r in rows], links))
    return out


def to_pairs(seqs, rng=None):
    """Adjacent pairs; with rng, the codas of each recording are first shuffled among its positions."""
    out = []
    for grp, tokens, links in seqs:
        if rng is not None:
            tokens = [tokens[i] for i in rng.permutation(len(tokens))]
        out.extend((grp, a, b) for a, b, ok in zip(tokens, tokens[1:], links) if ok)
    return out


def within_clan_shuffle(shuffles=SHUFFLES_WITHIN, seed=0):
    """The within-clan sweep's gains against the same gains after shuffling inside recordings."""
    rng = np.random.default_rng(seed)
    rows = []
    for clan in ALL_CLANS:
        for token in ("tempo", "rhythm", "joint"):
            seqs = sequences(clan, "qcut", token)
            (total, _, _), (changes, _, _), _, _ = held_out_gain(to_pairs(seqs), n_boot=0)
            null = np.array([[g[0][0], g[1][0]] for g in
                             (held_out_gain(to_pairs(seqs, rng), n_boot=0) for _ in range(shuffles))])
            for k, (scoring, observed) in enumerate((("all pairs", total), ("changes only", changes))):
                v = null[:, k][np.isfinite(null[:, k])]
                rows.append({"clan": clan, "token": token, "scoring": scoring, "observed": round(observed, 4),
                             "shuffled_mean": round(float(v.mean()), 4),
                             "shuffled_97.5": round(float(np.percentile(v, 97.5)), 4),
                             "p": round(float((1 + np.sum(v >= observed)) / (1 + len(v))), 4),
                             "shuffles": len(v)})
    return rows


def summarise(by_model):
    """Mean own gain, mean foreign gain, their difference and the number of comparisons helped."""
    n = len(CLAN_ORDER)
    off = ~np.eye(n, dtype=bool)
    return {m: {"own": float(np.diag(G).mean()), "foreign": float(G[off].mean()),
                "own_minus_foreign": float(np.diag(G).mean() - G[off].mean()),
                "helped": float((G[off] > 0).sum())} for m, G in by_model.items()}


def shared_kernel(pairs):
    """The ordering of all clans pooled, as cell-wise ratios to the table with no ordering."""
    R, T = shape_of(pairs)
    pooled = sum(count_table(pairs[c], R, T) for c in CLAN_ORDER)
    fitted = fit_model(pooled, False, MODELS["factored"])
    return fitted / fit(smoothed(pooled, False), INVENTORY, allowed(R, T, False))


def simulate_shared(seqs_by_clan, kernel, strength, rng):
    """Redraw every recording from the shared ordering, keeping its own coda counts.

    For each recording the kernel, raised to `strength`, is rescaled to that recording's
    own counts of current and next codas, and the recording's pairs are drawn from the
    result. strength=0 gives no ordering; strength=1 gives the pooled ordering as fitted.
    """
    R, T = kernel.shape[:2]
    K = kernel ** strength
    out = {}
    for clan, seqs in seqs_by_clan.items():
        prs = []
        for grp, tokens, links in seqs:
            real = [(grp, a, b) for a, b, ok in zip(tokens, tokens[1:], links) if ok]
            if not real:
                continue
            N = count_table(real, R, T)
            table = fit(N, INVENTORY, K * (N.sum((2, 3), keepdims=True) > 0) * (N.sum((0, 1), keepdims=True) > 0))
            p = table.ravel() / table.sum()
            for i in rng.choice(p.size, len(real), p=p):
                r, t, r2, t2 = np.unravel_index(i, table.shape)
                prs.append((grp, (int(r), int(t)), (int(r2), int(t2))))
        out[clan] = prs
    return out


def calibrate_strength(seqs_by_clan, kernel, target, changes, rng, model="both, no cross terms"):
    """Strength at which simulated clans' own gain matches the observed own gain."""
    grid = [0.25, 0.5, 0.75, 1.0, 1.25]
    gains = [np.mean([summarise(evaluate(simulate_shared(seqs_by_clan, kernel, s, rng), changes, nrep=NREP)[0])[model]["own"]
                      for _ in range(2)]) for s in grid]
    return float(np.interp(target, gains, grid)), dict(zip(grid, [round(float(g), 4) for g in gains]))


def split_half_distance(pairs, changes, splits=SPLITS, seed=0):
    """Procrustes distance between random halves of each clan's recordings."""
    R, T = shape_of(pairs)
    rng = np.random.default_rng(seed)
    tables = {c: count_table(pairs[c], R, T) for c in CLAN_ORDER}
    pooled = smoothed(sum(tables.values()), changes)
    out = {}
    for c in CLAN_ORDER:
        units = sorted({u for u, _, _ in pairs[c]}, key=str)
        ds = []
        for _ in range(splits):
            first = set(rng.permutation(len(units))[:len(units) // 2])
            halves = {"a": count_table([p for p in pairs[c] if units.index(p[0]) in first], R, T),
                      "b": count_table([p for p in pairs[c] if units.index(p[0]) not in first], R, T)}
            emb = ordering_embeddings(halves, pooled, changes)
            ds.append(procrustes(emb["a"], emb["b"]))
        out[c] = ds
    return out


def figure(check_rows, intervals, path=None):
    """Measured transfer between clans, placed between its two reference points.

    intervals[(scoring, model)] is the 95% interval of the measured value. The default
    figure explains itself for a general reader; with `path`, a bare version is written
    there for use with a caption.
    """
    bare = path is not None
    fig, axes = plt.subplots(1, 2, figsize=((11.5, 4.0) if bare else (15.5, 6.4)), sharey=True)
    panels = [("changes only", "Pairs where the coda changes"), ("all pairs", "All pairs, repeats included")]
    for ax, (scoring, title) in zip(axes, panels):
        for y, (model, _) in enumerate(ROWS):
            r = next(x for x in check_rows if x["scoring"] == scoring and x["model"] == model
                     and x["quantity"] == "foreign")
            for lo, hi, colour in ((r["shuffled_lo"], r["shuffled_hi"], NO_ORDER),
                                   (r["shared_lo"], r["shared_hi"], SHARED)):
                ax.barh(y, hi - lo, left=lo, height=0.5, color=colour, zorder=2)
            lo, hi = intervals[(scoring, model)]
            ax.plot([lo, hi], [y, y], color=ORANGE, lw=2.2, solid_capstyle="round", zorder=3)
            ax.plot(r["observed"], y, "D", color=ORANGE, ms=9, markeredgecolor="white", markeredgewidth=1.4, zorder=4)
            if y == 0:
                for x, text, colour, dy in ((np.mean([r["shuffled_lo"], r["shuffled_hi"]]), "no order\nat all", "#7a7a7a", -0.42),
                                            (np.mean([r["shared_lo"], r["shared_hi"]]), "one order shared\nby all clans", "#3f7fb5", -0.42),
                                            (r["observed"], "measured", ORANGE, 0.47)):
                    ax.text(x, y + dy, text, ha="center", va="bottom" if dy < 0 else "top", fontsize=9.5,
                            color=colour, linespacing=1.15)
        ax.set_ylim(len(ROWS) - 0.45, -0.95)
        ax.set_yticks(range(len(ROWS)))
        ax.set_yticklabels([label for _, label in ROWS], fontsize=11)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", colors=MUTED)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.xaxis.grid(True, color="#eeeeee")
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=10)
        ax.set_xlabel("How well another clan's order predicts a clan's next coda\n"
                      "(bits per pair of codas; further right = better)", color=INK)
    if bare:
        fig.subplots_adjust(left=0.2, right=0.985, top=0.9, bottom=0.2, wspace=0.08)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return
    fig.suptitle("How much of a clan's coda order is shared with other clans?",
                 x=0.03, y=0.985, ha="left", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.03, 0.925,
             "A coda is one whale call: a short burst of clicks. Order means which coda tends to follow which.\n"
             "Orange: what was measured when one clan's order was used to predict another clan (line = 95% interval).\n"
             "Grey: what the same test gives when the codas inside every recording are shuffled, so that there is no order at all.\n"
             "Blue: what it gives when all eight clans are simulated with one shared order.\n"
             "If the orange mark sits on the grey bar, clans share nothing. If it sits on the blue bar, they share everything.",
             ha="left", va="top", fontsize=11, color=MUTED, linespacing=1.45)
    fig.subplots_adjust(left=0.2, right=0.985, top=0.66, bottom=0.14, wspace=0.08)
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "10_order_shared_between_clans.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)

    rows = within_clan_shuffle()
    with (OUT / "shuffle_null_within.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for scoring in ("all pairs", "changes only"):
        for token in ("tempo", "rhythm", "joint"):
            sel = [r for r in rows if r["scoring"] == scoring and r["token"] == token]
            print(f"within-clan, {scoring}, {token}: observed beats 97.5% of shuffles in "
                  f"{sum(r['observed'] > r['shuffled_97.5'] for r in sel)} of {len(sel)} clans; "
                  f"mean observed {np.mean([r['observed'] for r in sel]):+.3f}, "
                  f"mean shuffled {np.mean([r['shuffled_mean'] for r in sel]):+.3f}")

    pairs = get_pairs()
    seqs = {c: sequences(c, "global", "joint") for c in CLAN_ORDER}
    assert all(sorted(map(repr, to_pairs(seqs[c]))) == sorted(map(repr, pairs[c])) for c in CLAN_ORDER)
    kernel = shared_kernel(pairs)
    rng = np.random.default_rng(1)
    check_rows, floor_rows = [], []
    for changes in (True, False):
        scoring = "changes only" if changes else "all pairs"
        observed = summarise(evaluate(pairs, changes)[0])
        shuffled = [summarise(evaluate({c: to_pairs(seqs[c], rng) for c in CLAN_ORDER}, changes, nrep=NREP)[0])
                    for _ in range(SHUFFLES_TRANSFER)]
        strength, grid = calibrate_strength(seqs, kernel, observed["both, no cross terms"]["own"], changes, rng)
        shared = [summarise(evaluate(simulate_shared(seqs, kernel, strength, rng), changes, nrep=NREP)[0])
                  for _ in range(SIMULATIONS)]
        print(f"\n{scoring}: shared-ordering strength {strength:.2f} (own gain by strength: {grid})")
        for m in MODELS:
            for q in ("own", "foreign", "own_minus_foreign", "helped"):
                sh = np.array([s[m][q] for s in shuffled])
                sim = np.array([s[m][q] for s in shared])
                obs = observed[m][q]
                check_rows.append({
                    "scoring": scoring, "model": m, "quantity": q, "observed": round(obs, 4),
                    "shuffled_mean": round(float(sh.mean()), 4),
                    "shuffled_lo": round(float(np.percentile(sh, 2.5)), 4),
                    "shuffled_hi": round(float(np.percentile(sh, 97.5)), 4),
                    "share_of_shuffles_at_or_above_observed": round(float(np.mean(sh >= obs)), 4),
                    "shared_mean": round(float(sim.mean()), 4),
                    "shared_lo": round(float(np.percentile(sim, 2.5)), 4),
                    "shared_hi": round(float(np.percentile(sim, 97.5)), 4),
                    "share_of_shared_at_or_below_observed": round(float(np.mean(sim <= obs)), 4),
                    "shared_strength": round(strength, 3), "shuffles": len(sh), "simulations": len(sim)})
            o, f_ = observed[m]["own"], observed[m]["foreign"]
            row = lambda q: next(r for r in check_rows if r["scoring"] == scoring and r["model"] == m and r["quantity"] == q)
            print(f"  {m:<22} own {o:+.3f} (shuffled {row('own')['shuffled_lo']:+.3f} to {row('own')['shuffled_hi']:+.3f}) | "
                  f"another clan's {f_:+.3f} (shuffled {row('foreign')['shuffled_lo']:+.3f} to {row('foreign')['shuffled_hi']:+.3f}; "
                  f"shared ordering {row('foreign')['shared_lo']:+.3f} to {row('foreign')['shared_hi']:+.3f})")

        D = ordering_distance(pairs, changes)
        off = ~np.eye(len(CLAN_ORDER), dtype=bool)
        halves = split_half_distance(pairs, changes)
        for c in CLAN_ORDER:
            floor_rows.append([scoring, c, round(float(np.mean(halves[c])), 4), round(float(np.min(halves[c])), 4),
                               round(float(np.max(halves[c])), 4), len(halves[c])])
        floor_rows.append([scoring, "between different clans", round(float(D[off].mean()), 4),
                           round(float(D[off].min()), 4), round(float(D[off].max()), 4), int(off.sum() // 2)])
        print(f"  Procrustes distance: halves of one clan {np.mean([np.mean(v) for v in halves.values()]):.3f} "
              f"({min(map(np.min, halves.values())):.3f} to {max(map(np.max, halves.values())):.3f}); "
              f"different clans {D[off].mean():.3f} ({D[off].min():.3f} to {D[off].max():.3f})")

    with (OUT / "ordering_checks.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(check_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(check_rows)
    with (OUT / "distance_noise_floor.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["scoring", "comparison", "mean_distance", "min_distance", "max_distance", "n"])
        w.writerows(floor_rows)
    with (OUT / "coda_ordering_bootstrap.csv").open() as f:
        intervals = {(r["scoring"], r["model"]): (float(r["foreign_lo"]), float(r["foreign_hi"]))
                     for r in csv.DictReader(f)}
    figure(check_rows, intervals)
    figure(check_rows, intervals, path=REPO / "paper" / "figure1.png")
    print("\nwrote results/shuffle_null_within.csv, ordering_checks.csv, distance_noise_floor.csv, figure 10")


if __name__ == "__main__":
    main()

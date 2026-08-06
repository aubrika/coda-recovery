"""M3 — split ladder, inter-coda-gap sweep, token-budget curve (spec 6.4, 6.5).

The ladder is the deliverable: recovery accuracy across random -> by_date ->
by_individual -> by_unit, each read against the frequency baseline and the strong
null. Where it collapses to the null is the cross-clan feasibility verdict.

Design notes forced by the deposit:
- Harder rungs (by_individual, by_unit) can only use the speaker/unit-attributed
  subset, so they run at ~1.7 transitions/cell. Expect collapse; that is a
  result, not a bug (spec 6.4).
- gap = CodaNumber gap (no seconds available); swept here (spec 5.1, trap 9.2).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .inventory import load_raw
from .transitions import coda_type_index, adjacent_pairs, row_normalise
from .pipeline import build_split_sets, SPLIT_TYPES
from .recover import (
    qap_recover,
    frequency_rank_baseline,
    accuracy_at_1,
)
from .nulls import shuffle_within_segments

REPO = Path(__file__).resolve().parents[2]
LADDER_CSV = REPO / "results" / "ladder.csv"
GAP_CSV = REPO / "results" / "gap_sweep.csv"
BUDGET_CSV = REPO / "results" / "token_budget.csv"

ALPHA = 1.0
N_SPLITS = 20
N_NULL = 40
QAP_RESTARTS = 25


def _bootstrap_ci(x, reps=5000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    bs = [np.mean(rng.choice(x, len(x), replace=True)) for _ in range(reps)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


@dataclass
class RungResult:
    split_type: str
    qap_mean: float
    qap_std: float
    base_mean: float
    diff_mean: float
    diff_lo: float
    diff_hi: float
    null_mean: float
    null_p95: float
    trans_per_cell: float
    frac_beats_base: float


def run_rung(df, types, split_type, gap=1) -> RungResult:
    qap, base, tpc = [], [], []
    for s in range(N_SPLITS):
        A, B = build_split_sets(df, types, split_type, "pooled", ALPHA, s,
                                max_codanumber_gap=gap)
        r = qap_recover(A.T, B.T, n_restarts=QAP_RESTARTS, seed=s)
        qap.append(accuracy_at_1(r.perm))
        base.append(accuracy_at_1(frequency_rank_baseline(A.C, B.C)))
        tpc.append(0.5 * (A.transitions_per_cell + B.transitions_per_cell))
    qap, base = np.array(qap), np.array(base)
    diff = qap - base
    lo, hi = _bootstrap_ci(diff)

    # Strong null: one distribution per rung (fixed split seed, shuffled data).
    null = []
    for i in range(N_NULL):
        sh = shuffle_within_segments(df, seed=2000 + i)
        nA, nB = build_split_sets(sh, types, split_type, "pooled", ALPHA, 0,
                                  max_codanumber_gap=gap)
        nr = qap_recover(nA.T, nB.T, n_restarts=10, seed=0, refine_2opt=False)
        null.append(accuracy_at_1(nr.perm))
    null = np.array(null)

    return RungResult(
        split_type, float(qap.mean()), float(qap.std()), float(base.mean()),
        float(diff.mean()), lo, hi, float(null.mean()),
        float(np.percentile(null, 95)), float(np.mean(tpc)),
        float((diff > 0).mean()),
    )


def gap_sweep(df, types, gaps=(1, 2, 3, 5), n_seeds=12):
    rows = []
    for g in gaps:
        qap, base, tpc = [], [], []
        for s in range(n_seeds):
            A, B = build_split_sets(df, types, "random", "pooled", ALPHA, s,
                                    max_codanumber_gap=g)
            r = qap_recover(A.T, B.T, n_restarts=20, seed=s)
            qap.append(accuracy_at_1(r.perm))
            base.append(accuracy_at_1(frequency_rank_baseline(A.C, B.C)))
            tpc.append(0.5 * (A.transitions_per_cell + B.transitions_per_cell))
        rows.append({"gap": g, "qap_mean": round(float(np.mean(qap)), 4),
                     "base_mean": round(float(np.mean(base)), 4),
                     "trans_per_cell": round(float(np.mean(tpc)), 3)})
    return rows


def token_budget_curve(df, types, budgets, reps=20):
    """Subsample the pooled adjacent-pair pool to a common budget, random split
    the sampled pairs 50/50, recover; bootstrap. Isolates power vs sample size
    (spec 6.5)."""
    pool = adjacent_pairs(df)  # pooled a_type/b_type pairs
    idx = {t: i for i, t in enumerate(types)}
    n = len(types)
    a = pool["a_type"].map(idx).to_numpy()
    b = pool["b_type"].map(idx).to_numpy()
    N = len(a)
    rows = []
    for B in budgets:
        B = min(B, N)
        qap, base = [], []
        for rep in range(reps):
            rng = np.random.default_rng(10_000 + rep)
            sel = rng.choice(N, B, replace=False)
            half = rng.integers(0, 2, size=B)
            CA = np.zeros((n, n)); CB = np.zeros((n, n))
            for k, s in zip(sel, half):
                (CA if s == 0 else CB)[a[k], b[k]] += 1
            TA, TB = row_normalise(CA, ALPHA), row_normalise(CB, ALPHA)
            r = qap_recover(TA, TB, n_restarts=15, seed=rep)
            qap.append(accuracy_at_1(r.perm))
            base.append(accuracy_at_1(frequency_rank_baseline(CA, CB)))
        qap = np.array(qap)
        lo, hi = _bootstrap_ci(qap)
        rows.append({"budget": B, "qap_mean": round(float(qap.mean()), 4),
                     "qap_lo": round(lo, 4), "qap_hi": round(hi, 4),
                     "base_mean": round(float(np.mean(base)), 4)})
    return rows


def _write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    df = load_raw()
    types = coda_type_index(df)
    print(f"loaded, {len(types)} types\n")

    print("===== M3.1 SPLIT LADDER (pooled, alpha=1, gap=1) =====")
    print(f"{'rung':<15}{'QAP':>8}{'base':>8}{'diff':>8}{'CI95':>18}"
          f"{'null':>8}{'t/cell':>8}{'>base':>7}")
    ladder = []
    for st in SPLIT_TYPES:
        r = run_rung(df, types, st)
        ladder.append(r)
        print(f"{st:<15}{r.qap_mean:>8.3f}{r.base_mean:>8.3f}{r.diff_mean:>+8.3f}"
              f"  [{r.diff_lo:+.3f},{r.diff_hi:+.3f}]{r.null_mean:>8.3f}"
              f"{r.trans_per_cell:>8.2f}{r.frac_beats_base:>7.2f}")
    _write_csv(LADDER_CSV, [r.__dict__ for r in ladder], list(ladder[0].__dict__.keys()))

    print("\n===== M3.2 INTER-CODA GAP SWEEP (random split) =====")
    gaps = gap_sweep(df, types)
    for row in gaps:
        print(f"  gap={row['gap']}: QAP={row['qap_mean']} base={row['base_mean']} "
              f"t/cell={row['trans_per_cell']}")
    _write_csv(GAP_CSV, gaps, list(gaps[0].keys()))

    print("\n===== M3.3 TOKEN-BUDGET CURVE (random split) =====")
    budgets = [200, 400, 800, 1600, 3200, 10**9]
    curve = token_budget_curve(df, types, budgets)
    for row in curve:
        print(f"  budget={row['budget']:>5}: QAP={row['qap_mean']} "
              f"[{row['qap_lo']},{row['qap_hi']}] base={row['base_mean']}")
    _write_csv(BUDGET_CSV, curve, list(curve[0].keys()))

    print(f"\nwrote {LADDER_CSV.name}, {GAP_CSV.name}, {BUDGET_CSV.name}")


if __name__ == "__main__":
    main()

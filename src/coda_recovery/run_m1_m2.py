"""M1 acceptance gate + first M2 random split-half (spec Section 7).

M1 acceptance, in order (all must pass before real splits are trusted):
  1. Identity check: recovery of T_A vs T_A returns identity, objective 0.
  2. Strong null runs end to end and produces a distribution.
  3. Frequency baseline implemented and reported.

Then the M2 headline: random split-half, pooled speaker mode (the only mode with
real power on this deposit), QAP vs frequency baseline vs strong null.

Run:  python -m coda_recovery.run_m1_m2
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

from .inventory import load_raw, coda_mask
from .transitions import coda_type_index
from .recover import qap_recover
from .pipeline import build_split_sets, run_experiment, ExperimentResult

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "results.csv"

ALPHA = 1.0          # fixed once, logged, never tuned per split (spec 5.2)
GAP = 1              # CodaNumber-gap default; swept later in M3
SEED = 0


def m1_identity_check(df, types) -> None:
    """T_A vs T_A must recover the identity at objective 0 (plumbing only)."""
    A, _ = build_split_sets(df, types, "random", "pooled", ALPHA, SEED)
    rec = qap_recover(A.T, A.T, n_restarts=20, seed=SEED)
    ident = np.array_equal(rec.perm, np.arange(len(types)))
    print(f"[M1.1] identity check: perm==identity={ident}  objective={rec.objective:.2e}")
    assert ident and rec.objective < 1e-9, "identity check FAILED — plumbing broken"


def append_results(rows: list[ExperimentResult]) -> None:
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].row().keys())
    exists = RESULTS.exists()
    with RESULTS.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r.row())


def main():
    df = load_raw()
    types = coda_type_index(df)
    print(f"loaded {int(coda_mask(df).sum())} codas, {len(types)} types\n")

    # ---- M1 acceptance ----
    m1_identity_check(df, types)

    # ---- M2 headline: random split-half, pooled, multiple seeds ----
    print("\n[M2] random split-half, pooled speaker mode, "
          f"alpha={ALPHA}, gap={GAP}, 5 seeds\n")
    rows = []
    for seed in range(5):
        r = run_experiment(df, types, "random", "pooled", ALPHA, GAP, seed=seed,
                           qap_restarts=30, strong_null_reps=30)
        rows.append(r)
        print(f"  seed {seed}: "
              f"trans/cell A={r.transitions_per_cell_A} B={r.transitions_per_cell_B} | "
              f"QAP acc@1={r.qap_accuracy} (fw={r.qap_freq_weighted_accuracy}) | "
              f"baseline={r.baseline_accuracy} | "
              f"null mean={r.strong_null_accuracy_mean} p95={r.strong_null_accuracy_p95} | "
              f"beats_base={r.beats_baseline} beats_null={r.beats_strong_null}")

    append_results(rows)

    # ---- honest summary ----
    qap = np.array([r.qap_accuracy for r in rows])
    base = np.array([r.baseline_accuracy for r in rows])
    null = np.array([r.strong_null_accuracy_mean for r in rows])
    n = rows[0].n_types
    print("\n===== M2 SUMMARY (random split-half, pooled) =====")
    print(f"  types (n)              : {n}")
    print(f"  QAP accuracy@1         : {qap.mean():.3f} ± {qap.std():.3f}  "
          f"(~{qap.mean()*n:.1f} / {n} types)")
    print(f"  frequency baseline     : {base.mean():.3f} ± {base.std():.3f}  "
          f"(~{base.mean()*n:.1f} / {n})")
    print(f"  strong-null mean acc   : {null.mean():.3f}")
    print(f"  QAP - baseline (the finding): {qap.mean()-base.mean():+.3f}")
    verdict = ("STRUCTURE BEATS FREQUENCY" if qap.mean() > base.mean() + 0.02
               else "NO CLEAR WIN OVER FREQUENCY BASELINE")
    print(f"  VERDICT: {verdict}")
    print(f"\nwrote {RESULTS}")


if __name__ == "__main__":
    main()

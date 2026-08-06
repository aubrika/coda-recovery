# PROGRESS

## M1 — inventory & plumbing ✅
- Fetched Gero et al. 2016 (Dryad ck4h0) — see `data/raw/PROVENANCE.md`. Dryad now
  fronts downloads with an Anubis proof-of-work wall; retrieved via browser.
- Inventory committed (`data/inventory/`). Verdict on required fields:
  - **type label** ✅ `CodaName`, 21 real types (+NOISE).
  - **speaker** ⚠️ `WhaleID`, only **41.3% attributed** (rest are the 0 sentinel).
    Binding constraint on within/between + by-individual arms.
  - **timestamp** ⚠️ **no sub-second time**, only day-level `Date`. Seconds-based
    inter-coda gap (spec 5.1) is not computable; substituted a **CodaNumber gap**
    (global monotonic recording index).
- M1 acceptance: identity check passes (perm==identity, obj 0); strong null runs
  end-to-end; frequency baseline implemented. QAP objective verified vs brute
  force on n≤7 (caught the FAQ inverse-permutation convention).

## M2 — random split-half ✅ (first real number)
Random split, pooled speaker mode, α=1, CodaNumber-gap=1, 24 splits:

| quantity | value |
|---|---|
| QAP accuracy@1 | **0.413 ± 0.206** (~8.7 / 21), range 0.05–0.81 |
| frequency baseline | 0.268 (~5.6 / 21) |
| strong-null mean | ~0.28 |
| **QAP − baseline** | **+0.145, 95% bootstrap CI [+0.042, +0.244]** (excludes 0) |
| splits where QAP ≤ baseline | 29% (incl. collapses to ~0.05) |

**Read:** on the optimistic rung, combinatorial position carries recoverable
signal *beyond* frequency — QAP re-identifies ~3 more types than frequency alone,
and the CI on the gap excludes zero. But it is **fragile**: ~1 split in 3 fails to
beat frequency, exactly as ~2 transitions/cell predicts. Effective structural
resolution ≈ 8–9 of 21 types on average.

## Next (not yet run)
- **M3 split ladder** (by_date → by_individual → by_unit) + inter-coda-gap sweep +
  token-budget bootstrap curve. The harder rungs use only the attributed subset
  (~1.7 transitions/cell) and are expected to collapse toward the null — that
  collapse point *is* the cross-clan feasibility verdict.
- Open design question: whether to also pull the Sharma et al. 2024 deposit for
  better speaker attribution before committing to the individual/unit rungs.
- M4 visualisation + write-up.

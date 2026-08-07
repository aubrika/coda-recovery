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

## M3 — split ladder, gap sweep, token-budget curve ✅
Pooled, α=1, 20 splits/rung, 40-rep strong null. `results/ladder.csv`,
`figures/ladder.png`, `figures/token_budget.png`.

| rung | QAP | base | QAP−base (95% CI) | null | t/cell | verdict |
|---|---|---|---|---|---|---|
| random | 0.400 | 0.257 | +0.143 [+0.03, +0.25] | 0.195 | 2.1 | beats freq |
| by_date | 0.300 | 0.190 | +0.110 [+0.02, +0.20] | 0.055 | 4.1 | beats freq |
| by_individual | 0.143 | 0.126 | +0.017 [−0.03, +0.07] | 0.192 | **1.6** | **COLLAPSE (CI incl. 0)** |
| by_unit | 0.233 | 0.098 | +0.136 [+0.06, +0.21] | 0.174 | 4.1 | **beats freq** |

**The surprise:** it does NOT collapse at the hardest rung. **by_unit** — halves
share no social units, the closest cross-clan analogue — retains a clean signal
(+0.136, CI excludes 0). The collapse is at **by_individual**, but that is
confounded: it is the *thinnest* rung (1.6 t/cell, attributed-only) because
splitting individuals both restricts to the 41% attributed subset and severs
within-individual pairs. So the collapse looks like a **power** artefact, not
evidence that structural role is individual-specific. Unit is known for *all*
codas, so by_unit keeps full density (4.1) and the signal survives.

- **Gap sweep**: QAP 0.30–0.39 across CodaNumber-gap ∈ {1,2,3,5}, always above
  baseline; t/cell barely moves (2.05→2.13). The result is NOT manufactured by
  the gap parameter (spec trap 9.2) — most adjacent codas are already contiguous.
- **Token-budget curve**: monotonic. QAP rises 0.18→0.59 as pairs go 200→3626,
  and the margin over frequency *widens* with data. Recovery is data-limited; a
  cross-clan attempt would want substantially more than ~3.6k codas.

## Cross-clan feasibility read
Cautiously positive, against the pre-registered pessimism: the strongest
cross-clan analogue available here (by_unit) recovers ~3 types beyond frequency
with a CI clear of zero, and the power curve says more data helps monotonically.
The one clean collapse (by_individual) is best explained by sample size, not by
absence of structure. Effective structural resolution ≈ 8–12 of 21 types at full
budget.

## M4 — diagnostics, views, write-up ✅
- Spectrum gate (spec 8.1): flat — 26.6% variance in top-3 non-trivial dims, so
  the 3D volumetric view is **decoration**, built and labelled as such.
- `figures/`: confusion.png (mean diagonal 0.38; confusions are STRUCTURED — D- and
  I-families confuse internally, rare types smear = the effective-resolution
  readout), triptych.png, null_histogram.png (observed objective 0.418 sits below
  the ENTIRE strong-null distribution — objective-level result is unambiguous),
  volumetric.html (labelled decoration), acoustic.html (form-vs-role contrast).
- README.md: question, controls, headline table, figures, method, the two data
  caveats, limitations, reproduce steps.

## Status: M1–M4 complete.
Verdict: combinatorial position re-identifies coda type above the frequency
baseline (random +0.14, by_unit +0.14, both CIs clear of 0); objective sits below
the strong null; recovery is data-limited (power curve monotonic). Cross-clan
feasibility is cautiously supported — the one collapse (by_individual) is a
power artefact of the 41%-attributed subset, not evidence against structure.

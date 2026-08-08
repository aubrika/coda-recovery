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

## Phase 2 — a genuine second system (Pacific clans) ✅
Motivation: re-identifying a correspondence we already hold (same clan, answer =
identity) is only a base case. Hersh et al. 2022 gives 7 Pacific clans (none is
the Caribbean EC1), with a GLOBAL coda-type scheme → cross-clan alignment is
gradeable (truth = identity over shared types) yet non-trivial (clans differ).

- **Within-clan replication (positive control, easy split, top-15 types):**
  mean QAP **0.61** vs baseline 0.48 across all 7 clans (REG 0.91, SH 0.85, …).
  The base-case finding generalizes across clans and to bigger vocabularies.
- **Cross-clan alignment (21 clan pairs, top-20 shared types):** QAP **0.026** ≈
  baseline 0.024 ≈ null 0.032 — **at chance**, even on high-density pairs
  (REG-SH 9 transitions/cell). Does not beat the null.

**Verified not an artefact:** `coda_number` encodes real order (same-type-repeat
3.2–6.2× chance, alongside Gero's 3.4×; shuffling kills it), and the pipeline
recovers strongly within-clan on the easy split. So the cross-clan null is real.

**Finding:** combinatorial role is **clan-specific**. The acoustic type inventory
is shared across clans, but the *sequencing* that identifies a type within its
clan does not transfer — the "what" is global, the "how" is a clan dialect.
Figure: `figures/plain/4_within_vs_across_clans.png`. Data: `hersh.py`,
`run_crossclan.py`, `results/{within_pacific,crossclan}.csv`.

## Phase 2b — airtight test PARTIALLY REFUTES the Phase-2 claim ⚠️
Attempting to make "combinatorial role is clan-specific" airtight (matched type
set K=15, matched token budget T=500, nulls mirrored to each condition's split)
walked the claim back. `run_airtight.py`, `results/airtight.csv`.

| condition | QAP (95% CI) | rank-baseline | null p95 | clears null? |
|---|---|---|---|---|
| within_easy (shared seqs) | 0.451 [0.07, 0.87] | 0.409 | 0.800 | **no** |
| within_hard (disjoint reps, same clan) | 0.182 [0.00, 0.53] | 0.143 | 0.453 | **no** |
| cross (different clans) | 0.032 [0.00, 0.13] | 0.052 | 0.133 | **no** |

Two corrections this forces:
1. **`within_hard` fails its null too.** It differs from `cross` only in the clan
   boundary, and both fail — so the cross-clan collapse is NOT attributable to
   clans specifically. The signal dies at independent repertoires within a clan.
2. **The frequency-RANK baseline was too lenient.** QAP exploits more marginal
   structure than rank-matching, so the shuffle NULL (0.45 here) is the true bar,
   well above the rank baseline (0.14). Earlier "beats baseline/null" wins —
   including the Phase-2 within-clan 0.61 and likely the EC1 headline — were
   inflated by sample-sharing leakage + this lenient baseline.

**What still stands:** cross-clan alignment fails (recovery at chance, below its
own low null) — robust. **What does NOT:** clan-specificity, and the magnitude of
the within-clan positive. Both need the strict-null re-audit below.

## REQUIRED NEXT: strict re-audit
Re-run the ORIGINAL EC1 ladder (and Phase-2 within-clan) with the shuffle null as
the primary bar (not the rank baseline) and disjoint-sample splits, matched
budget. Determine what, if anything, clears the strict null. Treat every earlier
"positive" as provisional until it does. Literature note: the cross-clan
transition question is genuinely NOVEL (nearest: "Rhythm of the Deep" arXiv
2606.16084, single clan; Sharma 2024 within-clan; Hersh 2022 / Rendell & Whitehead
2003 cross-clan but repertoire-only) — but novelty is worth nothing until the
strict re-audit says a signal survives.

## Phase 2c — unified strict-null re-audit: what survives ✅
One protocol for EC1 + 7 Pacific clans (`run_reaudit.py`, `results/reaudit.csv`):
top-15 types, DISJOINT-SESSION split (independent samples, no leakage), PAIRED
real-vs-shuffled test (shuffle = permute type labels within each session; the
paired difference isolates the sequential contribution beyond frequency).
Survival criterion: paired (real − shuffled) bootstrap CI excludes 0.

| clan | real | shuffled | real−shuffled (95% CI) | survives |
|---|---|---|---|---|
| **EC1 (Gero)** | 0.39 | 0.29 | **+0.093 [+0.018, +0.164]** | **YES** |
| PAC:REG | 0.38 | 0.30 | +0.080 [-0.011, +0.167] | no |
| PAC:SH | 0.17 | 0.20 | -0.031 [-0.102, +0.033] | no |
| PAC:FP | 0.07 | 0.08 | -0.016 | no |
| PAC:PALI | 0.20 | 0.20 | +0.004 | no |
| **PAC:PO** | 0.32 | 0.22 | **+0.107 [+0.060, +0.158]** | **YES** |
| PAC:RI | 0.23 | 0.18 | +0.047 [-0.002, +0.098] | no |
| **PAC:SI** | 0.49 | 0.26 | **+0.227 [+0.160, +0.300]** | **YES** |

**Final verdict: 3/8 clans (incl. the original EC1) show a SMALL but reliable
within-clan sequential signal beyond frequency.** The original EC1 finding
SURVIVES — but at +0.093 (~1.4 of 15 types), far below the inflated headline. The
effect is heterogeneous and not density-driven (SI: 1.9 t/cell, strongest;
SH: 5.1 t/cell, none). Cross-clan alignment fails throughout. Earlier large
positives were inflated by the lenient rank baseline + shared-sample splits;
under the strict paired null, only a modest signal remains, in some clans.

## Status: complete through strict re-audit. Honest final picture recorded.
Verdict: combinatorial position re-identifies coda type above the frequency
baseline (random +0.14, by_unit +0.14, both CIs clear of 0); objective sits below
the strong null; recovery is data-limited (power curve monotonic). Cross-clan
feasibility is cautiously supported — the one collapse (by_individual) is a
power artefact of the 41%-attributed subset, not evidence against structure.

## Correction: the factored model is NOT a regression
An earlier framing compared legacy-21-type recovery on the Gero data (pooled,
between-whale, +0.09/+0.52) against factored recovery on Sharma Dataset 2
(single-whale) — two different datasets AND sequence definitions. Apples-to-apples
on the SAME Dataset 2 single-whale data (`compare_codifications.py`,
`results/codification_comparison.csv`): legacy 21-type +0.048 (ns), joint -0.136,
rhythm -0.092, tempo +0.16. Legacy also fails here => the data model didn't cause
the "regression"; the difference was pooled/between-whale vs single-whale. The
(rhythm,tempo) grid is also a FINER partition than the 21 types (types split across
tempo cells), so cell re-identification is a harder question, not a lossy one.
Reinforces T_between (between-whale exchange) as the untested lead.

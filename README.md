# coda-recovery

**Can sperm whale coda *types* be re-identified from their position in the coda
transition graph alone — with the labels hidden — and does that beat simply
matching types by how often they occur?**

Split one clan's coda corpus in half, build a transition structure from each half
independently, anonymise the type labels, and search for the permutation that
best aligns the two graphs. Because both halves come from the same clan (EC-1),
the correct answer is known: the identity. The measurand is how much of it we
recover — the **effective structural resolution** of the coda system.

## Headline

On the Eastern Caribbean clan (Gero et al. 2016), 21 coda types, ~3.9k codas:

| split (halves share…) | QAP acc@1 | frequency baseline | **QAP − baseline (95% CI)** | strong null |
|---|---|---|---|---|
| random *(everything)* | 0.40 | 0.26 | **+0.143 [+0.03, +0.25]** | 0.20 |
| by date | 0.30 | 0.19 | **+0.110 [+0.02, +0.20]** | 0.06 |
| by individual | 0.14 | 0.13 | +0.017 **[−0.03, +0.07]** | 0.19 |
| by social unit | 0.23 | 0.10 | **+0.136 [+0.06, +0.21]** | 0.17 |

**Combinatorial position carries type identity beyond frequency**, and the signal
**survives to the by-unit split** — the closest analogue here to the cross-clan
case (the two halves share no social units). The lone collapse, by-individual, is
confounded with sample size: it is the only rung restricted to the 41%
speaker-attributed subset, running at **1.6 transitions/cell** vs 4.1 elsewhere.
So the collapse reads as *lack of power*, not *absence of structure*.

At the **objective** level the result is unambiguous even where accuracy is noisy:
the recovered `‖P·T_A·Pᵀ − T_B‖_F` sits **below the entire strong-null
distribution** (`figures/null_histogram.png`). Accuracy@1 is harsher than the
objective because many types genuinely share a structural position — which is the
finding, not a failure (see the confusion matrix).

## The controls (this is where a spurious result would come from)

- **Frequency baseline** (the one that matters): match types by marginal-frequency
  rank, using *no* structural information. Reported beside every number. The claim
  is always "QAP recovered k where frequency recovered j," never "QAP recovered k."
- **Strong null**: shuffle coda order *within segments* (preserving composition,
  length, marginals, sparsity, sample size), rebuild everything, rerun the whole
  pipeline. Isolates sequential structure from frequency/shape.
- **Random-permutation null**: weak floor.
- **Gap sweep**: the CodaNumber-gap parameter ∈ {1,2,3,5} does not move the result
  (`results/gap_sweep.csv`) — it is not manufactured by that knob.

## Figures

**For a general reader (`figures/plain/`)** — plain language, no jargon, one
consistent color language (blue = using the sequence patterns, orange = guessing
by how common each call is, grey dashed = pure luck):
- `1_main_result.png` — patterns beat guessing across four increasingly strict
  tests, counted as "call types correctly identified out of 21."
- `2_more_data_helps.png` — the power curve: more calls analyzed → better
  identification; guessing barely moves.
- `3_easy_vs_hard_calls.png` — per-call reliability (replaces the confusion
  heatmap): which of the 21 calls are reliably identified vs. easily confused.

**Technical / methods (`figures/`)** — jargon retained for a specialist reader:

- `ladder.png` — accuracy across the four splits, baseline + null as references.
- `token_budget.png` — power curve: QAP rises 0.18→0.59 as pairs go 200→3.6k and
  the margin over frequency *widens*; recovery is data-limited.
- `confusion.png` — which types get swapped with which over 60 splits. Confusions
  are **structured**: the two dominant types swap as a block, the D-family and
  I-family each confuse internally, rare types smear. This is the effective
  structural resolution: ~5–8 types reliably placed.
- `null_histogram.png` — observed objective vs both nulls.
- `triptych.png` — `T_A`, `T_B`, `P·T_A·Pᵀ` heatmaps.
- `volumetric.html` — 3D structural embedding. **Decoration, labelled as such**:
  the spectrum is flat (26.6% variance in 3 dims), so proximity is only weakly
  meaningful (spec §8.1 gate).
- `acoustic.html` — types in (clicks, duration, rhythm) space coloured by
  structural position: does acoustic form entangle with combinatorial role?

## Method (the primary arm is QAP, not Procrustes)

A relabelling permutes rows *and* columns of the transition matrix simultaneously,
so this is **graph matching**, solved with `scipy.optimize.quadratic_assignment`
(FAQ + 2opt, many restarts). The QAP objective is verified against brute force on
n≤7 in the tests — this caught a real sign/inverse-permutation convention bug (the
naive `(T_A, T_B)` call silently optimises σ⁻¹; the correct call is
`(T_B, T_A, maximize=True)`). A secondary spectral-Procrustes arm is included as
the MUSE analogue but is an **approximate** optimiser: unsupervised
embedding-matching gets trapped in local minima even on clean synthetic spectra —
which is precisely the spec's reason QAP is primary. It is read against QAP, never
as ground truth.

## Data & the two caveats it forced (`data/inventory/`)

Gero, Whitehead & Rendell 2016, Dryad `doi:10.5061/dryad.ck4h0` (CC0). An
inventory script audits the fields *before* any analysis (`data/raw/PROVENANCE.md`
records retrieval — Dryad now fronts downloads with an Anubis proof-of-work wall).

1. **No sub-second timestamp** — only day-level dates. The spec's seconds-based
   inter-coda gap is not computable; ordering comes from the global monotonic
   `CodaNumber`, and the gap parameter is a **CodaNumber gap** instead.
2. **41% speaker attribution** — the rest are the `WhaleID==0` sentinel. This caps
   the within/between-speaker and by-individual arms to a thin attributed subset.

## Limitations — what this does *not* show

- **Not a cross-clan result.** by-unit is the closest analogue, but units within a
  clan still share dialect; two clans share neither individuals nor dialect. This
  establishes feasibility and a power requirement, not success.
- **Underpowered.** ~2–4 transitions/cell against 441 cells; the power curve says a
  cross-clan attempt wants substantially more than ~3.6k codas.
- **No claim about meaning.** This is re-identification of type by structural role,
  nothing about semantics, translation, or a "dictionary."
- **The ceiling is real.** Rare types occupy near-identical structural positions
  and are unidentifiable in principle. That ceiling is the measurand.

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
export PYTHONPATH=src
python -m coda_recovery.inventory     # M1: fetch-audit (data already committed)
python -m coda_recovery.run_m1_m2     # M1 acceptance + M2 random split-half
python -m coda_recovery.run_m3        # M3 ladder + gap sweep + token budget
python -m coda_recovery.figures       # ladder + token-budget PNGs
python -m coda_recovery.m4            # confusion / triptych / null-hist / HTML views
pytest                                # QAP-vs-bruteforce + procrustes + controls
```

Results append to `results/`; provenance and inventory are committed for audit.
(Code is ~1.5k lines, a little over the spec's ~1.2k target — the M4 diagnostics
and two interactive HTML views account for the overrun.)

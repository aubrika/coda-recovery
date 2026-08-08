# coda-recovery

**Can sperm whale coda *types* be re-identified from their position in the coda
transition graph alone — with the labels hidden — and does that beat simply
matching types by how often they occur?**

Split one clan's coda corpus in half, build a transition structure from each half
independently, anonymise the type labels, and search for the permutation that
best aligns the two graphs. Because both halves come from the same clan (EC-1),
the correct answer is known: the identity. The measurand is how much of it we
recover — the **effective structural resolution** of the coda system.

> **Plain-language summary: [`SUMMARY.md`](SUMMARY.md).**

## Headline (after a strict re-audit)

The decisive test is the **paired real-vs-shuffled** comparison under a strict
null (`run_reaudit.py`): split each clan's recordings into disjoint-session
halves, top-15 types, and compare recovery on the **real** order against the
**same codas with order scrambled within each session** (frequencies preserved,
only sequence destroyed). The difference isolates what *order* contributes beyond
frequency. A clan's signal survives iff that paired difference's 95% CI clears 0.

| clan | real | shuffled | **real − shuffled (95% CI), of 15 types** | survives |
|---|---|---|---|---|
| **Caribbean EC1 (Gero)** | 0.39 | 0.29 | **+1.4 [+0.3, +2.5]** | **yes** |
| Pacific PO | 0.32 | 0.22 | **+1.6 [+0.9, +2.4]** | **yes** |
| Pacific SI | 0.49 | 0.26 | **+3.4 [+2.4, +4.5]** | **yes** |
| Pacific REG | 0.38 | 0.30 | +1.2 [−0.2, +2.5] | no |
| Pacific RI | 0.23 | 0.18 | +0.7 [0.0, +1.5] | no |
| Pacific SH / FP / PALI | — | — | ≈ 0 | no |

**A small but real within-clan sequential signal — about 1–3 of 15 types beyond
frequency — survives in 3 of 8 clans (including the original EC1), is marginal in
2, and absent in 3.** It is not driven by sample size (SI has the least data, the
largest effect). **Cross-clan alignment fails throughout** (`run_crossclan.py`):
the sequencing that helps within a clan does not transfer to another clan.

### What this corrects
Earlier versions of this README reported much larger effects (e.g. EC1 "+0.14
over frequency", Pacific within-clan "0.61"). Those were **inflated** by two
things the re-audit fixed: (1) grading against the frequency-**rank** baseline,
which is too lenient — QAP exploits more marginal structure than rank-matching, so
the **shuffle null** is the true bar; and (2) split-halves that shared sequences.
Under the strict paired null on independent samples, only the modest signal above
remains. The exploratory ladder/figures (`figures/plain/1–3`, `figures/*.png`)
use the lenient baseline and **overstate** the effect — kept for the record, but
superseded by the re-audit.

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

**The honest result (`figures/plain/`)** — plain language, colorblind-safe:
- `4_does_order_help.png` — **the headline.** Per clan, extra calls (of 15)
  identifiable from sequence order alone, with 95% CI; blue = clears zero.
- `5_real_vs_scrambled.png` — real order vs the order-scrambled control per clan;
  where the bars nearly tie, order adds nothing.
- `6_repetition_vs_syntax.png` — **the syntax cut.** Per clan, the full effect
  (with self-repetition) vs genuine syntax (self-repetition removed): EC1's signal
  jumps once repetition is removed (it was *hiding* the syntax), Pacific PO's
  collapses (it *was* repetition). Data: `syntax.py` → `results/syntax.csv`.
- `7_which_axis.png` — **the factored-model result.** Splitting a coda into rhythm
  (click pattern) and tempo (duration), only *tempo* carries a sequential signal —
  consistent with the paper's "rubato" duration drift. `recover_factored.py` →
  `results/factored_recovery.csv`.
- `8_clan_axis_grid.png` — **which dial carries re-identifiable order, per clan**
  (8 clans × tempo/rhythm/joint). Tempo is most reproducible (4/8), but the
  biggest clan REG uses rhythm/joint. `factored_by_clan.py` →
  `results/factored_by_clan.csv`.
- `9_predictive_information.png` — **the clean result (supersedes the QAP framing).**
  Cross-validated bits the current (rhythm,tempo) token carries about the next —
  all reliably positive, even with repeats removed. `predictive_info.py` →
  `results/predictive_info.csv`.
- `10_clan_cross_prediction.png` / `11_clan_procrustes.png` — **cross-clan grammar
- `12_expressive_features.png` — **additive check:** do ornament/rubato add predictive info on top of (rhythm,tempo)? Barely — only rubato's own weak self-structure. `expressive.py` → `results/expressive.csv`.
  comparison** (the right use of alignment): one clan's sequence model predicts
  another clan's next coda *worse than that clan's own base rates* (negative
  transfer), and clan transition-geometries are all distinct. Grammars are
  clan-specific. `clan_similarity.py` → `results/clan_similarity.csv`.

**Exploratory, lenient-baseline (superseded — overstate the effect):**
- `1_main_result.png`, `2_more_data_helps.png`, `3_easy_vs_hard_calls.png` — the
  EC1 ladder graded against the frequency-rank baseline. Kept for the record.

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

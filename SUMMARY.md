# Methods and results

This analysis asks whether a first-order sequence model predicts adjacent coda
tokens better than a frequency model, within and between the sampled vocal clans.
Results below were regenerated on 2026-09-26.

## Data and representation

The main analysis uses Caribbean EC1 data from Sharma et al. (2024), Dataset 2,
and seven Pacific clans from Hersh et al. (2022). Input files and digests are
listed in [data/sources.json](data/sources.json); acquisition details are in
[data/raw/PROVENANCE.md](data/raw/PROVENANCE.md).

Rhythm is assigned to the nearest EC1 template of the same click count, using
normalized cumulative inter-click intervals. Duration has two representations:

- Within-clan sweep: five per-clan quantile bins.
- Cross-clan comparisons: fixed EC1 duration edges, shared across clans.

These are different analysis frames. Their tempo scores should not be compared
as though the tokens were identical. Bins, templates, and vocabulary are fixed
before cross-validation; intervals are conditional on this representation.

Pairs join adjacent codas within a recording, pooling speakers. EC1 uses onset
order. Pacific data use coda numbers and reject gaps greater than one after
filtering. These rules do not identify conversational turns. The EC1 supplement
uses known speakers and an eight-second onset-gap limit.

## Score and baseline

The score is the average held-out log-likelihood gain:

```text
gain = mean(log2 P_sequence(next | current) - log2 P_baseline(next | current))
```

Positive values favor the sequence model; negative values favor the baseline.
This is a fitted-model prediction score, not an exact mutual-information estimate.
Its units are bits per scored pair.

For all-pair scoring, the baseline is the smoothed destination frequency in the
training recordings. The sequence model is a smoothed bigram, with alpha = 0.5.

For changes-only scoring, only pairs with different source and destination tokens
are evaluated. Both models assign zero probability to the excluded destination.
The bigram is normalized over its off-diagonal row. The baseline is estimated
from **all** training destinations, then conditioned on a change:

```text
P_baseline(b | a, b != a) = (n_b + alpha) / (N - n_a + alpha * (V - 1))
```

Here n_b counts destination b, N counts all training pairs, and V is vocabulary
size. This baseline represents draws from the training destination frequencies
subject to the known exclusion. It does not remove every possible effect of
repetition, recording context, or speaker composition.

## Correction to the earlier analysis

The earlier changes-only analysis filtered training and test pairs, but retained
an unconditional frequency baseline. That baseline spent probability on an outcome
excluded by construction, giving the bigram an artificial advantage.

For independent uniform five-token data, conditioning on a change leaves four
possible destinations. The old comparison could approach log2(5/4), about
0.322 bits, without any original sequence dependence. The regression test now
returns zero on balanced independent data, and checks nonuniform data too.

The previous uncertainty calculation resampled overlapping split scores.
It has been replaced with the recording bootstrap described below. Because both
the estimator and uncertainty method changed, new results supersede the previous
CSVs and figures. The previous universal-tempo and all-clans changes-only claims
are withdrawn.

## Cross-validation and uncertainty

Recordings are assigned to five disjoint folds using seed 0 (fewer folds if fewer
than five recordings exist). Each pair is scored once, using models fitted on the
other folds. The overall estimate is weighted by the number of scored pairs,
rather than giving a small fold the same weight as a large one.

For each of 500 bootstrap replicates, recordings are sampled with replacement
within each fixed fold. All pairs belonging to a sampled recording are retained;
duplicate copies remain in that fold. Both models are refitted on every replicate.
The 2.5th and 97.5th percentiles form the reported intervals.

This estimates recording-sampling uncertainty conditional on the folds and tokens.
It assumes recordings are independent sampling units, which cannot be established
from the available whale identities. It does not include uncertainty in template
selection, bin edges, or study design. With few recordings, the tails are unstable.
Intervals are exploratory and are not adjusted for multiple comparisons.

## Within-clan results

The [sweep CSV](results/predictive_info_sweep.csv) includes estimates, interval
endpoints, numbers of pairs and recordings, and bootstrap settings.

| Token | All-pair point-estimate range | Changes-only point-estimate range |
|---|---:|---:|
| Tempo | +0.154 to +0.861 | +0.034 to +0.638 |
| Rhythm | +0.069 to +0.783 | -0.032 to +0.279 |
| Joint rhythm/tempo | +0.154 to +0.965 | -0.104 to +0.593 |

All-pair tempo intervals are above zero in all eight clans. Rhythm's all-pair
interval crosses zero for PO. Changes-only rhythm intervals have no positive
lower bounds; tempo intervals cross zero in several clans. PALI's tempo lower
bound is close to zero and should not carry a strong interpretation.

![Changes-only estimates](figures/plain/2_current_predicts_next.png)

## Transfer between clans

The leave-one-clan-out bigram is fitted on seven clans. For each fold of the
eighth clan, its baseline is fitted on the remaining target-clan recordings.
The foreign bigram never trains on the target clan. Both distributions condition
on a change, and scores are weighted by changed pairs.

| Token | Positive transfer estimates | Mean transfer gain |
|---|---:|---:|
| Tempo | 3 / 8 | -0.111 |
| Rhythm | 0 / 8 | -0.684 |
| Joint rhythm/tempo | 0 / 8 | -1.365 |

These are descriptive point estimates, without transfer confidence intervals.
They do not establish that clans share no structure: sparse counts, unequal
training sizes, tokenization, and distribution shift can all reduce transfer.

![Within-clan and transferred models](figures/plain/3_shared_vs_clan_specific.png)

The [pairwise comparison](results/clan_similarity.csv) is a separate all-pair
analysis, retaining its 15 repeated recording splits. Its off-diagonal models
perform worse than the target-clan frequency baseline in this dataset. This
comparison mixes inventory and transition differences.

The Procrustes figure compares five-dimensional PMI embeddings on the 15 most
frequent pooled joint tokens, including smoothed cells for absent tokens.
Distances describe fitted embeddings; a nonzero distance is not a significance
test or proof of a distinct grammar.

## Procrustes distance and lost predictability

`drift` asks whether pairs of clans that sit further apart in Procrustes distance
also predict each other worse. Predictability lost is the pairwise cross-prediction
score above, averaged over both directions and sign-flipped, in bits per coda.

Each clan appears in seven of the 28 pairs, so the pairs are not independent.
Significance comes from a Mantel test on the Spearman correlation: clan labels are
permuted on one matrix and the correlation recomputed. All 40,320 relabellings of
eight clans are enumerated, so p-values are exact. They are two-sided and not
adjusted for the number of analyses.

| Analysis | Clans | Spearman ρ | p |
|---|---:|---:|---:|
| Distance vs predictability lost | 8 | +0.47 | 0.007 |
| Distance vs inventory divergence | 8 | +0.58 | 0.0006 |
| Predictability lost vs inventory divergence | 8 | +0.86 | 0.00002 |
| Distance vs predictability lost, given inventory divergence | 8 | -0.06 | 0.77 |
| Pacific clans only: distance vs predictability lost | 7 | +0.38 | 0.11 |
| Pacific clans only, given inventory divergence | 7 | -0.00 | 0.99 |

Inventory divergence is the Jensen-Shannon divergence between two clans' token
frequencies. The partial correlation removes its linear fit from both rank vectors.

Distance and lost predictability are associated, but inventory divergence explains
the association. This is expected of the cross-prediction score as built: a foreign
bigram scores a context it never saw as a uniform guess, so a clan with unfamiliar
tokens is predicted badly whatever its ordering. The embedding is affected too,
through smoothed cells for tokens a clan does not use.

Sensitivity, all in [drift.csv](results/drift.csv):

- Leaving out any one clan keeps the unadjusted correlation positive, from +0.35 to +0.65.
- It depends on the embedding. With five or eight dimensions it ranges from +0.47 to
  +0.80 across 10, 15 and 25 tokens. With three dimensions it ranges from -0.02 to +0.33.

Neither measure, as built here, separates ordering from inventory. The next
section rebuilds both so that it can.

![Distance and lost predictability](figures/plain/6_distance_vs_predictability.png)

## Ordering with inventory taken out

`ordering_drift` repeats the comparison with both measures rebuilt so that coda
frequencies cannot drive them. It was checked on synthetic sequences before use: a source with the same ordering but very
different frequencies transfers over 90% of the gain, and a source with no ordering
transfers none.

**Tokens.** Tempo and rhythm are analysed separately, each on the tokens with at
least 20 codas in every clan: four of the five duration bins, and seven of the 18
rhythm classes. Pairs touching any other token are dropped. The combined token is
not analysed, because none reaches 20 codas in all eight clans.

**Carrying ordering over.** A transition table has margins (how common each token
is) and odds ratios (how it departs from what the margins alone would give). To
predict clan B from clan A, A's smoothed table is rescaled by iterative
proportional fitting until its margins equal those of B's training recordings.
This keeps A's odds ratios and takes every frequency from B. The gain is scored on
B's held-out recordings against the table with B's margins and no association. For
changes-only scoring the diagonal is a structural zero in both tables. Recordings
are split as in the pairwise comparison: a third held out, 15 times.

**Ordering lost** for a pair is each clan's own gain minus the gain from the other
clan's ordering, averaged over both directions. **Distance** is the Procrustes
distance between PMI embeddings on the same shared tokens.

Changes-only scoring is treated as the primary analysis, because every clan repeats
codas. That choice was made before these results were seen, but it was not
registered anywhere, and the analysis as a whole followed two earlier attempts.

| Feature | Scoring | Own gain, mean (range) | Foreign ordering helps | Foreign gain, mean |
|---|---|---:|---:|---:|
| Tempo | changes only | +0.10 (-0.01 to +0.36) | 42 of 56 | +0.07 |
| Tempo | all pairs | +0.28 (+0.07 to +0.56) | 53 of 56 | +0.21 |
| Rhythm | changes only | -0.02 (-0.06 to +0.07) | 3 of 56 | -0.12 |
| Rhythm | all pairs | +0.29 (-0.06 to +0.65) | 42 of 56 | +0.11 |

For tempo changes, the gain depends on the clan being predicted and very little on
the clan supplying the ordering. Among the five clans whose own gain exceeds 0.05
bits, another clan's ordering keeps 67% to 98% of it on average. For rhythm
changes, clans' own gains on the shared classes are near zero, so transfer cannot
be assessed.

| Feature | Scoring | Distance vs ordering lost, ρ | p | Given token frequencies, ρ | p |
|---|---|---:|---:|---:|---:|
| Tempo | changes only | +0.00 | 1.00 | +0.19 | 0.38 |
| Tempo | all pairs | +0.52 | 0.044 | +0.64 | 0.009 |
| Rhythm | changes only | +0.25 | 0.15 | -0.03 | 0.87 |
| Rhythm | all pairs | +0.40 | 0.11 | +0.37 | 0.16 |

p-values are two-sided exact Mantel tests, unadjusted. The planned comparisons, on
changes only, show no relationship. Tempo with repeats included does, and it
strengthens when token frequencies are accounted for and when the Caribbean clan is
left out (ρ = +0.67). It is one of four comparisons and was not the planned one, so
it is a lead to follow up, not a result.

Limits: transfer gains are point estimates without intervals. Duration bins are
ordered, so successive codas of similar length fall in neighbouring bins in any
clan; some shared tempo ordering may reflect duration changing smoothly. The shared
token sets cover between 59% and 100% of a clan's tempo codas and between 29% and
92% of its rhythm codas, so the Caribbean clan's rhythm is thinly represented.
All of it is in [ordering_drift.csv](results/ordering_drift.csv),
[ordering_transfer.csv](results/ordering_transfer.csv) and
[ordering_drift_pairs.csv](results/ordering_drift_pairs.csv).

![Tempo ordering](figures/plain/7_ordering_tempo.png)

## Whole codas, with inventory taken out

The single-feature analysis cannot say how codas are ordered, because a coda is a
rhythm and a tempo together and clans share too few whole coda types to compare
their transition tables. `coda_ordering` describes each clan's ordering with a
factored model instead. Changes-only scoring is again the primary analysis.

**Model.** Transitions are counted in a four-way table: current rhythm and tempo,
next rhythm and tempo. A log-linear model is fitted by iterative proportional
fitting to six of its margins. Two are inventory: how common each coda type is as
the current coda and as the next. Four are ordering: rhythm to rhythm, tempo to
tempo, rhythm to next tempo, and tempo to next rhythm. Counts carry a uniform prior
worth 0.5 pseudo-pairs per rhythm-to-rhythm cell. Under changes-only scoring a
repeat of the same coda is a structural zero.

**Carrying ordering over.** To predict clan B from clan A, A's fitted table is
rescaled to B's two inventory margins. This keeps every odds ratio between current
and next coda from A and takes every coda frequency from B. The gain is scored on
B's held-out recordings (a third held out, 15 times) against the table with B's
inventory and no dependence of next on current. With plentiful data, an
ordering that says nothing scores zero and one that is confidently different scores
below zero. At the sample sizes here, estimation noise alone also scores below zero,
so results are read against the reference points described further down.

**Checks on synthetic data**, in the test suite: a clan with the same ordering on a
different inventory transfers over 90% of the gain; a clan with no ordering
transfers none; unrelated orderings score below zero on average; cross terms are
detected when present and not otherwise. These use tens of thousands of pairs on a
small token set, far more data per cell than any real clan has.

Changes only, mean over clans, bits per changed pair:

| Model | Own gain | 95% interval | Another clan's | 95% interval | Helps in |
|---|---:|---:|---:|---:|---:|
| Tempo to tempo only | +0.17 | +0.10 to +0.24 | +0.09 | +0.02 to +0.14 | 45 of 56 |
| Rhythm to rhythm only | +0.10 | -0.03 to +0.17 | -0.13 | -0.20 to -0.09 | 8 of 56 |
| Both, no cross terms | +0.22 | +0.07 to +0.31 | -0.05 | -0.16 to +0.02 | 21 of 56 |
| Factored (all four) | +0.21 | +0.04 to +0.32 | -0.15 | -0.24 to -0.07 | 8 of 56 |
| Full table, not factored | -0.42 | | | | |

All pairs, repeats included:

| Model | Own gain | 95% interval | Another clan's | 95% interval | Helps in |
|---|---:|---:|---:|---:|---:|
| Tempo to tempo only | +0.34 | +0.25 to +0.41 | +0.26 | +0.16 to +0.33 | 55 of 56 |
| Rhythm to rhythm only | +0.39 | +0.22 to +0.45 | +0.18 | +0.04 to +0.25 | 50 of 56 |
| Both, no cross terms | +0.58 | +0.39 to +0.68 | +0.32 | +0.15 to +0.43 | 52 of 56 |
| Factored (all four) | +0.59 | +0.41 to +0.70 | +0.24 | +0.07 to +0.34 | 46 of 56 |
| Full table, not factored | +0.17 | | | | |

Reading the tables:

- The unfactored table over whole coda types is too sparse to estimate, and scores
  below frequencies alone on changes. The factored model is what makes the question
  answerable.
- Cross terms do not raise a clan's own gain, and they make transfer worse. The model
  with rhythm-to-rhythm and tempo-to-tempo terms only ("both, no cross terms") is
  therefore the one reported as "whole coda" in the README.
- Zero is not the reference for "another clan's" gain. A table estimated from limited
  data is partly noise, and noise carried to another clan costs bits. The reference
  points are in the next section.

**Intervals.** 200 replicates. Each holds out a fresh third of every clan's
recordings and resamples the held-out recordings with replacement; models are
refitted on the training recordings. A first version also resampled the training
recordings. That leaves about a third fewer distinct recordings to learn from and
lowers every gain, and its intervals did not contain the estimates, so it was
replaced after it had been run. The intervals reported here therefore cover which
recordings are held out and scored, not sampling of the training set. The
within-clan sweep earlier in this document still resamples every fold, so its
intervals are conservative and are not comparable with these.

## Reference points: no order, and one shared order

`ordering_checks` runs the same analysis on data where the answer is known.

**No order.** The codas inside every recording are shuffled among that recording's
positions. Each recording keeps exactly the codas it had, links broken by gaps stay
broken, and any order is destroyed. This separates order from differences between
recordings in which codas they contain.

Within-clan sweep, 200 shuffles per clan. A clan counts when its observed gain is
above the 97.5th percentile of its shuffles:

| Token | Scoring | Clans above their shuffles | Mean observed | Mean shuffled |
|---|---|---:|---:|---:|
| Tempo | all pairs | 8 of 8 | +0.36 | +0.12 |
| Rhythm | all pairs | 8 of 8 | +0.35 | +0.05 |
| Joint | all pairs | 8 of 8 | +0.49 | -0.04 |
| Tempo | changes only | 8 of 8 | +0.19 | +0.07 |
| Rhythm | changes only | 6 of 8 | +0.09 | -0.02 |
| Joint | changes only | 8 of 8 | +0.12 | -0.14 |

So the gains are not produced by recording composition alone, but about a third of
the tempo gain is: it survives shuffling. Rhythm on changes fails in FP and PO.

**One shared order.** A factored model is fitted to all clans pooled, and its
ordering is kept as cell-wise ratios to the table with no ordering. Every recording
is then redrawn: the ratios, raised to a power, are rescaled to that recording's own
counts of current and next codas, and the recording's pairs are drawn from the
result. The power is chosen so that the mean own gain of the simulated clans equals
the observed one (0.44 for changes, 0.42 for all pairs). The simulated clans
therefore have the real inventories, the real recording sizes and compositions, an
ordering of realistic strength, and no difference between clans.

Transfer between clans, mean over the 56 clan-to-clan comparisons, bits per pair.
40 shuffles and 40 simulations, each scored with 5 splits; ranges are the central
95%:

| Scoring | Model | No order | Observed | One shared order | Position |
|---|---|---:|---:|---:|---:|
| Changes only | Tempo to tempo | +0.00 to +0.02 | +0.09 | +0.09 to +0.12 | 0.78 |
| Changes only | Rhythm to rhythm | -0.20 to -0.16 | -0.13 | -0.08 to -0.04 | 0.40 |
| Changes only | Both, no cross terms | -0.18 to -0.15 | -0.05 | +0.02 to +0.06 | 0.53 |
| Changes only | Factored (all four) | -0.29 to -0.24 | -0.15 | -0.07 to -0.03 | 0.55 |
| All pairs | Tempo to tempo | +0.04 to +0.06 | +0.26 | +0.26 to +0.30 | 0.93 |
| All pairs | Rhythm to rhythm | -0.13 to -0.08 | +0.18 | +0.21 to +0.26 | 0.85 |
| All pairs | Both, no cross terms | -0.11 to -0.06 | +0.32 | +0.36 to +0.41 | 0.86 |
| All pairs | Factored (all four) | -0.22 to -0.16 | +0.24 | +0.29 to +0.35 | 0.84 |

"Position" is (observed - mean with no order) / (mean with one shared order - mean
with no order): 0 means clans share nothing, 1 means they share everything. In every
row the observed value is above all 40 shuffles and below all 40 shared-order
simulations.

What can and cannot be said:

- Another clan's ordering carries information about a clan. The negative sign of
  some transfer gains is the cost of estimation noise, not evidence of misleading
  structure.
- Transfer falls short of what one shared ordering would give, most for rhythm.
- The held-out bootstrap intervals of the observed values are wide. For "both, no
  cross terms" on changes the interval is -0.16 to +0.02, which nearly reaches both
  reference ranges. The position figures are point estimates and should be read as
  rough.
- The shared-order simulation gives every clan the same ordering strength. Real
  clans differ, which this does not capture.

**Distance.** Each clan's fitted table is rescaled to one pooled inventory, so that
tables differ only in ordering. Standardized residuals from independence are
embedded in five dimensions and compared by Procrustes distance.

| Scoring | Distance vs ordering lost, ρ | p | Given inventory divergence, ρ | p |
|---|---:|---:|---:|---:|
| Changes only | +0.21 | 0.34 | +0.13 | 0.55 |
| All pairs | +0.49 | 0.036 | +0.35 | 0.14 |

The planned comparison shows no relationship, and the next check shows why this
test could not have found one.

**Noise floor.** Each clan's recordings were split into random halves 20 times, and
the distance between the two halves computed in the same way:

| Scoring | Two halves of one clan, mean (range) | Two different clans, mean (range) |
|---|---:|---:|
| Changes only | 0.85 (0.66 to 1.02) | 0.94 (0.83 to 1.06) |
| All pairs | 0.77 (0.44 to 0.97) | 0.87 (0.72 to 1.02) |

Halves carry half the data and so are noisier than whole clans, but the overlap is
large: the distance is dominated by estimation noise. The Mantel result above is
therefore uninformative, not negative. The distance and the lost-predictability
score are also both computed from the same transition tables, so agreement between
them would not by itself show that either tracks divergence. That needs an outside
measure, such as how much two clans overlap in space.

Outputs: [coda_ordering.csv](results/coda_ordering.csv),
[coda_ordering_models.csv](results/coda_ordering_models.csv),
[coda_ordering_bootstrap.csv](results/coda_ordering_bootstrap.csv),
[coda_ordering_pairs.csv](results/coda_ordering_pairs.csv),
[shuffle_null_within.csv](results/shuffle_null_within.csv),
[ordering_checks.csv](results/ordering_checks.csv),
[distance_noise_floor.csv](results/distance_noise_floor.csv) and
[data_table.csv](results/data_table.csv).

![Whole-coda ordering](figures/plain/9_ordering_coda.png)

## Artifacts

| Output | Script |
|---|---|
| Within-clan CSV, figure 2 | `predictive_info_sweep`, then `plain_figures` |
| Leave-one-clan-out CSV, figure 3 | `universal_structure` |
| Pairwise CSV, figures 4 and 5 | `clan_similarity` |
| Mantel tests, per-pair CSV, figure 6 | `drift` |
| Ordering-only transfer and Mantel tests, figures 7 and 8 | `ordering_drift` |
| Whole-coda factored model, transfer, intervals, figure 9 | `coda_ordering` |
| Shuffle and shared-order reference points, distance noise floor, figure 10 | `ordering_checks` |
| Sample sizes per clan | `describe` |
| Native vs pooled EC1 CSV | `ec1_pacified` |
| Token-count overview, figure 1 | `plain_figures` |

Figure 1 uses fixed duration edges; figure 2 uses per-clan quantiles. Reproduction
commands are in the [README](README.md). [Limitations](limits.md) covers the
remaining sampling and interpretation issues.

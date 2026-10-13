# Development history

## Graph matching

The original question was whether coda identities could be recovered from
sequence position using QAP graph matching. Repetition-heavy transition matrices
made that approach poorly suited to the identification question. The current
project instead compares predictions of adjacent tokens.

## Predictive comparisons

The next version introduced within-clan bigram comparisons, cross-clan transfer,
and a shared rhythm/tempo representation. It retained native EC1 sequences as
a sensitivity analysis because EC1 contains speaker and timing information that
the Pacific data lack.

## September 2026 correction

Review found that the changes-only baseline still assigned probability to the
excluded current token. Independent uniform five-token data could score about
+0.32 bits under that comparison. Both distributions now condition on a change,
with baseline destination frequencies estimated before filtering.

The uncertainty calculation now resamples recordings within fixed cross-validation
folds and refits both models. The earlier implementation resampled overlapping
split scores.

The rerun does not support the earlier claims of a universal tempo rule or
above-zero changes-only gains in every clan. All eight all-pair tempo estimates
remain positive, but corrected changes-only effects and transfer are mixed.
Current results and assumptions are in [SUMMARY.md](SUMMARY.md).

## October 2026: drift hypothesis, ordering without inventory, and a second correction

The project took up a specific hypothesis: that the Procrustes distance between two
clans' sequence structure could act as a proxy for drift between them.

A first test found that distance tracked lost predictability only through coda
inventory. A second, on single features with inventory removed, found tempo
ordering mostly shared. A third described whole-coda ordering with a factored
log-linear model and carried one clan's ordering onto another clan's inventory.

That third analysis was first reported as showing that another clan's ordering
"misleads", because it scored below zero. An outside review pointed out that zero
was the wrong reference and that the headline used a model with cross terms the
data did not support. Shuffling codas within recordings showed that transfer with
no ordering at all scores as far below zero, through noise alone. Read against
that, and against a simulated shared ordering, clans share part of their ordering:
most of it for tempo, less for rhythm.

A split-half check then showed the Procrustes distance to be dominated by noise at
these sample sizes, so the drift hypothesis is untested, not rejected.

The lesson repeats September's: a score needs a reference that has been through
the same pipeline. Current results are in [SUMMARY.md](SUMMARY.md).

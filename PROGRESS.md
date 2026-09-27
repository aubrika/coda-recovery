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

# Limitations

This is an exploratory reanalysis of two published datasets. It has not been
independently replicated or peer reviewed.

## Recording differences

Caribbean EC1 recordings include speaker identities and onset times. Pacific
recordings provide session-level coda order without individual identities.
The main analysis pools speakers in both, but the collection methods remain
different. A Caribbean–Pacific comparison therefore combines biological and
recording differences.

Adjacent recorded codas are not necessarily adjacent calls by the same whale,
or turns in an exchange. Excluding identical adjacent tokens does not specifically
remove an individual whale's repetitions.

Individuals may recur across sessions. The recording bootstrap cannot account
for that dependence without identities. Some clans have few usable recordings;
a large coda count does not compensate for a small number of sampling units.

## Representation

Pacific rhythms are mapped to Caribbean templates. A nearest-template assignment
does not establish that the same category has the same biological role in both
populations. Codas without a supported click count are excluded.

Within-clan duration quantiles are estimated using each clan's full data, before
splitting recordings. This uses held-out duration information to define the
representation. The analysis evaluates prediction conditional on these fixed
labels, rather than a completely held-out preprocessing pipeline. Future
sensitivity checks should fit bin edges on training recordings alone.

Cross-clan analyses use fixed shared duration edges instead. Their tempo scores
are not directly comparable to within-clan quantile scores. Ornamentation and
rubato are not included.

## Statistical interpretation

The measured quantity is held-out log-likelihood gain between fitted models.
Smoothing, vocabulary size, sample size, and model mismatch affect it. A negative
score does not imply negative mutual information; it means the fitted sequence
model predicts less well than its baseline.

The corrected changes-only baseline conditions on the excluded current token.
It tests a specified frequency-based null, not every possible account of
repetition or contextual variation. The earlier unconditioned baseline created
a positive score even for independent data; its stronger claims are withdrawn.

Bootstrap intervals resample whole recordings within fixed folds and refit
models. They condition on folds, labels, and vocabulary, assume recording
independence, and do not cover model-selection uncertainty. No multiple-comparison
adjustment is applied. Near-zero endpoints should not be treated as decisive.

Transfer scores have no uncertainty intervals. Failure to transfer may reflect
inventory differences, sparse support, unequal sample sizes, or collection
methods, as well as transition differences. The descriptive Procrustes comparison
does not isolate biology or supply a significance test.

## What remains to check

Useful follow-ups include training-only duration bins, alternate rhythm
representations, smoothing sensitivity, matched recording protocols, and
independent replication. A separate shuffled or simulated control that preserves
recording composition would help distinguish local context from sequential
dependence.

Nothing here establishes meaning, syntax, a translation, or a species-wide rule.

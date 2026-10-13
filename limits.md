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

The leave-one-clan-out and pairwise cross-prediction scores have no uncertainty
intervals and carry the source clans' inventory with them, so failure to transfer
there mostly reflects inventory differences.

The whole-coda transfer scores remove inventory and have held-out bootstrap
intervals, but those intervals cover only which recordings are scored. They are
read against two reference points, shuffled recordings and a simulated shared
ordering, and the second of these assumes every clan has the same ordering
strength. Transfer estimated from limited data scores below zero through noise
alone, so the sign of a transfer score means nothing without those references.

The Procrustes distance between clans is close to the distance between two halves
of one clan. At these sample sizes it is dominated by estimation noise, and the
Mantel tests built on it are uninformative. The distance and the transfer scores
also come from the same transition tables; neither has been compared with an
outside measure such as spatial overlap or relatedness.

The Caribbean clan is 11 tagged whales. Its estimates describe those animals and
their social units, and its recordings are repeated samples of the same
individuals, not independent draws from a clan.

Adjacent codas are pooled across whales with no limit on the time between them.
Part of what is called order here may be exchange between whales (overlapping,
matching, turn-taking) and not an individual's sequencing.

## What remains to check

Useful follow-ups include training-only duration bins, alternate rhythm
representations, smoothing sensitivity, matched recording protocols, and
independent replication. The shuffled control that preserves recording
composition has now been run (see SUMMARY.md, "Reference points").

Still to do: an analysis of the Pacific clans alone using the source study's own
coda types; a time limit on what counts as adjacent; separate treatment of identity
and non-identity codas; and a comparison of any clan-to-clan measure with spatial
overlap between clans.

Nothing here establishes meaning, syntax, a translation, or a species-wide rule.

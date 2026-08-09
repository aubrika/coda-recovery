# Development history & lessons

A short, honest record of how this project got to its current form. The trustworthy
results and methods live in [`SUMMARY.md`](SUMMARY.md); this file is just the record
of the detour, kept for the lessons rather than the numbers.

## The retired approach: QAP re-identification

The project began as a harder question — *identification*: hide every coda label and
try to work out which coda is which purely from its position in the transition graph,
by aligning two halves of the data with **QAP** (quadratic-assignment graph matching).
It produced a signal that kept shifting: it appeared, weakened under stricter controls,
and eventually **flipped sign** depending on an arbitrary choice. We diagnosed why, and
the two lessons are the useful residue:

1. **Diagonal dominance breaks graph-matching.** Whales repeat (and match) so much that
   the who-follows-whom table is dominated by its diagonal. QAP-accuracy handles that
   unreliably — it can score a frequency-clean *scramble* above the real data. The metric
   was partly measuring its own artefact.
2. **The null's scale has to be chosen, and the answer depends on it.** A "what if order
   didn't matter" shuffle can be done within tiny exchanges (preserves persistence) or
   across whole recordings (destroys it), and the tempo result flipped between them. There
   was no principled single choice.

Along the way we also caught two null-construction bugs (nulls that didn't mirror the
split scale) and a flawed cross-dataset comparison (legacy-21-type on pooled Gero data vs
factored on single-whale Sharma data — different data *and* sequence definitions, so not
apples-to-apples). All are the kind of mistake worth remembering.

## The pivot: predictive information

The resolution was to stop trying to *identify* and instead measure **prediction**
directly: held-out, cross-validated **mutual information** (bigram vs unigram). It has
neither QAP problem — it never aligns tables (diagonal dominance is irrelevant) and never
shuffles (the frequency model *is* the baseline). Asked this way, the structure QAP kept
losing was there all along: clean, positive, reproducible, in every clan. **The finding
was never fragile; the earlier tool was.**

The QAP arm and its Gero-data pipeline have since been removed from the codebase to keep
the repository focused on the mutual-information results.

## Current status

Complete and consolidated around the MI result: within-clan prediction beyond frequency
and repetition (universal across 8 clans), the between-whale tempo exchange, clan-specific
grammar (cross-prediction + Procrustes), and the additive ornament/rubato check.
Next: standardize *all* clans (including EC1) through one uniform tokenization/sequence
pipeline, after finding that EC1's larger signal was mostly a measurement effect
(`ec1_pacified.py`).

# Limitations

*Draft, 2026-09-21. What this analysis can and cannot support, in the order a careful reader will ask.*

This is an independent, unfunded reanalysis of two published datasets. It has not been peer reviewed. The findings are
modest in size and stated as such; nothing here should be read as a claim about whale communication beyond what a
transition-probability model on these particular recordings can show.

## 1. Two datasets that were not collected to be compared

The eight clans come from two sources with different collection methods, and every cross-source comparison inherits
those differences.

| | Caribbean (EC1) | Pacific (7 clans) |
|---|---|---|
| Source | Sharma et al. 2024, Dataset 2 | Hersh et al. 2022 |
| Recording | Animal-borne tags (DTags); per-whale audio | Hydrophone recordings of groups |
| Codas used | 3,687 (after excluding codas of more than 10 clicks) in 217 recordings | 24,237 in 251 sessions (95–99% of codas typed, by clan) |
| Speaker identity | Known for each coda | Not recorded; a session is a group of unknown size |
| Timing | Absolute onset time of every coda | Order of codas within a session only |
| Per-clan size | one clan | 1,265 (SI) to 8,289 (REG) codas; 15 to 50 sessions |

The consequences:

- **"Pairs" are pairs in the recorded stream, not pairs in a conversation.** The unit of analysis throughout is two
  adjacent codas within one recording, with speakers pooled. In the Caribbean data a stream is often one tagged whale;
  in the Pacific data it is whoever was audible to the hydrophone. Adjacent codas may come from one whale answering
  itself, two whales in exchange, or two whales talking past each other. The analysis cannot tell these apart, and it
  does not try to. What it measures is the sequential structure of the stream that a listener would hear.
- **Self-repetition means different things in the two sources.** A repeated coda from a single tagged whale is
  repetition; in a pooled session it may be two whales producing the same coda. The analysis reports a variant with
  repeats removed, which narrows but does not close this gap.
- **The Caribbean-versus-Pacific distance is partly a data-source distance.** Every cross-clan measure places EC1
  farthest from the Pacific clans. Some of that is biology (the most geographically separated population), but some is
  method: single-whale streams versus pooled groups, tags versus hydrophones, timed versus ordered. The two cannot be
  separated with these data. The seven Pacific clans, all collected one way, are the clean within-protocol comparison,
  and the clan-specificity result should be read primarily from them.
- **Nothing is known about group composition, behavioural context, season, or whether the same individuals recur
  across sessions.** Hersh sessions carry no individual IDs, so the effective number of independent whales behind each
  Pacific clan is unknown and is certainly smaller than the number of codas.

## 2. What the tokens are, and what was thrown away to make them comparable

Every coda in all eight clans is reduced to two labels: a rhythm class (0–17, the nearest of the EC1 rhythm templates
from Sharma et al.) and a tempo bin (0–4, from total duration). This is the only representation both datasets support.

- **The rhythm templates were derived from the Caribbean clan.** Assigning Pacific codas to the nearest Caribbean
  template is a choice forced by the data; a Pacific coda with no close Caribbean analogue is still assigned somewhere.
  Hersh's own global coda-type labels exist but have no counterpart in the Sharma data, so they could not be used for
  the cross-clan work.
- **Tempo bins are quantiles.** For within-clan analysis, bins are balanced per clan so that frequency alone carries no
  information; for cross-clan analysis, one shared set of edges is used. Bin edges are a modelling decision, and the
  size of the tempo effect depends on it.
- **The two "expressive" features of the Sharma model, ornamentation and rubato, are not available for the Pacific
  clans and are excluded everywhere.** Any structure carried by those features is invisible here.
- **Coda typing is incomplete in the Pacific data** (1–5% untyped, by clan); untyped codas break sequences.

## 3. What the statistics do and do not establish

- **Mutual information is measured against a base rate that already includes coda frequency and self-repeats, with
  held-out cross-validation.** It answers "does the current coda predict the next, beyond what frequency and repetition
  explain?" It does not identify *which* transitions carry the structure, and it does not imply syntax, meaning, or
  intent.
- **Effects are real but small.** Next-coda prediction is dominated by repetition and a few frequent codas; the
  information beyond that is a fraction of a bit per coda. The result is that the fraction is reliably above zero in
  every clan, not that codas are richly ordered.
- **Cross-prediction (Figure 4) is directional and blends two kinds of difference.** Training on clan A and testing on
  clan B measures both which codas each clan uses and how it orders them, and the model, test set and baseline differ
  in each direction, so the matrix is legitimately asymmetric. It shows clans differ; it does not isolate ordering.
- **Procrustes distance (Figure 5) is the measure that isolates ordering geometry.** It is computed on tokens shared
  between the two clans, after optimal rotation, so inventory differences are removed by construction. It is a proper
  symmetric distance. It has no built-in significance test; distances are reported relative to one another, and the
  Caribbean caveat in §1 applies to its largest entries.
- **Leave-one-clan-out (Figure 3) tests transfer against the held-out clan's own base rates**, so the current coda
  earns no credit for revealing which clan it belongs to. "Tempo transfers, rhythm does not" is a statement about
  these eight clans and this tokenization; with seven of eight clans from one ocean and one protocol, it is not a
  statement about sperm whales in general.
- **No multiple-comparison correction is applied** across the per-clan and per-pair tables. The claims are about
  consistent direction across all clans, which is robust to this; individual cells are not.

## 4. Reproducibility and data access

- **Raw data are not redistributed.** The Hersh 2022 file (OSF) and the Sharma 2024 deposit (Zenodo) carry no explicit
  licence, so the repository ships fetch scripts and checksums, never the data. The Sharma pickles are converted once to
  plain CSV and the analysis pipeline never unpickles anything.
- **Every number in the README is regenerated by scripts in `src/coda_recovery/`**; results are written to `results/`
  and figures to `figures/`. Sample sizes above were read from the fetched data on 2026-09-21.
- **Single analyst, no independent replication.** Reviewer-level checks that would strengthen this: an independent
  re-tokenization, a permutation test on the Procrustes distances, and a bootstrap over sessions rather than over codas
  (sessions, not codas, are the independent units).

## 5. What would resolve the main caveat

Any Pacific dataset with individual attribution, or any Caribbean dataset recorded as pooled groups, would allow the
data-source and biological components of the Caribbean-versus-Pacific gap to be separated. Until then, the honest
summary is: *within one collection protocol, clans are measurably distinct in how they order codas; across protocols,
the apparent distance is larger and partly artefactual.*

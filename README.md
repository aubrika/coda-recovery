# coda-recovery

**Does the order of sperm-whale codas carry predictive information, and does it carry over from one clan to another?**

Python analysis of adjacent sperm-whale codas across eight vocal clans. The project
compares frequency-based and first-order sequence models on held-out recordings,
then tests whether sequence models transfer between clans.

A coda is a patterned burst of clicks. Here each coda is represented by a rhythm
class and a duration bin. The implementation covers data preparation, recording-level
cross-validation, conditional baselines, uncertainty estimation, and result figures.

## Results

**Knowing the current coda helps predict the next one in every clan, though most of
that is repetition. With each clan's own coda inventory accounted for, clans do
appear to order their codas differently, and the difference is in rhythm: how
duration changes from one coda to the next is largely shared between clans, while
one clan's rhythm ordering misleads about another's. Procrustes distance between
clans does not track how much is lost, so the "drift" hypothesis is so far a null
result.**

The score is a gain in bits per coda pair: how much better a model that sees the
current coda predicts the next one than a model that only knows how common each
coda is, on recordings neither model was fitted to. Above zero means order carries
information beyond frequency. Tempo (duration) and rhythm (click pattern) are
scored separately.

- **Order is predictive.** Across all adjacent pairs, tempo gains run from +0.15 to
  +0.86 bits per pair and are clearly above zero in all eight clans. Rhythm gains run
  from +0.07 to +0.78 and are clearly above zero in seven of eight.
- **Most of that is repetition.** Whales often repeat a coda, and a repeat is easy to
  predict. Scoring only the pairs where the coda changes, tempo gains fall to +0.03 to
  +0.64 and stay clearly above zero in four of eight clans. Rhythm gains fall to
  between -0.03 and +0.28 and are clearly above zero in none.
- **A whole model does not transfer between clans, mostly because clans use different
  codas.** A model fitted on seven clans predicts the eighth clan's changes better than
  that clan's own coda frequencies for tempo in three of eight clans, and for rhythm in
  none. That model carries the other clans' coda frequencies with it, so this says
  little about ordering.
- **With inventory accounted for, the ordering of whole codas still does not
  transfer.** A coda is a rhythm and a tempo together. When only the ordering is
  carried from one clan to another and every coda frequency is the target clan's own,
  another clan's ordering predicts a clan's changes worse than no ordering at all:
  -0.15 bits on average (95% interval -0.24 to -0.07), against +0.21 for a clan's own
  ordering. It helps in 8 of 56 clan-to-clan comparisons.
- **The difference is in rhythm.** Split into its parts, the tempo-to-tempo ordering
  does carry over (+0.09 bits, interval +0.02 to +0.14, helping in 45 of 56
  comparisons). The rhythm-to-rhythm ordering does not (-0.13, interval -0.20 to -0.09,
  helping in 8 of 56).

![Changes-only prediction gains with recording-bootstrap intervals](figures/plain/2_current_predicts_next.png)

![Leave-one-clan-out transfer: a model fitted on the other seven clans against each clan's own model](figures/plain/3_shared_vs_clan_specific.png)

"Clearly above zero" means the 95% interval excludes zero. For the first three
points, intervals come from 500 bootstrap resamples of whole recordings with
five-fold cross-validation by recording, and the whole-model transfer is a point
estimate. For the last two, see the next section.
[Methods and results](SUMMARY.md) has the definitions and the full tables.

### Do clans order their codas differently?

The hypothesis behind this project is that each clan has its own sequence
structure, and that the Procrustes distance between two clans' structures could
serve as a proxy for a kind of "linguistic drift" between them: clans that sit
further apart should preserve less of each other's predictability. Testing it took
three attempts, because clans differ first of all in which codas they use, and that
difference swamps everything else unless it is taken out.

**1. Whole codas, inventory left in.** Across the 28 pairs of clans, Procrustes
distance tracks how much predictability is lost between them (Spearman ρ = +0.47,
exact Mantel p = 0.007). But both measures also track how different the two clans'
coda inventories are, and once that is accounted for nothing is left (partial
ρ = -0.06, p = 0.77). The distance reflected which codas a clan uses, not how it
orders them.

**2. One feature at a time, inventory taken out.** Restricted to the tokens every
clan shares, and with one clan's ordering carried to another as the odds ratios of
its transition table, tempo ordering turned out to be mostly shared. But clans
share too few whole coda types for this method, so it could only say how one
feature is sequenced, not how codas are.

**3. Whole codas, inventory taken out.** Each clan's ordering is described by a
factored model: how the next coda's rhythm and tempo depend on the current coda's
rhythm and tempo, built from four small tables (rhythm to rhythm, tempo to tempo,
and the two cross terms) that are dense enough to estimate even where whole coda
types are rare. To predict clan B from clan A, A's model is rescaled until every
coda frequency is B's, keeping only A's ordering. Scoring pairs where the coda
changes:

| Ordering carried over | A clan's own | Another clan's | Helps in |
|---|---:|---:|---:|
| Tempo to tempo | +0.17 (+0.10 to +0.24) | +0.09 (+0.02 to +0.14) | 45 of 56 |
| Rhythm to rhythm | +0.10 (-0.03 to +0.17) | -0.13 (-0.20 to -0.09) | 8 of 56 |
| Whole coda | +0.21 (+0.04 to +0.32) | -0.15 (-0.24 to -0.07) | 8 of 56 |

Gains are bits per changed pair, averaged over clans, with 95% intervals.

- **Clans order whole codas differently.** Another clan's ordering does not merely
  fail to help; it predicts worse than using no ordering. This holds among the seven
  Pacific clans alone (helping in 5 of 42 comparisons).
- **The difference is in rhythm, not tempo.**
- **Rhythm and tempo do not appear to interact.** The cross terms add nothing to a
  clan's own gain, so a coda's ordering looks like its rhythm ordering plus its tempo
  ordering.
- **The method does not manufacture this.** When all eight clans are simulated from
  one shared ordering, each on its real inventory and recording sizes, the same
  analysis reports that another clan's ordering helps in 55 or 56 of 56 comparisons.
- **Distance still does not track what is lost.** Procrustes distance between clans'
  ordering against ordering lost gives ρ = +0.21, p = 0.34.

![Whole codas: Procrustes distance and ordering lost for every pair of clans](figures/plain/9_ordering_coda.png)

**Where this leaves the question.** Clans share how a coda's duration follows the
last one, and differ in how its rhythm does. Whether that difference grows in a way
a distance can measure is not shown: the drift hypothesis remains a null result.

Limits worth knowing:

- The intervals cover which recordings are held out and scored. They do not cover
  sampling of the recordings the models learn from.
- Rhythm classes come from Caribbean reference patterns. Pacific codas are assigned
  to the nearest one, which is approximate, and a clan's own rhythm ordering is only
  weakly predictive to begin with (its interval reaches zero).
- Duration bins are ordered, so successive codas of similar length land in
  neighbouring bins in any clan. Some of the shared tempo ordering may be duration
  changing smoothly, not a sequencing rule.
- With repeats included, most ordering carries over, because every clan repeats
  codas, and distance does track what is lost (ρ = +0.49, p = 0.04). That was not
  the planned test and it weakens once inventory is accounted for (ρ = +0.35,
  p = 0.14), so it is noted and not claimed.
- An earlier version of this project claimed a shared tempo rule and clan-specific
  rhythm, and withdrew the claim because its baseline was unfair (see
  [History and corrections](#history-and-corrections)). The result here is similar
  in outline but rests on a different method, and should be judged on that.

[Methods and results](SUMMARY.md#whole-codas-with-inventory-taken-out) has the
definitions, the checks and the full tables.

## What this does *not* show

- **Nothing about meaning or syntax.** This measures prediction of recorded token
  sequences. It does not identify meaning, syntax, or individual whales' choices.
- **Not one whale's choices.** Speakers are pooled in the main analysis.
- **Not a like-for-like comparison of oceans.** The Caribbean and Pacific data were
  collected differently, and shared processing does not remove those differences.

See [limitations](limits.md) for the full list.

## Reproduce

The committed CSVs and figures can be inspected without downloading data.
The September 2026 rerun used Python 3.14.5; direct dependency versions are pinned.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# PowerShell alternative: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

python data/fetch.py all
python data/fetch.py all --verify
```

The fetcher checks input SHA-256 digests against [the source manifest](data/sources.json).
Raw data are fetched separately; source details are in [provenance](data/raw/PROVENANCE.md).
The source includes Python pickles, read during EC1 preprocessing and rhythm-template
loading. Only use the recorded inputs.

Set the source path once:

```bash
export PYTHONPATH=src
# PowerShell alternative: $env:PYTHONPATH = "src"
```

Then run:

```bash
python -m coda_recovery.predictive_info_sweep
python -m coda_recovery.universal_structure
python -m coda_recovery.clan_similarity
python -m coda_recovery.drift
python -m coda_recovery.ordering_drift
python -m coda_recovery.coda_ordering
python -m coda_recovery.ec1_pacified
python -m coda_recovery.plain_figures
python -m pytest
```

These commands replace the corresponding files in `results/` and `figures/plain/`.
Tests cover independent and deterministic sequences, the changes-only baseline,
recording folds, bootstrap refitting, and cross-clan transfer.

## Read the code

| File | Purpose |
|---|---|
| [standardize.py](src/coda_recovery/standardize.py) | Shared tokenization and adjacent recording pairs |
| [predictive_info.py](src/coda_recovery/predictive_info.py) | Model scores, grouped cross-validation, recording bootstrap |
| [universal_structure.py](src/coda_recovery/universal_structure.py) | Leave-one-clan-out comparison |
| [clan_similarity.py](src/coda_recovery/clan_similarity.py) | Pairwise transfer and descriptive embedding distances |
| [drift.py](src/coda_recovery/drift.py) | Mantel tests relating Procrustes distance to lost predictability |
| [ordering_drift.py](src/coda_recovery/ordering_drift.py) | The same question for one feature at a time, with coda frequencies taken out |
| [coda_ordering.py](src/coda_recovery/coda_ordering.py) | Factored model of whole-coda ordering; transfer between clans on each clan's own inventory |

## History and corrections

The name comes from an earlier attempt to recover coda labels by graph matching.
[Development history](PROGRESS.md) records that change of direction.

**Correction, September 2026.** An earlier version of the changes-only comparison
used a baseline that still assigned probability to the excluded current coda.
Independent five-token data could therefore score about +0.32 bits solely because
repeats were removed. The baseline now accounts for the exclusion, and the earlier
claims of a universal tempo rule and above-zero changes-only effects in every clan
have been withdrawn. [Methods and results](SUMMARY.md#correction-to-the-earlier-analysis)
explains the correction.

## License and credits

The code is released under the [MIT License](LICENSE). The data are not mine and are
not redistributed here: the Caribbean recordings are from Sharma et al. (2024) and the
Pacific recordings from Hersh et al. (2022), fetched from their public deposits as
described in [provenance](data/raw/PROVENANCE.md).

Built with AI coding assistance (Claude Code). The questions, the analysis decisions
and the conclusions are mine.

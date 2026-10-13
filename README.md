# coda-recovery

**Does the order of sperm-whale codas carry predictive information, and does it carry over from one clan to another?**

Python analysis of adjacent sperm-whale codas across eight vocal clans. The project
compares frequency-based and first-order sequence models on held-out recordings,
then tests whether sequence models transfer between clans.

A coda is a patterned burst of clicks. Here each coda is represented by a rhythm
class and a duration bin. The implementation covers data preparation, recording-level
cross-validation, conditional baselines, uncertainty estimation, and result figures.

## Results

**Knowing the current coda helps predict the next one in every clan. The advantage
shrinks sharply once repeated codas are set aside, and what remains mostly fails to
carry over from one clan to another.**

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
- **What remains is mostly clan-specific.** A model fitted on seven clans predicts
  the eighth clan's changes better than that clan's own coda frequencies for tempo in
  three of eight clans (EC1, REG, SI), and for rhythm in none. On average it does
  worse than frequencies alone: -0.11 bits for tempo and -0.68 for rhythm.

![Changes-only prediction gains with recording-bootstrap intervals](figures/plain/2_current_predicts_next.png)

![Leave-one-clan-out transfer: a model fitted on the other seven clans against each clan's own model](figures/plain/3_shared_vs_clan_specific.png)

"Clearly above zero" means the 95% interval excludes zero. Intervals come from 500
bootstrap resamples of whole recordings, with five-fold cross-validation by
recording. The transfer figures are point estimates without intervals.
[Methods and results](SUMMARY.md) has the definitions, the full tables and the
combined rhythm-and-tempo results.

### What this may suggest

Read tentatively, these results suggest that each clan's coda sequences have a
largely clan-specific structure: order is predictive within a clan, but a model of
one clan's ordering says little about another's. Poor transfer can have other
causes too, such as different coda inventories, sparse counts and different
recording methods, so this is a reading of the results and not a conclusion.

That reading sets up the hypothesis this project is working toward: can the
Procrustes distance between two clans' sequence structures serve as a proxy for a
kind of "linguistic drift" between them? If it can, the distance should track how
much predictability is preserved from one clan to another. Clans whose structures
sit closer together should predict each other better, and clans further apart
should predict each other worse.

A first test is in, and it does not yet support the hypothesis. Across the 28 pairs
of clans, Procrustes distance does track how much predictability is lost between
them (Spearman ρ = +0.47, exact Mantel p = 0.007). But both measures also track how
different the two clans' coda inventories are, and once inventory is accounted for
nothing is left (partial ρ = -0.06, p = 0.77). As currently built, the distance
reflects which codas a clan uses, not separately how it orders them.

![Procrustes distance and predictability lost for every pair of clans, and the two plotted against each other](figures/plain/6_distance_vs_predictability.png)

Testing the hypothesis properly needs a transfer score and an embedding that are
both insensitive to inventory, for example by restricting each comparison to the
codas two clans share. [Methods and results](SUMMARY.md#procrustes-distance-and-lost-predictability)
has the details and the sensitivity checks.

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

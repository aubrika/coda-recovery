# coda-recovery

Python analysis of adjacent sperm-whale codas across eight vocal clans. The project
compares frequency-based and first-order sequence models on held-out recordings,
then tests whether sequence models transfer between clans.

A coda is a patterned burst of clicks. Here each coda is represented by a rhythm
class and a duration bin. The implementation covers data preparation, recording-level
cross-validation, conditional baselines, uncertainty estimation, and result figures.

## Results

The corrected analysis uses five recording folds and 500 bootstrap replicates,
resampling whole recordings and refitting the models.

- With all adjacent pairs included, tempo gains are positive in all eight clans;
  rhythm gains are positive in all eight as point estimates, with one interval crossing zero.
- When identical adjacent tokens are excluded, both models account for that exclusion.
  The results are mixed: several estimates are near zero, and most intervals include zero.
- In leave-one-clan-out prediction, tempo transfer is positive in **3 of 8** clans;
  rhythm and joint-token transfer are positive in **0 of 8**. These are point estimates.

![Changes-only prediction gains with recording-bootstrap intervals](figures/plain/2_current_predicts_next.png)

**Correction, September 2026:** the previous changes-only baseline assigned
probability to the excluded current token. Independent five-token data could
therefore score about +0.32 bits solely because repeats were removed. That baseline
has been corrected, and the earlier claims of a universal tempo rule and
above-zero changes-only effects in every clan have been withdrawn.
[Methods and results](SUMMARY.md) explains the correction and the current estimates.

## Scope

This measures prediction of recorded token sequences. It does not identify meaning,
syntax, or individual whales' choices. Speakers are pooled in the main analysis,
and the Caribbean and Pacific data were collected differently. Shared processing
does not remove those differences. See [limitations](limits.md).

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

The name comes from an earlier attempt to recover coda labels by graph matching.
[Development history](PROGRESS.md) records that change of direction.

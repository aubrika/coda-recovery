# coda-recovery

**Do sperm whales string their calls together in a meaningful order — and if so,
is that order the same from one clan to the next?**

Sperm whales "talk" in short bursts of clicks, like Morse code. Each patterned
burst is a **coda**. This project asks a simple question with a careful method:
when a whale picks its next coda, does the choice depend on the current one —
*beyond* the base rate of how often each coda happens to occur?

**Short answer: yes, robustly, in every clan we tested — but the ordering itself
is clan-specific.** The effect is real and reproducible, but modest: it makes the
next call *more predictable*, not a rich, meaning-carrying "grammar."

> **Read this first:** [`SUMMARY.md`](SUMMARY.md) tells the whole story in plain
> language, and why the method is trustworthy. This README is the short version.

## The animals and their "words"

Each whale population uses a set of distinct coda patterns — a small
**vocabulary** (about 21 patterns in the Caribbean group, several dozen in the
Pacific). Whales belong to **clans**: cultural groups, each with its own
characteristic mix of codas, like regional dialects.

Recent work (Sharma et al. 2024) shows a coda is better described by *two dials*
than one label:

- **Rhythm** — the pattern of gaps between clicks (like a drum pattern), 1 of 18.
- **Tempo** — how long the whole coda lasts, 1 of 5 duration classes.

The classic ~21 named types live *inside* this finer 18 × 5 grid.
**Figure 1** shows where all ~23,700 codas in the study actually fall (Caribbean
plus all 7 Pacific clans) — the whales concentrate on a handful of cells.

## How we ask the question — a prediction contest

The clean way to test whether order matters is **prediction**. Build two models
on part of the data and test them on held-out recordings:

- a **frequency-only** model — guess the next coda from base rates alone;
- a **sequence** model — guess the next coda from the *current* one.

If the sequence model predicts the held-out next coda **better**, order carries
real information. The size of that improvement, in **bits per coda**, is the
**mutual information** between consecutive codas — how much knowing the current
call reduces uncertainty about the next.

This has two advantages that matter: there is **no scrambling** (the
frequency-only model *is* the "order doesn't matter" baseline) and **no
label-matching** — just an honest out-of-sample prediction contest. Cross-validation
(train on some recordings, test on others) means the improvement can't be an
artefact of overfitting.

## What we found

- **The current coda predicts the next, beyond frequency — in every clan.** All 8
  clans go through one **uniform pipeline**, using only data both datasets share, so
  no clan is measured more cleanly than another. Even with whale self-repeats removed,
  **every clan is positive on both dials** — tempo +0.3 to +1.0 bits, rhythm +0.07 to
  +0.47, all clear of zero. Structured sequencing is a general feature, not a quirk of
  one clan. **(Figure 2.)**

- **Clans do not share a sequencing grammar.** Train the "what follows what" model
  on clan A and use it to predict clan B: for *every* pair of different clans, A's
  model predicts B **worse than B's own base rates**. A second method (aligning the
  clans' transition-geometries as closely as possible) agrees — every clan pair is
  distinct, with the Caribbean clan the biggest outlier. **The *what* is partly
  shared** (overlapping coda inventories) but **the *how* — the order — is
  clan-specific.** **(Figures 3 and 4.)**

## Figures (`figures/plain/`)

Plain-language, colorblind-safe. The palette is validated with the dataviz
checks — the tempo/rhythm pair clears CVD ΔE 22.8 and normal-vision ΔE 28.9;
sequential panels use one hue, the cross-prediction panel a diverging map with a
neutral zero.

1. **`1_the_data_model.png`** — every coda is a rhythm × a tempo (the 18 × 5 grid),
   with real coda counts pooled across the whole study (Caribbean + all 7 Pacific
   clans). *What we measure.*
2. **`2_current_predicts_next.png`** — in every clan, the current coda predicts the
   next beyond frequency *and* repetition (both dials, all 8 clans, clearing zero).
   *The headline.*
3. **`3_grammar_is_clan_specific.png`** — one clan's grammar predicts another's next
   coda *worse than chance*; only the diagonal (a clan predicting itself) is warm.
4. **`4_grammar_geometry.png`** — every clan's transition-geometry is distinct.

## What this does *not* show

- **The effect is modest** — fractions of a bit per coda beyond repetition. Real
  and reproducible, but not a rich combinatorial language.
- **Nothing about meaning.** Only that order is *structured*, not what any coda
  "means" — no translation, no dictionary.
- **Prediction is not identification.** Guessing the next coda is easy (75–85%,
  mostly repetition). Working out *which coda is which* from sequence position alone
  is a much harder, different question we don't tackle here.
- **Deliberately narrow scope.** We use only the data both datasets share. Richer
  EC1-only avenues (the between-whale exchange, the ornament/rubato features) are
  left for a possible later extension.

*(An earlier version asked the identification question with QAP graph-matching; it
proved the wrong tool for repetition-heavy data and was retired in favour of the
mutual-information test above. See [`PROGRESS.md`](PROGRESS.md) for that history.)*

## Data & the caveats it forced

Two sperm-whale sources, no other species:

- **Caribbean clan (EC1)** — Sharma et al. 2024, Dataset 2 (3,687 codas with real
  onset times and known speakers), using the paper's own rhythm and tempo labels.
- **7 Pacific clans** — Hersh et al. 2022; rhythm derived by nearest EC1 template,
  tempo by per-clan duration classes (a faithful approximation, not identical
  measurements).

Sharma's factored data is distributed as Python **pickles**; we de-pickle it once
into a plain CSV so nothing in the analysis pipeline ever unpickles. Provenance and
licences are in [`data/raw/PROVENANCE.md`](data/raw/PROVENANCE.md); unlicensed raw
data is **fetched, not redistributed**.

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
bash data/fetch_sharma.sh                        # fetch + de-pickle the Caribbean (EC1) data
bash data/fetch_phase2.sh                        # fetch the 7 Pacific clans (Hersh)
export PYTHONPATH=src

python -m coda_recovery.predictive_info_sweep    # within-clan MI, all 8 clans (uniform)
python -m coda_recovery.clan_similarity          # cross-clan grammar comparison (figs 3, 4)
python -m coda_recovery.ec1_pacified             # methods check: native EC1 vs uniform
python -m coda_recovery.plain_figures            # figures 1, 2
pytest                                           # MI-core sanity tests
```

Results append to `results/`; provenance and inventory are committed for audit.

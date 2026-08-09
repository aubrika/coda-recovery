# Do sperm whales string their calls together in a meaningful order? — in plain language

## The short answer

**Yes — robustly.** A sperm whale's current call genuinely predicts its next one,
*beyond* how common each call is, and this holds in **every clan we tested** (the
Caribbean clan plus all 7 Pacific clans). It even holds when we remove the easy
part (whales repeating themselves). The effect is real but modest: it makes the
next call *more predictable*, not a "grammar" in any rich, meaning-carrying sense.

The rest of this write-up explains what we measured, why the method is trustworthy,
and where the honest limits are.

## The animals and their "words"

Sperm whales talk in short bursts of clicks — like Morse code. Each patterned
burst is a **coda**, and each population uses a set of distinct coda patterns
(about 21 in the Caribbean group, several dozen in the Pacific). Think of these as
a small **vocabulary**. Whales are sorted into **clans** — cultural groups, each
with its own characteristic mix of codas (overlapping vocabularies used in
distinctive ways, like regional dialects).

**A richer description of each coda.** Recent work (Sharma et al. 2024) shows a
coda is better captured by *two dials* than one label: its **rhythm** (the pattern
of gaps between clicks — like a drum pattern, 1 of 18) and its **tempo** (how long
the whole coda lasts — 1 of 5 duration classes). We use the paper's own rhythm and
tempo labels, on its cleanest recordings (real timestamps and known individual
speakers), and leave its two "expressive" features (ornament, rubato) aside for now.

## The question, made precise

> Does the **order** matter? When a whale picks its next coda, does the choice
> depend on the current one — *beyond* the base rate of how often each coda occurs?

The clean way to ask this is **prediction**: build two models on part of the data
and test them on held-out recordings —
- a **frequency-only** model: guess the next coda from base rates alone;
- a **sequence** model: guess the next coda from the *current* one (a bigram).

If the sequence model predicts the held-out next coda **better** than the
frequency-only model, then order carries real information. The size of that
improvement, in **bits per coda**, is the **mutual information (MI)** between
consecutive codas — literally, the amount of uncertainty about the next call that
knowing the current one removes. Cross-validation (train on some recordings, test
on others) means the improvement can't be an artefact of overfitting — overfitting
would only *lower* it.

This has two big advantages that matter a lot below: there is **no scrambling**
(the frequency model *is* the "order doesn't matter" baseline) and **no
label-matching** — just an honest out-of-sample prediction contest.

## The result

**Every clan carries the signal — and we measure them all the same way.** All 8
clans (Caribbean EC1 + the 7 Pacific clans) go through **one uniform pipeline**: the
same rhythm/tempo derivation and the same within-recording sequences, so no clan —
not even the data-rich Caribbean clan — is measured more cleanly than another. Even
with the easy part removed (whales repeating themselves), **every clan shows positive
predictive information in both tempo and rhythm**: repeats-removed, tempo lands at
**+0.3 to +1.0 bits** and rhythm at **+0.07 to +0.47** across the eight clans, every
confidence interval clear of zero. Structured sequencing beyond frequency is a
**general feature**, not a quirk of one clan. (Figure `2_current_predicts_next.png`;
`python -m coda_recovery.predictive_info_sweep`.)

We deliberately keep to what both datasets share (rhythm, tempo, sequence order),
rather than lean on EC1's richer extras (known speakers, precise timing) — using them
would measure the Caribbean clan more finely than the rest and make it an artificial
outlier. (A methods check, `ec1_pacified.py`, shows exactly that: measured with its
native single-whale data EC1 looks far ahead, but on the uniform pipeline its rhythm
advantage shrinks into the Pacific band and its tempo lead roughly halves.)

## Do clans share a sequencing "grammar"? — No

With a robust measure in hand, we can finally ask the cross-clan question cleanly:
is one clan's sequencing structure the *same* as another's? Two ways, both saying
no. **Cross-prediction:** train the "what follows what" model on clan A and use it
to predict clan B's next coda. For *every* pair of different clans, A's model
predicts B **worse than B's own base rates** (negative transfer, −0.4 to −2.9 bits)
— a clan's grammar doesn't just fail to carry over, it actively *mis*-predicts
another clan. **Procrustes** (aligning the clans' transition-geometries as
directly as possible) agrees: all clan pairs are far apart. The Caribbean clan is
the biggest outlier from the Pacific clans, as you'd expect for the most separated
population. (Figures `3_grammar_is_clan_specific.png`, `4_grammar_geometry.png`;
`python -m coda_recovery.clan_similarity`.)

So the picture is consistent and, in hindsight, tidy: **the *what* is partly
shared** (clans draw on overlapping coda inventories) but **the *how* — the order
they string codas in — is clan-specific.** Sequencing is a cultural, clan-level
property. (Caveat: cross-prediction blends two kinds of difference — clans use
different codas *and* order them differently; the Procrustes distance, computed on
shared tokens, more specifically isolates the ordering geometry, and it too shows
clans are distinct. The Caribbean-vs-Pacific gap is also partly a data-source
difference — single-whale streams vs pooled repertoires.)

## Predicting the next call is not the same as identifying calls

It is easy to conflate two very different questions:
1. **Prediction** — given the current coda, guess the next. *(What we measure.)*
2. **Identification** — hide every label and work out which coda is which purely
   from its position in sequences.

Prediction is *easy* here (75–85% next-coda accuracy, mostly from repetition plus a
few dominant codas — the MI above quantifies exactly the part beyond base rates).
Identification is *much harder*. The two are genuinely different: an English speaker
can predict that "the" is followed by a noun, but if you erased every word and
showed only "which blob follows which," you'd struggle to point to "the" — because
*many* words precede nouns. **Predictable is not the same as identifiable.**

*(An earlier version of this project asked the identification question directly,
with QAP graph-matching. It proved the wrong tool for repetition-heavy data — the
who-follows-whom table is dominated by self-repeats, which alignment handles
unreliably — and was retired in favour of the mutual-information test above. The
development history is in `PROGRESS.md`.)*

## What it means

Mostly, a coda's identity lives in **how it sounds** and **how often it's used**.
On top of that, there is **genuine, universal, but modest sequential structure**:
the current coda shifts the odds on the next one — through heavy repetition, and,
underneath that, real "this tends to follow that" structure in both rhythm and
tempo, within every clan. This is *predictable order* — not "whale grammar" in a
strong, meaning-bearing sense.

As far as the literature shows, the specific question — comparing the *ordering* of
coda types, and measuring its information content, within and between clans — has
not been asked before, so even this modest, careful answer is new ground.

## Honest limits

- The effect is **modest** (fractions of a bit per coda beyond repetition) — real
  and reproducible, but not a rich combinatorial language.
- This says **nothing about meaning** — only that order is *structured*, not what
  any coda "means."
- The rhythm/tempo tokens are **derived** for every clan (nearest-template rhythm,
  quantile-binned tempo) — a faithful approximation on equal footing, not identical
  measurements.
- **EC1 gets no special treatment.** Using the Caribbean clan's richer native data
  (known speakers, precise timing) would measure it more finely than the others and
  make it an artificial outlier: on the uniform pipeline its rhythm advantage shrinks
  into the Pacific band (0.81 → 0.35 bits) and its tempo lead roughly halves. A methods
  check (`ec1_pacified.py`) documents this; the primary analysis uses only shared data.
- We keep the scope **deliberately narrow** — only the data both datasets share, and
  only the two questions above. Richer EC1-only avenues (the between-whale exchange,
  the expressive ornament/rubato features) are left for a possible later extension.

## Figures (`figures/plain/`)

Plain-language and colorblind-safe; the palette is validated with the dataviz
checks (tempo/rhythm categorical pair clears CVD ΔE 22.8 and normal-vision 28.9;
figures 1 and 4 are one-hue sequential ramps, figure 3 a diverging map with a
neutral zero).

- `1_the_data_model.png` — every coda is a rhythm × a tempo (18 × 5 grid), with
  real counts pooled across the whole study (Caribbean + all 7 Pacific clans).
- `2_current_predicts_next.png` — **the headline.** In every clan, the current coda
  predicts the next beyond frequency *and* repetition (both dials, all 8 clans).
- `3_grammar_is_clan_specific.png` — clan×clan grammar transfer: only the diagonal
  (a clan predicting itself) is positive; every cross-clan pair is negative.
- `4_grammar_geometry.png` — geometry of clan grammars (Procrustes distance,
  symmetric); all clans distinct, Caribbean the outlier.

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
bash data/fetch_sharma.sh                 # fetch + de-pickle the Caribbean (EC1) data
bash data/fetch_phase2.sh                 # fetch the 7 Pacific clans (Hersh)
export PYTHONPATH=src
python -m coda_recovery.predictive_info_sweep   # within-clan MI, all 8 clans (uniform)
python -m coda_recovery.clan_similarity         # cross-clan grammar comparison
python -m coda_recovery.ec1_pacified            # methods check: native EC1 vs uniform
python -m coda_recovery.plain_figures           # figures 1, 2
pytest                                          # MI-core sanity tests
```

A detailed, expert-facing method section follows.

---

## Method (detail, for a reviewer)

### 1. Data
Two sperm-whale sources, no other species. **Caribbean clan EC1** — Sharma et al.
2024's Dataset 2 (3,687 DTag codas after dropping >10-click codas; real onset times
and speaker IDs). **7 Pacific clans** — Hersh et al. 2022 (repertoire-level, no
speaker IDs). De-pickled once into a plain CSV so nothing in the pipeline unpickles
(`coda_model.py`, `inventory_factored.py`). Provenance and licences in
`data/raw/PROVENANCE.md`; unlicensed raw data is fetched, not redistributed.

### 2. The uniform pipeline (`standardize.py`)
Every clan — EC1 included — is tokenized and sequenced the *same* way, so the
cross-clan comparison is apples-to-apples: **rhythm** = nearest of the paper's 18 EC1
templates; **tempo** = 5 duration bins (per-clan quantiles for the within-clan test;
shared EC1 edges for the cross-clan comparison, where tokens must mean the same
thing); **pairs** = adjacent codas within one recording, *speakers pooled* (EC1
ordered by onset, Pacific by coda_number). This deliberately does **not** use EC1's
native labels or single-whale segmentation — those would make EC1 an artificial
outlier (see Honest limits); the one place native EC1 is measured is the
`ec1_pacified.py` methods check that demonstrates exactly that.

### 3. The measure: held-out predictive information
The identity token is the (rhythm, tempo) cell; we also test each axis alone. For
repeated ⅔/⅓ splits of the recordings we fit an add-α-smoothed bigram P(next|current)
and unigram P(next) on train and score, on held-out pairs,
`mean( log2 P_bi(next|cur) − log2 P_uni(next) )` — the cross-validated MI in bits/coda,
with a bootstrap 95% CI over folds. The **transition-only** variant trains and tests
on non-self pairs (a≠b), isolating "given a change, is the destination predictable
beyond base rate" — training on non-self is essential, or the full bigram's diagonal
mass makes any change look unpredictable. Code: `predictive_info_sweep.py`,
`clan_similarity.py`.

### 4. Controls and honesty
No shuffle scale to choose (the unigram *is* the frequency baseline); cross-validation
guards overfitting; results carry bootstrap CIs with the repeat component separated
out. The retired QAP re-identification arm, the two null bugs, and a flawed
legacy-vs-factored comparison a reviewer caught are all recorded in `PROGRESS.md`
rather than smoothed over.

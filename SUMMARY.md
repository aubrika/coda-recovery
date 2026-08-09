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

**Within a single whale's stream of codas** (Caribbean clan), the current coda
predicts the next, beyond frequency, by a wide margin — cross-validated:

| dial | predictive info (all) | with repeats removed |
|---|---|---|
| Tempo (duration) | +1.40 bits | **+0.81 bits** |
| Rhythm (click pattern) | +0.87 bits | **+0.70 bits** |
| Both (rhythm+tempo) | +1.80 bits | **+0.79 bits** |

Every value is comfortably above zero. A lot of the "all" column is simple
**repetition** (whales repeat a coda ~75–85% of the time — legitimate
order-dependence, but the easy kind). The striking part is the **repeats-removed**
column: even when a whale *changes* coda, the current one predicts *where it goes*,
beyond base rates — in tempo, rhythm, and jointly. (Figure `2_current_predicts_next.png`.)

**This is universal across clans.** Running the same test inside each of the 7
Pacific clans, **every clan** shows positive predictive information in tempo and
rhythm, and the repeats-removed transition signal is positive in **all 7** for both
tempo (+0.32 to +0.61 bits) and rhythm (+0.07 to +0.39). So structured sequencing
is not a quirk of one clan — it's a general feature. (Reproducible:
`python -m coda_recovery.predictive_info_sweep`.)

**Between whales — the exchange.** Sperm whales chorus and take turns. When we
build transitions *across* speakers (one whale's coda → the other whale's reply,
within the 2-second turn-taking window), the predictive structure is real and
concentrated in **tempo**: +0.52 bits, almost all of it genuine (not just
matching). In plain terms, **a whale's reply duration is predictable from its
partner's** — the coda "matching" and duration-drift ("rubato") the paper
describes. Rhythm and the full type carry little between-whale signal, but those
tests are data-starved (~480 pairs), so treat their nulls cautiously.

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
population. (Figures `4_grammar_is_clan_specific.png`, `5_grammar_geometry.png`;
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

## An additive check: do ornament and rubato add anything? — barely

The paper layers two *expressive* features on top of rhythm and tempo: **ornament**
(an occasional extra click) and **rubato** (smooth duration drift across a run). We
kept rhythm+tempo as the "classical coda type" analysis above and asked, as a
*separate, additive* question, whether these two carry extra predictive information.

They add almost nothing to predicting the **next call's identity**: on top of
rhythm+tempo, ornament contributes a negligible **+0.01 bits** and rubato actually
**hurts** (−0.31 — it splinters the predictor without adding signal). So the
classical (rhythm,tempo) description already captures the identity-predictive part
of the sequencing. The features do have a little structure of their *own*: the next
call's ornament is **not** predictable from the current call (−0.01), but its
**rubato direction is** (+0.13 bits) — the duration drift is sustained across a run,
exactly as the paper reports. (Figure `6_expressive_adds_little.png`; `python -m
coda_recovery.expressive`. Caveat: ornament and rubato are *context* features
defined via neighbours, so even these small numbers are partly neighbourhood-
encoding, not purely new structure.)

## What it means

Mostly, a coda's identity lives in **how it sounds** and **how often it's used**.
On top of that, there is **genuine, universal, but modest sequential structure**:
the current coda shifts the odds on the next one — through heavy repetition, and,
underneath that, real "this tends to follow that" structure in both rhythm and
tempo, within every clan and (for tempo) across the turn-taking exchange between
whales. This is *predictable order*, consistent with the paper's rubato and coda
matching — not "whale grammar" in a strong, meaning-bearing sense.

As far as the literature shows, the specific question — comparing the *ordering* of
coda types, and measuring its information content, within and between clans — has
not been asked before, so even this modest, careful answer is new ground.

## Honest limits

- The effect is **modest** (fractions of a bit per coda beyond repetition) — real
  and reproducible, but not a rich combinatorial language.
- This says **nothing about meaning** — only that order is *structured*, not what
  any coda "means."
- The between-whale exchange result rests on **little data** (~480 turn-taking
  pairs); tempo there is solid, rhythm/joint are underpowered.
- We used the paper's rhythm/tempo labels for the Caribbean clan and *derived* them
  for the Pacific clans (nearest-template rhythm, per-clan duration classes), so the
  Pacific numbers are a faithful approximation, not identical measurements.
- **EC1's much larger signal is mostly a measurement effect, not clan biology.**
  EC1 is measured more cleanly than the others (native rhythm/tempo labels;
  single-whale sequences from known speakers; the 41% attributed subset). Put EC1
  through the *identical* Pacific pipeline — derived rhythm, quantile tempo, pooled
  within-recording order, all codas — and its **rhythm** advantage collapses into the
  Pacific band (total 0.81 → 0.35 bits) and its **tempo**-total advantage roughly
  halves (1.38 → 0.92). The tempo signal stays comparatively high, but that residual
  is confounded — pooling speakers folds in the between-whale "matching," and balanced
  tempo bins give more MI headroom than native fixed edges — so it is *not* clean
  evidence of a richer clan grammar. So the earlier "EC1 is special" impression is
  largely how EC1 was measured, not a categorically more structured clan.
  (`ec1_pacified.py` → `results/ec1_pacified.csv`.)

## Figures (`figures/plain/`)

Plain-language and colorblind-safe; the palette is validated with the dataviz
checks (tempo/rhythm categorical pair clears CVD ΔE 22.8 and normal-vision 28.9;
figure 1 and 5 are one-hue sequential ramps, figure 4 a diverging map with a
neutral zero).

- `1_the_data_model.png` — every coda is a rhythm × a tempo (18 × 5 grid), with
  real counts pooled across the whole study (Caribbean + all 7 Pacific clans).
- `2_current_predicts_next.png` — **the headline.** In every clan, the current coda
  predicts the next beyond frequency *and* repetition (both dials, all 8 clans).
- `3_between_whale_reply.png` — the turn-taking exchange: only the reply's duration
  is predictable from the first whale's coda.
- `4_grammar_is_clan_specific.png` — clan×clan grammar transfer: only the diagonal
  (a clan predicting itself) is positive; every cross-clan pair is negative.
- `5_grammar_geometry.png` — geometry of clan grammars (Procrustes distance); all
  clans distinct, Caribbean the outlier.
- `6_expressive_adds_little.png` — ornament and rubato add almost nothing on top of
  (rhythm, tempo).

## Reproduce

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
bash data/fetch_sharma.sh                 # fetch + de-pickle the Caribbean (EC1) data
bash data/fetch_phase2.sh                 # fetch the 7 Pacific clans (Hersh)
export PYTHONPATH=src
python -m coda_recovery.predictive_info        # the clean within-clan MI result
python -m coda_recovery.predictive_info_sweep   # between-whale + all Pacific clans
python -m coda_recovery.clan_similarity         # cross-clan grammar comparison
python -m coda_recovery.ec1_pacified            # EC1 under the uniform pipeline
pytest                                          # MI-core sanity tests
```

A detailed, expert-facing method section follows.

---

## Method (detail, for a reviewer)

### 1. Data
Two sperm-whale sources, no other species. **Caribbean clan EC1** — Sharma et al.
2024's Dataset 2 (3,687 DTag codas after dropping >10-click codas; real onset times
and speaker IDs), with the paper's own rhythm (0–17) and tempo (0–4) labels
(verified 100% against its cluster templates; ornament rate 3.8% vs the paper's
~4%). De-pickled once into a plain CSV so nothing in the pipeline unpickles
(`coda_model.py`, `inventory_factored.py`). **7 Pacific clans** — Hersh et al. 2022;
rhythm derived by nearest EC1 template, tempo by per-clan duration quantiles.
Provenance and licences in `data/raw/PROVENANCE.md`; unlicensed raw data is
fetched, not redistributed.

### 2. The measure: held-out predictive information
The identity token is the (rhythm, tempo) cell; we also test each axis alone.
Consecutive token pairs come from single-whale call sequences (same speaker,
onsets ≤ 8 s apart) for the within test, turn-taking pairs (different speakers, next
onset 0–2 s after the previous coda's end) for the between test, and within-group
repertoire order for the Pacific clans. For repeated ⅔/⅓ splits of the recordings
we fit an add-α-smoothed bigram P(next|current) and unigram P(next) on train and
score, on held-out pairs, `mean( log2 P_bi(next|cur) − log2 P_uni(next) )` — the
cross-validated MI in bits/coda, with a bootstrap 95% CI over folds. The
**transition-only** variant trains and tests on non-self pairs (a≠b), isolating
"given a change, is the destination predictable beyond base rate" — training on
non-self is essential, or the full bigram's diagonal mass makes any change look
unpredictable. Code: `predictive_info.py`, `predictive_info_sweep.py`.

### 3. Controls and honesty
No shuffle scale to choose (the unigram *is* the frequency baseline); cross-validation
guards overfitting; results carry bootstrap CIs with the repeat component separated
out. The retired QAP re-identification arm, the two null bugs, and a flawed
legacy-vs-factored comparison a reviewer caught are all recorded in `PROGRESS.md`
rather than smoothed over.

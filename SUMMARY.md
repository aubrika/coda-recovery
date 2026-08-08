# Do sperm whales string their calls together in a meaningful order? — in plain language

## The animals and their "words"

Sperm whales talk in short bursts of clicks — like Morse code. Each patterned
burst is called a **coda**, and each population uses a set of distinct coda
patterns: about 21 different ones in the Caribbean group we studied, and several
dozen in the Pacific groups. Think of these coda types as a little **vocabulary**
of "words."

Whales are also sorted into **clans** — large cultural groups, each with its own
characteristic set of codas and how often it uses them. In fact a clan is
*defined* by this repertoire, and clans that share the same waters still keep
distinct repertoires. The inventories **overlap heavily** — many coda types show
up in more than one clan — but each clan favours its own mix, and a few codas are
near-unique to one clan. So it is not quite "same words, different speakers"; it
is more like **regional dialects** — a largely shared vocabulary, used in
distinctive ways. (No, whales do not all use all codas equally: which codas a
whale produces, and how often, is exactly what marks its clan.)

## The question

Everyone already knows *which* codas each clan uses and *how often*. We asked a
different question:

> Does the **order** matter? When a whale picks its next coda, does the choice
> depend on what came just before — so that a coda has a **role in the sequence**,
> the way "the" in English is usually followed by a noun?

If order carries information, you should be able to **identify a coda just from
its position in the back-and-forth** — from what tends to come before and after
it — *without listening to the coda itself*. That would be a hint of something
grammar-like. If order carries nothing, then a coda is just a coda, and only its
sound and its frequency matter.

## How we tested it

1. Take **one clan's** recordings and split them into two halves. The split is
   **random, at the level of whole recording sessions** (a recording day for the
   Caribbean clan; a recording bout, called a *repertoire*, for the Pacific
   clans). Because we divide *sessions* — not individual codas — the two halves
   share **no recordings**, so they are genuinely independent samples rather than
   two views of the same conversations.
2. From each half, **calculate** a "who-follows-whom" table (a *transition
   matrix*): go through the codas in the true order they were produced and count
   how often each coda type is immediately followed by each other type. This
   table is **computed by us from the ordered sequence** in the data — it is not
   something the dataset hands us; the dataset provides only the coda labels and
   their order.
3. **Hide the names** of the coda types in both tables.
4. Ask a computer to **re-match** the anonymized types between the two halves,
   using *only* the shape of each type's row-and-column in the table — its
   pattern of what comes before and after it.
5. Count how many of the coda types it puts back correctly.

**Why 15 types?** The full vocabularies differ (21 in the Caribbean clan, 54–85
in the Pacific clans), and the rarest types appear too seldom to estimate their
transitions reliably — their rows in the table are mostly empty, which is just
noise. We therefore use **each clan's 15 most frequent coda types**: enough to be
meaningful, common enough to have real data in most cells, and the **same count
across every clan** so the comparison is fair. (This choice is not doing the work:
see the robustness check under "What we found.")

**The catch, and the fix.** Getting a lot right *sounds* impressive, but it could
be a cheat. If one coda is very common in both halves, you can match it just by
noticing it's common — no sense of "order" needed. So we need to subtract out that
cheat. That is the **real-vs-shuffled** comparison, the heart of the whole thing,
explained next.

## The real and shuffled datasets (the core control)

We run everything **twice**, on the same split:

- **Real** = the codas in the **true order the whales produced them**.
- **Shuffled** = the **same codas, with their order scrambled within each
  recording session**. Every coda type still appears the exact same number of
  times, each session is the same length, and all the frequencies are identical —
  the **only** thing destroyed is the sequence.

Here is a **real 20-coda recording session** from the Caribbean clan, in its true
order and in one scrambled copy (each column is one coda in time; both rows
contain exactly thirteen `1+1+3`, four `5R1`, three `7I`):

```
 time →      1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20
 REAL     1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3  5R1  5R1  5R1  5R1  7I   7I   7I 1+1+3 1+1+3
 SHUFFLED 1+1+3 1+1+3  5R1  5R1  5R1  7I 1+1+3  7I 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3 1+1+3  7I 1+1+3 1+1+3  5R1
```

The **real** row is *blocky*: long runs of one coda, then a clean switch to the
next (…`1+1+3`→`5R1`→`7I`→`1+1+3`…). The **shuffled** row has the identical
thirteen/four/three counts but the blocks are gone. A method that keys on *order*
sees a difference between these two rows; a method that keys only on *how common
each coda is* sees them as identical. That gap is exactly what we measure.

The shuffled version is the honest yardstick: it is a "what if order didn't matter
at all?" copy of the same data. Anything the computer still recovers from the
shuffled data, it is getting **from frequency alone**. So the quantity that
actually answers our question is:

> **real − shuffled** = the part of the recovery that genuinely comes from coda order.

This also disposes of two worries at once. *Is it just the very common coda like*
`1+1+3`*?* No — the shuffled copy keeps `1+1+3` exactly as common, so if prediction in the real dataset beats
shuffled, it should also be beating that frequency. *Could a small dataset just look
structured by chance?* Any such fluke is baked into the size and composition of
the data — and the shuffled copy has the identical size and composition — so the
fluke appears equally in both and cancels in the difference. And note the
frequencies we compare against are always **that clan's own** (indeed each
session's own) — never frequencies pooled across clans.

## What we found

A **small but genuine** effect — much smaller than it first looked, and not
universal. The decisive test is the **paired real-vs-shuffled comparison** (real
accuracy minus shuffled accuracy, measured across 30 independent random splits,
with a 95% confidence range on the average difference — see Method):

- In the **original Caribbean clan**, order really does carry a little extra
  identity: about **1–2 extra codas out of 15** are identifiable from order alone,
  beyond frequency (**+1.4 of 15, 95% range +0.3 to +2.5** — the whole range is
  above zero, so it is unlikely to be a fluke).
- The same faint signal appears in **2 of the 7 Pacific clans** (PO, SI), is
  **borderline** in 2 more (REG, RI), and is **absent** in 3 (SH, FP, PALI). So it
  is real in places, but **not a universal law** of sperm whale communication.
- It is **not driven by the dominant coda.** Remove the two most common Caribbean
  codas (`1+1+3`, `5R1`) and swap in the next tier, and the signal is *stronger*
  (+2.0 of 15), because the common codas are the easy-to-match-by-frequency ones
  that add little to the *difference*. The mid-frequency codas carry the order
  signal. (It is, however, sensitive to exactly how many types you include —
  shrinking to 13 types loses significance — an honest sign the effect is small.)
- The clan with the *least* data (SI) shows the *strongest* effect, which rightly
  invites suspicion — a small dataset gives a noisier, easier-to-fluke estimate.
  We checked it two ways and it holds up: SI's signal is **genuine syntax, not
  self-repetition** (it is unchanged when self-repeats are removed — see next
  section), and its confidence range is well clear of zero. We nonetheless treat
  the *magnitude* and the "strongest of all clans" ranking with caution: with only
  ~1,200 codas and 15 sessions, SI's number is the **least precise**, and we would
  want more SI data before leaning on the ordering. (The effect is *not* generally
  explained by data volume — but neither do we claim less data causes more signal.)
- **Across two different clans, the order does not transfer.** The sequencing that
  helps identify a coda inside its own clan tells you nothing about another clan.
  (This negative is itself limited by data — with only a few thousand codas per
  clan, a weak shared signal could be there and we would miss it — so we state it
  as "no evidence of transfer," not "proof of none.")

## Is it grammar, or just repetition?

Sperm whales **repeat the same coda a lot** — in the Caribbean clan, 79% of
back-to-back pairs are the *same* type (you can see it in the worked example:
eleven `1+1+3` in a row). Repeating a coda is technically "order," but it is a
trivial kind. The interesting question is whether there is genuine **syntax** —
does coda A tend to be followed by a *different* coda B in a patterned way?

We can separate the two. Self-repetition lives on the "diagonal" of the
who-follows-whom table (type → same type); genuine syntax lives off it (type →
different type). So we re-ran the whole paired test **with self-repetition removed**
(diagonal zeroed, for both real and shuffled). What survives is real syntax:

| clan | full (with self-repeats) | off-diagonal (syntax only) | reading |
|---|---|---|---|
| **Caribbean EC1** | +1.4 of 15 | **+7.8 of 15** | **strong syntax** (repeats were *hiding* it) |
| **Pacific SI** | +3.4 | **+3.3** | **genuine syntax** (unchanged) |
| **Pacific REG** | +1.2 (borderline) | **+1.0** ✓ | **modest syntax** (repeats were masking it) |
| Pacific PO | +1.6 ✓ | −0.5 | **was just repetition** — no real syntax |
| SH / FP / PALI / RI | ≈ 0 | ≈ 0 | nothing |

Two things fall out, and both matter:

- **The signal is genuinely syntactic, not mere repetition.** In the Caribbean
  clan, removing self-repeats makes the effect *far larger* (from +1.4 to +7.8 of
  15). The whales' self-repetition was actually *diluting* the who-follows-what
  structure, because repeats are the same for every coda and carry little identity.
- **But it is honest to separate the clans.** Once you demand real syntax,
  **PO drops out** (its apparent signal was pure repetition), while **REG comes in**.
  So the clans with genuine sequencing structure are **EC1, SI, and REG** — still
  3 of 8, but not the same 3 the headline number gave.

(Reproducible: `python -m coda_recovery.syntax`.)

## Zooming in: is it the *rhythm* or the *timing*?

So far we treated each coda as a single label (like "`1+1+3`"). But recent work
(Sharma et al. 2024) shows a coda is better described by **two independent dials**:

- its **rhythm** — the *pattern* of gaps between clicks (like a drum pattern), and
- its **tempo** — how *long* the whole coda takes (fast or slow),

plus two fine "expressive" touches: an occasional extra **ornament** click, and
**rubato** — a smooth speeding-up or slowing-down of duration across a run of
codas. We rebuilt the whole analysis on this richer description, using the paper's
own rhythm/tempo labels and a cleaner recording set that comes with **real
timestamps and known individual speakers** (so "next coda" and "same whale" are
exact, not approximated).

Then we asked a sharper question than before: **which dial carries the sequential
signal — the rhythm, or the timing?** We split each coda into its rhythm and its
tempo and ran the same re-identification test on each.

**The answer is timing, not pattern.** Only **tempo** shows a *re-identifiable*
sequential signal (clears the shuffle bar); **rhythm** does not. This is *not* to
say rhythm order is random — even when a whale *changes* rhythm, the current
rhythm predicts the next one somewhat better than chance (see the next section).
It is that rhythm's structure is too weak, and spread over too many (18) noisy
categories, to let you *re-identify* which rhythm is which across recordings. Its
durations, by contrast, *drift in a structured, directional way* across a run —
exactly the **rubato** the paper describes — which is distinctive enough to
re-identify. So the *identifiable* sequential structure is a matter of
*timing/expression*, not of which drum-pattern comes next. (Figure
`7_which_axis.png`. Reproducible: `python -m coda_recovery.recover_factored`.)

## Predicting the next call is not the same as identifying calls

It is easy to conflate two very different questions, so it is worth separating
them plainly — especially because they give opposite-looking answers:

1. **Prediction** — *given the current coda, can you guess the next one?*
2. **Identification** (what this whole project measures) — *if you hid every
   label, could you work out which coda is which from its position in sequences
   alone?*

**Prediction is easy here.** You can guess the next coda **75–85%** of the time.
Even *rhythm alone* predicts the next coda **82%** of the time. A lot of that comes
from two dull facts: whales **repeat** (the next coda is the same as the current
one ~80% of the time), and a **few codas are very common** (one rhythm is 64% of
all codas). But it is *not only* repetition: even when a whale actually **changes**
coda, the current one still predicts where it goes better than chance — for rhythm,
54% vs a 39% base rate (a real +15-point gain); for tempo, more (+26). So there is
genuine "A tends to be followed by B" structure in every axis.

**Identification is much harder, and mostly fails** — because the very thing that
makes codas predictable (everyone repeats) is *identical for every coda*, so it
gives you no way to tell them apart. Only tempo behaves distinctively enough
(its durations drift *directionally*) to be identified.

An analogy: in English you can reliably predict that the word after "the" is a
noun. But if someone erased every word and handed you only "which word-blob
follows which," you would struggle to point to which blob is "the" — because *many*
words are followed by nouns. **Predictable is not the same as identifiable.**

So, to answer the two natural questions directly:

- *Can we still predict the next coda from sequence data?* **Yes, very well** — for
  rhythm, tempo, and the full type alike (the current coda helps in every case).
- *Can we re-identify (reconstruct) coda types from sequence position alone,
  beyond frequency?* **Mostly no** for the click-pattern/rhythm and the full type
  on this dataset; **yes for tempo.** The data-model refactor did not remove
  predictability — it let us pinpoint that the *identifiable* sequential structure
  lives specifically in **timing**.
- *Does using the full (rhythm, tempo) tuple make re-identification more reliable
  than the axes separately?* **No — it makes it worse.** Combining dilutes the
  clean tempo signal with the noisy rhythm one, and spreads the same ~2,800
  transitions across 64 token types instead of 5 (≈1 per cell vs ~114) — far too
  thin. **Tempo alone is the sweet spot.** (Reproducible: `python -m
  coda_recovery.predictability`.)

## What it means

Mostly, a sperm whale coda's identity lives in **how it sounds** and **how often
it's used** — and, on top of that, in a lot of plain **repetition**. But underneath
the repetition there is **genuine syntax** in a few clans (Caribbean EC1, Pacific
SI and REG): a real tendency for particular codas to follow particular *other*
codas, **statistically distinguishable from both random guessing and
frequency-based guessing** (that is what "the confidence range clears zero"
means — across repeated tests, real order reliably beat the frequency-preserving
shuffle). It is modest, it varies between clans, and it does not carry across
clans.

So: not "whale grammar" in any bold sense — but a small, honest signal that a few
clans put their codas in slightly non-random orders, in a way specific to each
clan. As far as the published literature shows, **no one has asked this particular
question before** — comparing the *ordering* of coda types across clans (prior
work compares clans by *which* codas they use, or studies ordering within a single
clan) — so even the modest answer is new ground.

## Honest limits

- The effect is **small** and clears the bar in only some clans, and is sensitive
  to how many coda types are included.
- The recordings are **limited** — a few thousand codas per clan — so faint
  signals are hard to measure precisely, and the cross-clan negative may be a
  power limit rather than a true absence.
- This says **nothing about meaning**: we ask whether order is *structured*, not
  what any coda "means."
- **The rhythm/tempo split has its own limits.** We only looked at single-whale
  runs (one whale's own codas), not the back-and-forth *between* whales, which may
  hold more structure. And a formal test of whether rhythm and tempo combine
  independently in sequence was **not answerable** on this data: one rhythm is 64%
  of all codas, so that test collapses to "match the common one" and learns
  nothing. We report that as a dead end rather than a result.

---

## Method (in detail, for both a curious reader and a reviewer)

This section is deliberately thorough: it should convince a specialist that the
methods were appropriate and correctly applied, while remaining readable by a
non-specialist. Acronyms are spelled out on first use. Every step below is
implemented in the repository (module names in `code font`).

### 1. The data and its structure

Two published, openly available sources, **both sperm whale, no other species**:

- **Caribbean clan "EC1"** — Gero, Whitehead & Rendell (2016), one Eastern
  Caribbean clan recorded off Dominica. ~3,900 codas after removing non-coda
  "NOISE" markers; **21 coda types**. (A larger curated version of the same clan,
  Sharma et al. 2024, ~8,700 codas, was inspected but not needed for the core
  result.)
- **7 Pacific clans** — Hersh et al. (2022), ~24,000 codas across clans REG, SH,
  FP, PALI, PO, RI, SI (**none is the Caribbean clan**), 54–85 types per clan.

Each dataset is a table with **one row per coda**, carrying: the **coda type**
(a categorical label), a **session identifier** (recording day, or Pacific
repertoire), and a **sequence index** giving the order codas were produced within
the record. Neither source provides sub-second timestamps, so "adjacent in time"
is operationalized as **adjacent in the sequence index within the same session**
(a gap in the index — e.g. a coda that was dropped — breaks the chain). A
transition is therefore a genuine **back-to-back pair of codas** in one recording,
and a "sequence" is a contiguous run of such codas (median ~8–10 long; a session
usually contains several runs). This is audited in `inventory.py` /
`data/inventory/`. Provenance and checksums are in `data/raw/PROVENANCE.md`;
the two no-license Pacific/Sharma files are fetched, not redistributed.

### 2. From recordings to a transition graph

For one clan, restricted to its top-15 types, we build an **n×n count matrix
`C`** (n = 15): `C[i, j]` = the number of times a coda of type *i* was immediately
followed by a coda of type *j*, over all back-to-back pairs. We then **row-
normalize** with add-one (Laplace) smoothing to get a **transition matrix `T`**:
`T[i, j]` ≈ the probability that type *i* is followed by type *j*. Smoothing keeps
empty rows from being undefined and is fixed once (never tuned). This is the
"who-follows-whom" object; it is *computed*, not given. (Code: `transitions.py`,
`hersh.py`.) The key sparsity statistic — transitions per cell — is reported for
every run, because with n²=225 cells and only a few thousand pairs it governs how
noisy everything is.

### 3. The re-identification problem = graph matching

Split a clan's sessions randomly into two halves and build a transition matrix for
each: `T_A` and `T_B`. Hide the type labels. The task is to find the relabelling
of types that best lines the two graphs up. Because both halves are the same clan,
the **correct answer is known**: each type should map back to itself (the
identity). We measure **accuracy** = the fraction of the 15 types mapped to
themselves.

Crucially, relabelling the coda types permutes **both the rows and the columns of
`T` at the same time** (type *i* is both a "from" and a "to"). So this is a
**graph-matching** problem — align two networks whose nodes (coda types) are the
meaningful units — not a geometry-alignment problem.

### 4. Why QAP, and why not Procrustes (and the MUSE connection)

The intellectual seed for this project is **MUSE** (*Multilingual Unsupervised and
Supervised Embeddings*, Facebook AI, 2017), which can translate words between two
languages **without a dictionary**: each language's words are first turned into a
cloud of points (an *embedding*) built separately per language, and MUSE finds a
single **rotation** that best overlays one cloud onto the other, so that
"dog"↔"chien" land on top of each other. The often-missed point is that MUSE does
**not create** the structure — the embeddings exist first, monolingually — it only
**aligns** two pre-existing structures. That is exactly why our honest first
question was whether coda types even *have* enough structural signature to be
aligned at all.

MUSE's alignment step is **Procrustes analysis** — the classic method for finding
the best **rotation/reflection** to overlay one set of points on another. Rotation
is the right move *there* because embedding axes are arbitrary: only the relative
geometry of the points carries meaning.

For our transition matrices, a rotation would be **wrong**. The axes are *not*
arbitrary — every row and column is indexed by a specific coda type. A rotation
would blend types into meaningless mixtures ("0.5 of `5R1` + 0.5 of `4D`"), which
do not exist. The only transformation that makes sense is a **permutation** — a
strict one-to-one relabelling — applied to rows and columns together. Finding the
permutation that makes one weighted network most resemble another is precisely the
**Quadratic Assignment Problem (QAP)** — a classic combinatorial-optimization
problem (Koopmans–Beckmann, 1957). So **QAP is the correct primary tool, and
Procrustes is not**, even though Procrustes is what the linguistic analogue (MUSE)
uses. (We *also* implemented a spectral-embedding + Procrustes route as the direct
MUSE analogue, for comparison; it is an approximate optimizer that gets trapped in
poor solutions even on clean test cases — consistent with the argument above — so
it is reported as a secondary check, never as ground truth. Code: `recover.py`.)

QAP with 15 types is too large to solve by brute force (15! ≈ 10¹²), so we use the
standard **FAQ** approximate solver (*Fast Approximate QAP*, Vogelstein et al.
2015), shipped in SciPy, run from many random starts and refined, reporting the
spread across starts rather than cherry-picking the best. We **verified our QAP
objective against exhaustive brute force** on small (≤7-type) synthetic problems —
this caught a genuine sign/convention bug (the naive call optimizes the *inverse*
permutation) that a self-consistency check would have missed. (Tests:
`tests/test_recover.py`.)

### 5. The controls, and which bar is the honest one

Three yardsticks, in increasing strictness:

- **Frequency-rank baseline** — match types by how common they are (rank the types
  in each half by frequency, pair rank-1 with rank-1, etc.). Uses **no** order
  information. We eventually found this bar **too lenient**: QAP can exploit more
  of the frequency structure than simple rank-matching, so passing the rank
  baseline is not enough.
- **Order-shuffled null (the real bar)** — the "shuffled" dataset above: permute
  type labels *within each session*, preserving every frequency and the sample
  size, destroying only order. Rebuild the whole pipeline and recover. Whatever
  recovery survives here is coming from frequency/composition, not sequence. This
  is the yardstick the final result is graded against.
- **Random-permutation floor** — accuracy under random relabellings; a sanity
  floor only.

All three are computed **within each clan** (the shuffle is within each session of
that clan) — never using frequencies pooled across clans.

### 6. The paired test and confidence intervals

For each of **30 random session-splits** of a clan we compute the recovery
accuracy on the **real** order and on a **shuffled** copy of *the same split*, and
take the difference (real − shuffled). Pairing on the same split cancels the fact
that some splits are simply easier than others. We then take the average
difference and put a **95% confidence interval (CI)** on it by **bootstrap**
(resampling the 30 differences 5,000 times). A **CI** is the range of values
consistent with the data given the noise: if the whole range sits **above zero**,
we conclude order reliably adds identity beyond frequency (the clan "survives").
This paired design is why the earlier, cruder comparison (observed mean vs. an
unpaired null's 95th percentile) was replaced — that mixed paired signal with
split-to-split variance and was not a valid test. (Code: `run_reaudit.py`;
per-clan numbers in `results/reaudit.csv`.)

### 6b. Robustness checks

Two targeted checks probe whether the surviving signal is what it appears to be —
both reproducible, both reported honestly including where they *complicate* the
story:

- **Is it just the dominant coda?** (`robustness.py`) Re-run the paired test on the
  Caribbean clan with the two most common codas removed. The effect *strengthens*
  (from +1.4 to +2.0 of 15) — the common codas are matched by frequency and add
  little to the difference — but it is sensitive to how many types are kept
  (dropping to 13 loses significance), a sign the effect is small.
- **Is it syntax or self-repetition?** (`syntax.py`) Re-run with self-repetition
  removed (the transition matrix's diagonal zeroed for both real and shuffled), so
  only "coda A → *different* coda B" structure remains. Genuine syntax survives in
  EC1 (much stronger: +7.8 of 15), SI (+3.3), and REG (+1.0); Pacific PO's
  full-matrix signal was **pure repetition** and vanishes; the rest stay null.
  This reorders which clans count as having real sequencing structure and is
  treated as the more meaningful cut in "Is it grammar, or just repetition?" above.

### 7. What we deliberately did *not* claim, and errors we caught

The honest history is in `PROGRESS.md`. In brief: earlier versions reported much
larger effects, inflated by (a) grading against the too-lenient rank baseline and
(b) split-halves that shared recordings (leaking structure between the two sides).
Two separate null-construction bugs were found and fixed along the way (nulls that
did not mirror their condition's split, producing impossibly high "chance"
levels). The strict, paired, disjoint-session re-audit in §6 supersedes all of it,
and the numbers above are what remains after those corrections.

### 8. The factored (rhythm, tempo, ornament, rubato) data model

A later refinement replaced the single categorical coda "type" with Sharma et
al.'s (2024) factored representation: each coda is a **rhythm** (1 of 18 click
patterns) and a **tempo** (1 of 5 duration classes), plus two context features,
**ornament** and **rubato**. We use the paper's *own* published labels (verified
against its cluster templates — rhythm match 100%, ornament rate 3.8% vs the
paper's ~4%) and its Dataset 2 (3,687 DTag codas with real onset times and speaker
IDs), de-pickled into a plain CSV so nothing in the pipeline unpickles.
(`coda_model.py`, `inventory_factored.py`; 64 of 90 rhythm×tempo cells attested.)

The **firewall** is unchanged: rhythm/tempo are the recovery *target* and are never
fed to the matcher, nor are duration, click count, or the raw intervals — only
transition counts between (rhythm, tempo) tokens. Transitions are built from
single-whale call sequences (same speaker, consecutive codas ≤ 8 s apart — the
paper's rule, now exact thanks to real timestamps).

Three experiments (`recover_factored.py`): (7.1) **joint** recovery over the
top-K (rhythm, tempo) cells; (7.3) **marginal** recovery of rhythm alone and tempo
alone — *which axis carries the signal?*; and (7.2) **factored** recovery under a
Kronecker-constrained permutation (relabel rhythms and tempos independently), whose
exhaustive solver is verified exact against a known relabelling in the tests. Only
tempo's marginal recovery clears the shuffle bar; the factored test is degenerate
here (rhythm-frequency skew — see Honest limits).

**Recovery vs prediction.** These experiments measure *re-identification* (matching
anonymized tokens across independent recordings by transition fingerprint), which
is strictly harder than *prediction* (guessing the next coda). `predictability.py`
quantifies the gap: next-coda prediction runs 75–85% (rhythm alone 82%), and
knowing the current coda beats base rates in every case — but that gain is mostly
**persistence** (repetition), which is uniform across tokens and therefore does not
make them re-identifiable. High predictability with low re-identifiability is the
expected signature of a system built on repetition plus a few dominant types.

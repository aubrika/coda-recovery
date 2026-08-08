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

The shuffled version is the honest yardstick: it is a "what if order didn't matter
at all?" copy of the same data. Anything the computer still recovers from the
shuffled data, it is getting **from frequency alone**. So the quantity that
actually answers our question is:

> **real − shuffled** = the part of the recovery that genuinely comes from order.

This also disposes of two worries at once. *Is it just the very common coda like*
`1+1+3`*?* No — the shuffled copy keeps `1+1+3` exactly as common, so if real beats
shuffled, it is beating that commonness. *Could a small dataset just look
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
- It is **not** about how much data we had: the clan with the *least* data (SI)
  showed the *strongest* effect. It seems to be a real difference between clans.
- **Across two different clans, the order does not transfer.** The sequencing that
  helps identify a coda inside its own clan tells you nothing about another clan.
  (This negative is itself limited by data — with only a few thousand codas per
  clan, a weak shared signal could be there and we would miss it — so we state it
  as "no evidence of transfer," not "proof of none.")

## What it means

Mostly, a sperm whale coda's identity lives in **how it sounds** and **how often
it's used** — not strongly in where it sits in a sequence. But there is a **faint,
real trace of sequential structure** in some clans, including the original one,
and it is **statistically distinguishable from both random guessing and
frequency-based guessing** (that is what "the confidence range clears zero"
means — across repeated tests, real order reliably beat the frequency-preserving
shuffle). It is subtle, it varies between clans, and it does not carry across
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

### 7. What we deliberately did *not* claim, and errors we caught

The honest history is in `PROGRESS.md`. In brief: earlier versions reported much
larger effects, inflated by (a) grading against the too-lenient rank baseline and
(b) split-halves that shared recordings (leaking structure between the two sides).
Two separate null-construction bugs were found and fixed along the way (nulls that
did not mirror their condition's split, producing impossibly high "chance"
levels). The strict, paired, disjoint-session re-audit in §6 supersedes all of it,
and the numbers above are what remains after those corrections.

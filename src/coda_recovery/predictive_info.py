"""Held-out bigram log-likelihood gain and recording-level uncertainty.

For changes-only scoring, both models exclude the current token. The frequency
baseline is fitted on ALL training destinations before conditioning on a change.
Filtering first would introduce dependence even in independent token sequences.
"""
from __future__ import annotations

from itertools import groupby

import numpy as np

SEQUENCE_GAP_S = 8.0
ALPHA = 0.5
NBOOT = 500
NFOLDS = 5


def single_whale_sequences(codas):
    """EC1 supplement: same speaker, consecutive onsets at most eight seconds apart."""
    cs = sorted(codas, key=lambda c: (c.deployment, c.speaker, c.t_start))
    out = []
    for _, grp in groupby(cs, key=lambda c: (c.deployment, c.speaker)):
        grp = list(grp)
        cur = [grp[0]]
        for prev, c in zip(grp, grp[1:]):
            if c.t_start - prev.t_start <= SEQUENCE_GAP_S:
                cur.append(c)
            else:
                out.append((cur[0].deployment, cur))
                cur = [c]
        out.append((cur[0].deployment, cur))
    return out


def pair_counts(pairs, vocab):
    index = {token: i for i, token in enumerate(vocab)}
    counts = np.zeros((len(vocab), len(vocab)), dtype=float)
    for _, a, b in pairs:
        counts[index[a], index[b]] += 1
    return counts


def log_gain_matrix(train, transition_only=False, baseline=None):
    """Cellwise log2(P_bigram / P_frequency).

    An optional baseline count matrix allows transfer models to use the target
    clan's training frequencies. All inputs include self-pairs. For a != b the
    conditional baseline is (n_b + alpha) / (N - n_a + alpha * (V - 1)).
    """
    baseline = train if baseline is None else baseline
    destinations = baseline.sum(axis=0) + ALPHA
    bigram = train + ALPHA
    frequency = np.broadcast_to(destinations, train.shape).copy()
    if transition_only:
        np.fill_diagonal(bigram, 0)
        np.fill_diagonal(frequency, 0)
    if len(train) < 2 and transition_only:
        return np.zeros_like(train)
    bigram = bigram / bigram.sum(axis=1, keepdims=True)
    frequency = frequency / frequency.sum(axis=1, keepdims=True)
    # Diagonal cells are not scored in the changes-only analysis.
    if transition_only:
        np.fill_diagonal(bigram, 1)
        np.fill_diagonal(frequency, 1)
    return np.log2(bigram / frequency)


def _gain(train, test, vocab, transition_only=False):
    """Per-pair held-out gains; retained as a small, directly testable primitive."""
    vocab = sorted(vocab, key=repr)
    index = {t: i for i, t in enumerate(vocab)}
    scores = log_gain_matrix(pair_counts(train, vocab), transition_only)
    return [float(scores[index[a], index[b]]) for _, a, b in test
            if not transition_only or a != b]


def recording_folds(units, seed=0):
    """Disjoint recording folds. A recording and all its bootstrap copies stay together."""
    if len(units) < 2:
        raise ValueError("Held-out scoring needs at least two recordings")
    return np.array_split(np.random.default_rng(seed).permutation(len(units)),
                          min(NFOLDS, len(units)))


def _crossfit(fold_counts):
    total = sum(fold_counts)
    sums = np.zeros(2)
    sizes = np.zeros(2)
    for test in fold_counts:
        train = total - test
        for k, changes_only in enumerate((False, True)):
            scored = test.copy()
            if changes_only:
                np.fill_diagonal(scored, 0)
            sums[k] += np.sum(scored * log_gain_matrix(train, changes_only))
            sizes[k] += scored.sum()
    return np.divide(sums, sizes, out=np.full(2, np.nan), where=sizes > 0)


def held_out_gain(all_pairs, n_boot=NBOOT, seed=0):
    """Five-fold recording CV, weighted by scored pairs, with cluster bootstrap.

    Resample whole recordings within each fixed fold and refit both models for
    every replicate. Percentile intervals are conditional on these folds and the
    supplied tokenization; they do not cover uncertainty from label construction.
    Return (total estimate/lo/hi), (changes estimate/lo/hi), pair count, vocab size.
    n_boot=0 computes point estimates only (bounds are NaN).
    """
    vocab = sorted({t for _, a, b in all_pairs for t in (a, b)}, key=repr)
    units = sorted({u for u, _, _ in all_pairs}, key=repr)
    folds = recording_folds(units, seed)
    unit_index = {u: i for i, u in enumerate(units)}
    token_index = {t: i for i, t in enumerate(vocab)}
    counts = np.zeros((len(units), len(vocab), len(vocab)))
    for u, a, b in all_pairs:
        counts[unit_index[u], token_index[a], token_index[b]] += 1
    point = _crossfit([counts[f].sum(axis=0) for f in folds])
    rng = np.random.default_rng(seed + 1)
    boot = []
    for _ in range(n_boot):
        boot.append(_crossfit([counts[rng.choice(f, len(f), replace=True)].sum(axis=0)
                              for f in folds]))
    bounds = np.full((2, 2), np.nan)
    if n_boot:
        for k in range(2):
            values = np.array(boot)[:, k]
            values = values[np.isfinite(values)]
            if len(values):
                bounds[:, k] = np.percentile(values, [2.5, 97.5])
    return ((float(point[0]), *bounds[:, 0]), (float(point[1]), *bounds[:, 1]),
            len(all_pairs), len(vocab))


def evaluate(mode, seqs, deps=None, rng_seed=0):
    """Native EC1 supplement, using the same scoring and bootstrap as the sweep."""
    tokfn = {"joint": lambda c: (c.rhythm, c.tempo),
             "rhythm": lambda c: c.rhythm, "tempo": lambda c: c.tempo}[mode]
    pairs = [(dep, tokfn(a), tokfn(b)) for dep, seq in seqs for a, b in zip(seq, seq[1:])]
    (mean, lo, hi), (change, clo, chi), n, v = held_out_gain(pairs, seed=rng_seed)
    return {"mode": mode, "n_tokens": v, "n_pairs": n,
            "self_repeat_frac": round(float(np.mean([a == b for _, a, b in pairs])), 3),
            "gain_bits": round(mean, 4), "gain_lo": round(lo, 4), "gain_hi": round(hi, 4),
            "gain_positive": bool(lo > 0), "gain_bits_nonself": round(change, 4),
            "nonself_lo": round(clo, 4), "nonself_hi": round(chi, 4),
            "nonself_positive": bool(clo > 0)}

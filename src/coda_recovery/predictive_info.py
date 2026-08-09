"""Mutual-information machinery + EC1 native-sequence evaluation.

Provides the shared held-out MI primitives used across the project — `_gain`
(cross-validated bigram-vs-unigram log-likelihood ratio, bits/coda), `ALPHA`, `NREP`
— and the EC1-only native-sequence helpers (`single_whale_sequences`, `evaluate`)
used by `ec1_pacified.py` to justify the uniform pipeline (it shows that measuring
EC1 with its richer native data makes it an artificial outlier).

The primary, cross-clan-comparable analysis does NOT use the native single-whale
segmentation here — it goes through `standardize.py` so every clan is treated the
same. This module is a library; it has no standalone entry point.

  gain (bits/coda) = mean over held-out pairs of  log2 P_bi(next|cur) − log2 P_uni(next)

A cross-validated estimate of the mutual information I(current; next) between
consecutive tokens: > 0 (CI clears zero) means the current coda predicts the next
beyond base rates. Immune to the diagonal-dominance problem that broke the retired
QAP metric, and needs no shuffle (the unigram IS the frequency null).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import groupby
from math import log2

import numpy as np

SEQUENCE_GAP_S = 8.0
ALPHA = 0.5          # add-alpha smoothing for the models
NREP = 40            # repeated train/test splits over deployments


def single_whale_sequences(codas):
    """List of (deployment, [codas]) — same speaker, consecutive <= 8 s apart.
    EC1-only (needs speaker IDs + onset times); used for the native-vs-uniform check."""
    cs = sorted(codas, key=lambda c: (c.deployment, c.speaker, c.t_start))
    out = []
    for _, grp in groupby(cs, key=lambda c: (c.deployment, c.speaker)):
        grp = list(grp)
        cur = [grp[0]]
        for prev, c in zip(grp, grp[1:]):
            if c.t_start - prev.t_start <= SEQUENCE_GAP_S:
                cur.append(c)
            else:
                out.append((cur[0].deployment, cur)); cur = [c]
        out.append((cur[0].deployment, cur))
    return out


def _tokfn(mode):
    return {"joint": lambda c: (c.rhythm, c.tempo),
            "rhythm": lambda c: c.rhythm, "tempo": lambda c: c.tempo}[mode]


def _pairs(seqs, tokfn):
    """(deployment, tok_a, tok_b) for adjacent codas within each sequence."""
    out = []
    for dep, seq in seqs:
        toks = [tokfn(c) for c in seq]
        for a, b in zip(toks, toks[1:]):
            out.append((dep, a, b))
    return out


def _gain(train, test, vocab, transition_only=False):
    """Held-out mean log2 likelihood-ratio (bigram vs unigram), bits/coda.

    transition_only=False: all pairs — total predictive information (includes the
        whales' heavy self-repetition, which is legitimate order-dependence).
    transition_only=True: train AND test on non-self pairs (a!=b) — isolates
        genuine "given a change, does the source predict the destination beyond the
        base rate of destinations?" (Training on non-self is essential: the full
        bigram spends its mass on the diagonal, so it would under-predict any
        change purely as an artefact.)"""
    if transition_only:
        train = [p for p in train if p[1] != p[2]]
        test = [p for p in test if p[1] != p[2]]
    V = len(vocab)
    uni = Counter(b for _, _, b in train); Nu = sum(uni.values())
    bi = defaultdict(Counter); rowsum = Counter()
    for _, a, b in train:
        bi[a][b] += 1; rowsum[a] += 1
    g = []
    for _, a, b in test:
        p_uni = (uni[b] + ALPHA) / (Nu + ALPHA * V)
        p_bi = (bi[a][b] + ALPHA) / (rowsum[a] + ALPHA * V)
        g.append(log2(p_bi) - log2(p_uni))
    return g


def evaluate(mode, seqs, deps, rng_seed=0):
    """EC1 native single-whale within-clan MI (total + transition-only), for the
    native-vs-uniform comparison in `ec1_pacified.py`."""
    tokfn = _tokfn(mode)
    vocab = {tokfn(c) for _, seq in seqs for c in seq}
    all_pairs = _pairs(seqs, tokfn)
    self_frac = np.mean([a == b for _, a, b in all_pairs])
    rng = np.random.default_rng(rng_seed)
    fold_gain_all, fold_gain_off = [], []
    for r in range(NREP):
        d = deps.copy(); rng.shuffle(d)
        te = set(d[:max(1, len(d) // 3)])
        train = [p for p in all_pairs if p[0] not in te]
        test = [p for p in all_pairs if p[0] in te]
        if not test or not train:
            continue
        fold_gain_all.append(np.mean(_gain(train, test, vocab, transition_only=False)))
        goff = _gain(train, test, vocab, transition_only=True)
        fold_gain_off.append(np.mean(goff) if goff else np.nan)

    def ci(x):
        x = np.array([v for v in x if np.isfinite(v)])
        bs = [np.mean(rng.choice(x, len(x), replace=True)) for _ in range(4000)]
        return float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

    m_all, lo_all, hi_all = ci(fold_gain_all)
    m_off, lo_off, hi_off = ci(fold_gain_off)
    return {"mode": mode, "n_tokens": len(vocab), "n_pairs": len(all_pairs),
            "self_repeat_frac": round(float(self_frac), 3),
            "gain_bits": round(m_all, 4), "gain_lo": round(lo_all, 4), "gain_hi": round(hi_all, 4),
            "gain_positive": bool(lo_all > 0),
            "gain_bits_nonself": round(m_off, 4), "nonself_lo": round(lo_off, 4),
            "nonself_hi": round(hi_off, 4), "nonself_positive": bool(lo_off > 0)}

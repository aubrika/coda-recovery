"""Predictive-information test — EC1 native single-whale SUPPLEMENT.

This measures EC1's within-clan predictive information using its *richer* native
data: the paper's own rhythm/tempo labels and true single-whale sequences (known
speakers, real onset times, ≤ 8 s apart). That is more precise than the uniform
cross-clan pipeline but NOT comparable to the Pacific clans, which lack speaker IDs
— so it is a supplement, not the headline. The primary, apples-to-apples within-clan
result (EC1 put through the same pipeline as everyone else) is in
`predictive_info_sweep.py`; `ec1_pacified.py` shows how much the two differ. This
module also provides the shared MI machinery (`_gain`, `ALPHA`, `NREP`,
`single_whale_sequences`) used across the project.

The question is "does the previous coda predict the next, beyond frequency?" We
answer it directly, with no alignment and no shuffle (both of which introduced
artefacts): a cross-validated likelihood-ratio between a bigram model
P(next | current) and a unigram model P(next), on held-out data.

  gain (bits/coda) = mean over held-out pairs of  log2 P_bi(next|cur) − log2 P_uni(next)

This is the held-out (bias-free) estimate of the mutual information I(current;next)
between consecutive (rhythm, tempo) tokens. gain > 0 (CI clears zero) means the
current coda genuinely predicts the next beyond base rates — cross-validated, so
overfitting can only *lower* it. It is immune to the diagonal-dominance problem
that broke the QAP metric (a likelihood, not a matrix alignment) and needs no
shuffle-scale choice (the unigram IS the frequency null).

Tokens are the factored (rhythm, tempo) representation (ornament and rubato left
out, per request). We report the joint token and each axis alone, and split the
gain into its persistence part (self-repeats) and its genuine-transition part.

Run:  python -m coda_recovery.predictive_info
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from itertools import groupby
from math import log2
from pathlib import Path

import numpy as np

from .coda_model import load

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "predictive_info.csv"
SEQUENCE_GAP_S = 8.0
ALPHA = 0.5          # add-alpha smoothing for the models
NREP = 40            # repeated train/test splits over deployments


def single_whale_sequences(codas):
    """List of (deployment, [codas]) — same speaker, consecutive <= 8 s apart."""
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


def main():
    codas = load()
    seqs = single_whale_sequences(codas)
    deps = np.array(sorted({dep for dep, _ in seqs}), dtype=object)
    print("Predictive information — held-out bigram vs unigram (bits/coda), "
          "single-whale sequences.\n")
    print(f"{'token':<8}{'#tok':>5}{'pairs':>7}{'self%':>7}"
          f"{'gain (95% CI)':>26}{'gain|non-self (95% CI)':>28}")
    rows = []
    for mode in ("joint", "rhythm", "tempo"):
        r = evaluate(mode, seqs, deps)
        rows.append(r)
        print(f"{mode:<8}{r['n_tokens']:>5}{r['n_pairs']:>7}{r['self_repeat_frac']*100:>6.0f}%"
              + f"{r['gain_bits']:+.4f} [{r['gain_lo']:+.4f},{r['gain_hi']:+.4f}]".rjust(26)
              + f"{r['gain_bits_nonself']:+.4f} [{r['nonself_lo']:+.4f},{r['nonself_hi']:+.4f}]".rjust(28))
    print("\ngain>0 = the current (rhythm,tempo) token predicts the next beyond frequency,")
    print("cross-validated. 'non-self' removes repeats: genuine A->different-B structure.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

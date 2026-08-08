"""Predictability vs re-identifiability — the distinction behind the factored
results. Recovery (elsewhere) asks whether an anonymized token can be re-matched
across two independent recordings by its transition fingerprint. This asks the
easier, different question: given the current coda, how well can you PREDICT the
next one? A system can be highly predictable (everyone repeats; one type is
common) yet un-recoverable (no token has a distinctive fingerprint).

Held-out by deployment (2/3 train, 1/3 test). Three predictors:
  marginal    — always guess the single most common token (base rate)
  persistence — guess "the next token repeats the current one"
  bigram      — guess argmax P(next | current) learned on train

bigram − marginal = how much knowing the CURRENT coda helps, beyond base rates.

Run:  python -m coda_recovery.predictability
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .recover_factored import factored_df, single_whale_sequences, _tokfn

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "predictability.csv"
NTRIALS = 20


def predictability(seqs, deps, mode):
    tokfn = _tokfn(mode)
    marg, pers, big, gain = [], [], [], []
    top_share = None
    for s in range(NTRIALS):
        rng = np.random.default_rng(s)
        d = deps.copy(); rng.shuffle(d)
        tr = set(d[: len(d) * 2 // 3]); te = set(d[len(d) * 2 // 3:])
        seqtr = [[tokfn(r) for r in seq] for seq in seqs if seq[0]["deployment"] in tr]
        seqte = [[tokfn(r) for r in seq] for seq in seqs if seq[0]["deployment"] in te]
        marg_counts = Counter(t for seq in seqtr for t in seq)
        top = marg_counts.most_common(1)[0][0]
        bg = defaultdict(Counter)
        for seq in seqtr:
            for a, b in zip(seq[:-1], seq[1:]):
                bg[a][b] += 1
        pred = {a: c.most_common(1)[0][0] for a, c in bg.items()}
        n = cm = cp = cb = 0
        for seq in seqte:
            for a, b in zip(seq[:-1], seq[1:]):
                n += 1
                cm += (b == top); cp += (b == a); cb += (b == pred.get(a, top))
        marg.append(cm / n); pers.append(cp / n); big.append(cb / n); gain.append((cb - cm) / n)
    all_counts = Counter(tokfn(r) for seq in seqs for r in seq)
    tot = sum(all_counts.values())
    return {
        "mode": mode, "n_tokens": len(all_counts),
        "top_token_share": round(all_counts.most_common(1)[0][1] / tot, 3),
        "marginal": round(float(np.mean(marg)), 3),
        "persistence": round(float(np.mean(pers)), 3),
        "bigram": round(float(np.mean(big)), 3),
        "bigram_minus_marginal": round(float(np.mean(gain)), 3),
        "gain_std": round(float(np.std(gain)), 3),
    }


def main():
    df = factored_df()
    seqs = single_whale_sequences(df)
    deps = df["deployment"].unique()
    rows = [predictability(seqs, deps, m) for m in ("rhythm", "tempo", "joint")]
    print("Next-coda predictability (held-out), single-whale sequences:\n")
    print(f"{'mode':<8}{'#tok':>6}{'top%':>7}{'marginal':>10}{'persist':>9}"
          f"{'bigram':>8}{'bigram−marg':>13}")
    for r in rows:
        print(f"{r['mode']:<8}{r['n_tokens']:>6}{r['top_token_share']*100:>6.0f}%"
              f"{r['marginal']:>10.3f}{r['persistence']:>9.3f}{r['bigram']:>8.3f}"
              f"{r['bigram_minus_marginal']:>+10.3f}±{r['gain_std']:.3f}")
    print("\nAll three are highly PREDICTABLE and the current coda helps (bigram > "
          "marginal). But that gain is mostly persistence (repetition), which is\n"
          "uniform across tokens — which is why it does NOT make tokens re-identifiable"
          " (see recover_factored: only tempo is recoverable).")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

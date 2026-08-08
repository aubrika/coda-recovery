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
    nr_baseacc, nr_srcacc, nr_frac = [], [], []
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
        # non-repeat model: where does a CHANGE go? (bigram over a!=b only)
        bg_nr = defaultdict(Counter); destc = Counter()
        for seq in seqtr:
            for a, b in zip(seq[:-1], seq[1:]):
                if a != b:
                    bg_nr[a][b] += 1; destc[b] += 1
        pred_nr = {a: c.most_common(1)[0][0] for a, c in bg_nr.items()}
        topdest = destc.most_common(1)[0][0]
        n = cm = cp = cb = 0
        nrn = nr_base = nr_src = 0
        for seq in seqte:
            for a, b in zip(seq[:-1], seq[1:]):
                n += 1
                cm += (b == top); cp += (b == a); cb += (b == pred.get(a, top))
                if a != b:
                    nrn += 1
                    nr_base += (b == topdest); nr_src += (b == pred_nr.get(a, topdest))
        marg.append(cm / n); pers.append(cp / n); big.append(cb / n); gain.append((cb - cm) / n)
        nr_baseacc.append(nr_base / nrn); nr_srcacc.append(nr_src / nrn); nr_frac.append(nrn / n)
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
        "nonrepeat_frac": round(float(np.mean(nr_frac)), 3),
        "nonrepeat_baserate": round(float(np.mean(nr_baseacc)), 3),
        "nonrepeat_sourceaware": round(float(np.mean(nr_srcacc)), 3),
        "nonrepeat_gain": round(float(np.mean(nr_srcacc) - np.mean(nr_baseacc)), 3),
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
    print("\nNON-REPEAT (where does a CHANGE go?): current coda still helps every axis")
    print(f"{'mode':<8}{'%change':>8}{'base-rate':>11}{'source-aware':>14}{'gain':>8}")
    for r in rows:
        print(f"{r['mode']:<8}{r['nonrepeat_frac']*100:>7.0f}%{r['nonrepeat_baserate']:>11.3f}"
              f"{r['nonrepeat_sourceaware']:>14.3f}{r['nonrepeat_gain']:>+8.3f}")
    print("\nAll three are PREDICTABLE, and the current coda helps even for NON-repeats "
          "(genuine A->B structure in every axis). But prediction != re-identification:\n"
          "rhythm's structure is weak (+0.15), smeared over 18 noisy categories, so it "
          "does NOT re-identify; tempo's is stronger (+0.26), in 5 clean categories, and\n"
          "directional (rubato) — the only axis that recovers (see recover_factored).")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

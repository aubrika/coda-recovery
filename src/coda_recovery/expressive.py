"""Additive experiment: do ORNAMENT and RUBATO add predictive information on top of
(rhythm, tempo)? This EXTENDS the mutual-information method to the paper's two
context features without touching the (rhythm, tempo) results, which stay the
distinct 'classical coda type' section.

Generalised held-out MI: the predictor (current coda) and the target (next coda)
can each be any subset of {rhythm, tempo, ornament, rubato}. All numbers are
cross-validated bits/coda (held-out bigram vs unigram), as before.

Two questions:
  1. ADDITIVE — predict the next coda's (rhythm, tempo) from the current one.
     Baseline predictor = current (rhythm, tempo). Then add the current coda's
     ornament and/or rubato and measure the paired gain. > 0 = the expressive
     features carry extra sequential information about the next call's identity.
  2. Do the expressive features have their OWN sequential structure — does the
     current coda predict the NEXT coda's ornament / rubato?

CAVEAT (inherited from the data model, coda-4d-data-model.md 3): ornament and
rubato are CONTEXT features — ornament is defined by click-count vs neighbours,
rubato by duration change vs the previous same-(rhythm,tempo) coda. So conditioning
on them partly conditions on local sequence facts by construction; a positive gain
is partly "these features encode neighbourhood," which we state rather than hide.

Run:  python -m coda_recovery.expressive
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .coda_model import load
from .predictive_info import single_whale_sequences, ALPHA, NREP

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "expressive.csv"

# feature tokenizers on a Coda
RT = lambda c: (c.rhythm, c.tempo)
RTO = lambda c: (c.rhythm, c.tempo, c.ornament)
RTR = lambda c: (c.rhythm, c.tempo, c.rubato_dir)
RTOR = lambda c: (c.rhythm, c.tempo, c.ornament, c.rubato_dir)
ORN = lambda c: c.ornament
RUB = lambda c: c.rubato_dir


def coda_pairs(codas):
    return [(dep, a, b) for dep, seq in single_whale_sequences(codas)
            for a, b in zip(seq, seq[1:])]


def fold_gains(pairs, cur_tok, next_tok, split_seed=0):
    """Per-fold held-out MI (bits/coda). Same split_seed -> aligned folds, so gains
    for different predictors are PAIRED and their difference has a valid CI."""
    units = sorted({u for u, _, _ in pairs}, key=str)
    V = len({next_tok(b) for _, _, b in pairs})
    rng = np.random.default_rng(split_seed)
    out = []
    for _ in range(NREP):
        u = np.array(units, dtype=object); rng.shuffle(u)
        te = set(u[:max(1, len(u) // 3)])
        train = [(cur_tok(a), next_tok(b)) for un, a, b in pairs if un not in te]
        test = [(cur_tok(a), next_tok(b)) for un, a, b in pairs if un in te]
        uni = Counter(y for _, y in train); Nu = sum(uni.values())
        bi = defaultdict(Counter); rs = Counter()
        for x, y in train:
            bi[x][y] += 1; rs[x] += 1
        g = [np.log2((bi[x][y] + ALPHA) / (rs.get(x, 0) + ALPHA * V))
             - np.log2((uni[y] + ALPHA) / (Nu + ALPHA * V)) for x, y in test]
        out.append(float(np.mean(g)) if g else np.nan)
    return np.array(out)


def _ci(x, seed=0):
    x = x[np.isfinite(x)]
    rng = np.random.default_rng(seed)
    bs = [np.mean(rng.choice(x, len(x), replace=True)) for _ in range(4000)]
    return float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    pairs = coda_pairs(load())
    rows = []

    print("ADDITIVE — predict the NEXT coda's (rhythm,tempo). Does adding the current")
    print("coda's ornament / rubato to the predictor help, beyond current (rhythm,tempo)?\n")
    base = fold_gains(pairs, RT, RT)
    bm, bl, bh = _ci(base)
    print(f"  {'predictor':<26}{'MI (95% CI)':>22}{'gain over base (95% CI)':>28}")
    print(f"  {'(rhythm,tempo)  [base]':<26}" + f"{bm:+.3f} [{bl:+.3f},{bh:+.3f}]".rjust(22))
    rows.append({"experiment": "predict_next_RT", "predictor": "RT", "mi": round(bm, 4),
                 "mi_lo": round(bl, 4), "mi_hi": round(bh, 4), "gain": 0.0,
                 "gain_lo": 0.0, "gain_hi": 0.0, "gain_positive": False})
    for name, tok in [("+ ornament", RTO), ("+ rubato", RTR), ("+ ornament + rubato", RTOR)]:
        g = fold_gains(pairs, tok, RT)
        gm, gl, gh = _ci(g)
        dm, dl, dh = _ci(g - base)
        print(f"  {'(rhythm,tempo) ' + name:<26}" + f"{gm:+.3f} [{gl:+.3f},{gh:+.3f}]".rjust(22)
              + f"{dm:+.3f} [{dl:+.3f},{dh:+.3f}]".rjust(28) + ("  *" if dl > 0 else ""))
        rows.append({"experiment": "predict_next_RT", "predictor": name.strip("+ ").replace(" ", "_"),
                     "mi": round(gm, 4), "mi_lo": round(gl, 4), "mi_hi": round(gh, 4),
                     "gain": round(dm, 4), "gain_lo": round(dl, 4), "gain_hi": round(dh, 4),
                     "gain_positive": bool(dl > 0)})

    print("\nSEQUENTIAL STRUCTURE OF THE EXPRESSIVE FEATURES THEMSELVES")
    for tgt_name, tgt in [("next ornament", ORN), ("next rubato", RUB)]:
        gr = fold_gains(pairs, RT, tgt)
        gf = fold_gains(pairs, RTOR, tgt)
        rm, rl, rh = _ci(gr); fm, fl, fh = _ci(gf)
        print(f"  predict {tgt_name}:  from current (rhythm,tempo) = "
              f"{rm:+.3f} [{rl:+.3f},{rh:+.3f}] bits ;  from full current token = "
              f"{fm:+.3f} [{fl:+.3f},{fh:+.3f}] bits")
        rows.append({"experiment": f"predict_{tgt_name.replace(' ', '_')}", "predictor": "RT",
                     "mi": round(rm, 4), "mi_lo": round(rl, 4), "mi_hi": round(rh, 4),
                     "gain": "", "gain_lo": "", "gain_hi": "", "gain_positive": bool(rl > 0)})
        rows.append({"experiment": f"predict_{tgt_name.replace(' ', '_')}", "predictor": "RTOR",
                     "mi": round(fm, 4), "mi_lo": round(fl, 4), "mi_hi": round(fh, 4),
                     "gain": "", "gain_lo": "", "gain_hi": "", "gain_positive": bool(fl > 0)})

    print("\nNote: ornament/rubato are context features (defined via neighbours), so a")
    print("gain is partly neighbourhood-encoding, not purely new structure — see header.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

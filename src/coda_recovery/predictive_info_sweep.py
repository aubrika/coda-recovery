"""Predictive-information (mutual-information) sweep — held-out MI within every clan.

MI = mutual information: the held-out bigram-vs-unigram log-likelihood gain is a
cross-validated estimate of I(current token; next token), in bits/coda. Positive
(CI clears 0) = the current coda predicts the next beyond frequency.

All 8 clans — EC1 and the 7 Pacific clans — go through the *same* `standardize`
pipeline (nearest-template rhythm, per-clan quantile tempo, adjacent within-recording
pairs, speakers pooled), using only data both datasets share. No clan is measured
more cleanly than another, so the numbers are directly comparable.

Tokens: tempo, rhythm, joint (rhythm,tempo). Reports total MI and transition-only MI
(repeats removed).

Run:  python -m coda_recovery.predictive_info_sweep
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .predictive_info import _gain, NREP
from .standardize import clan_frame, pooled_pairs, token_fn, ALL_CLANS

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "predictive_info_sweep.csv"


def _ci(x, rng):
    x = np.array([v for v in x if np.isfinite(v)])
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    bs = [np.mean(rng.choice(x, len(x), replace=True)) for _ in range(3000)]
    return float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def held_out_mi(all_pairs):
    """all_pairs: list of (cv_unit, tok_a, tok_b). Returns total & transition MI."""
    vocab = {a for _, a, _ in all_pairs} | {b for _, _, b in all_pairs}
    units = sorted({u for u, _, _ in all_pairs}, key=str)
    rng = np.random.default_rng(0)
    ga, gt = [], []
    for r in range(NREP):
        u = np.array(units, dtype=object); rng.shuffle(u)
        te = set(u[:max(1, len(u) // 3)])
        train = [p for p in all_pairs if p[0] not in te]
        test = [p for p in all_pairs if p[0] in te]
        if not train or not test:
            continue
        ga.append(np.mean(_gain(train, test, vocab, transition_only=False)))
        g = _gain(train, test, vocab, transition_only=True)
        gt.append(np.mean(g) if g else np.nan)
    return _ci(ga, rng), _ci(gt, rng), len(all_pairs), len(vocab)


def main():
    rows = []
    print("Mutual information (held-out bits/coda). total | transition-only (repeats removed)")
    print("Uniform pipeline — all 8 clans treated identically.\n")
    print(f"{'dataset':<10}{'token':<8}{'pairs':>6}"
          f"{'MI total (95% CI)':>24}{'MI transition (95% CI)':>26}")
    for clan in ALL_CLANS:
        label = clan if clan == "EC1" else f"PAC:{clan}"
        frame = clan_frame(clan, tempo="qcut")
        for token in ("tempo", "rhythm", "joint"):
            (mt, ml, mh), (tt, tl, th), n, V = held_out_mi(pooled_pairs(frame, token_fn(token)))
            rows.append({"dataset": label, "mode": "within", "token": token, "pairs": n,
                         "mi_total": round(mt, 3), "total_lo": round(ml, 3), "total_hi": round(mh, 3),
                         "mi_transition": round(tt, 3), "trans_lo": round(tl, 3), "trans_hi": round(th, 3),
                         "total_pos": bool(ml > 0), "transition_pos": bool(tl > 0)})
            print(f"{label:<10}{token:<8}{n:>6}"
                  + f"{mt:+.3f} [{ml:+.3f},{mh:+.3f}]".rjust(24)
                  + f"{tt:+.3f} [{tl:+.3f},{th:+.3f}]".rjust(26))
        print()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

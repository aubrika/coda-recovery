"""Predictive-information (mutual-information) sweep — the clean MI test extended
to the between-whale exchange and to every Pacific clan.

MI = mutual information: the held-out bigram-vs-unigram log-likelihood gain is a
cross-validated estimate of I(current token; next token), in bits/coda. Positive
(CI clears 0) = the current coda predicts the next beyond frequency.

  EC1 (Sharma Dataset 2, real times + speakers):
    within  — same whale, consecutive <= 8 s
    between — different whales, turn-taking (next onset within 2 s after prev end)
    pooled  — all adjacent-in-time pairs within 2 s
  Pacific clans (Hersh): within-repertoire (no speaker IDs), rhythm/tempo derived.

Tokens: tempo, rhythm, joint (rhythm,tempo). Reports total MI and transition-only
MI (repeats removed).

Run:  python -m coda_recovery.predictive_info_sweep
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from .predictive_info import _gain, single_whale_sequences, NREP
from .coda_model import load
from .factored import prep_clan, load_templates
from .hersh import load_hersh, CLANS

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "predictive_info_sweep.csv"


def _tf(mode):
    return {"tempo": lambda c: c.tempo, "rhythm": lambda c: c.rhythm,
            "joint": lambda c: (c.rhythm, c.tempo)}[mode]


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


# ---- pair generators -> (cv_unit, tok_a, tok_b) --------------------------

def ec1_within(codas, tf):
    return [(dep, tf(a), tf(b)) for dep, seq in single_whale_sequences(codas)
            for a, b in zip(seq, seq[1:])]


def ec1_time_adjacent(codas, tf, between_only):
    out = []
    by = defaultdict(list)
    for c in codas:
        by[c.deployment].append(c)
    for dep, cs in by.items():
        cs = sorted(cs, key=lambda c: c.t_start)
        for a, b in zip(cs, cs[1:]):
            gap = b.t_start - (a.t_start + a.duration)
            if not (0 <= gap <= 2):
                continue
            if between_only and a.speaker == b.speaker:
                continue
            out.append((dep, tf(a), tf(b)))
    return out


def pacific_within(sub, tf):
    out = []
    for grp, g in sub.sort_values(["grpvar", "coda_number"]).groupby("grpvar"):
        rows = list(g.itertuples())
        for a, b in zip(rows, rows[1:]):
            if b.coda_number - a.coda_number <= 1:
                out.append((grp, tf(a), tf(b)))
    return out


def main():
    rows = []
    print("Mutual information (held-out bits/coda). total | transition-only (repeats removed)\n")
    print(f"{'dataset':<10}{'mode':<9}{'token':<8}{'pairs':>6}"
          f"{'MI total (95% CI)':>24}{'MI transition (95% CI)':>26}")

    def emit(dataset, mode, token, pairs):
        (mt, ml, mh), (tt, tl, th), n, V = held_out_mi(pairs)
        rows.append({"dataset": dataset, "mode": mode, "token": token, "pairs": n,
                     "mi_total": round(mt, 3), "total_lo": round(ml, 3), "total_hi": round(mh, 3),
                     "mi_transition": round(tt, 3), "trans_lo": round(tl, 3), "trans_hi": round(th, 3),
                     "total_pos": bool(ml > 0), "transition_pos": bool(tl > 0)})
        print(f"{dataset:<10}{mode:<9}{token:<8}{n:>6}"
              + f"{mt:+.3f} [{ml:+.3f},{mh:+.3f}]".rjust(24)
              + (f"{tt:+.3f} [{tl:+.3f},{th:+.3f}]".rjust(26) if np.isfinite(tt) else "  —".rjust(26)))

    codas = load()
    print("--- EC1 (Dataset 2) ---")
    for mode, gen in [("within", lambda tf: ec1_within(codas, tf)),
                      ("between", lambda tf: ec1_time_adjacent(codas, tf, True)),
                      ("pooled", lambda tf: ec1_time_adjacent(codas, tf, False))]:
        for token in ("tempo", "rhythm", "joint"):
            emit("EC1", mode, token, gen(_tf(token)))
        print()

    print("--- Pacific clans (within-repertoire) ---")
    templates = load_templates()
    h = load_hersh()
    for clan in CLANS:
        sub = prep_clan(h[h.clan_name == clan], templates)
        for token in ("tempo", "rhythm", "joint"):
            emit(f"PAC:{clan}", "within", token, pacific_within(sub, _tf(token)))
        print()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

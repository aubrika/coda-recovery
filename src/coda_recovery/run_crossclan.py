"""Cross-clan gradeable alignment (Phase 2) — the real test.

For each pair of Pacific clans, restrict to their top-k shared coda types, build
a transition graph for each clan independently, and ask whether QAP can recover
the KNOWN type correspondence (identity over the shared index) from transition
structure alone — beating the frequency baseline and a strong (order-shuffled)
null. Success means combinatorial role is conserved across clans that use the
same acoustic types with different dialect/frequency.
"""
from __future__ import annotations

import csv
import itertools
from pathlib import Path

import numpy as np

from .hersh import (
    load_hersh, CLANS, shared_top_types, clan_transition,
    shuffle_types_within_repertoire, clan_pairs,
)
from .recover import (
    qap_recover, frequency_rank_baseline, accuracy_at_1, freq_weighted_accuracy,
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "crossclan.csv"
ALPHA = 1.0
K = 20                    # shared types per pair (density control)
QAP_RESTARTS = 30
NULL_REPS = 25


def run_pair(df, ca, cb, k=K, seed=0):
    types = shared_top_types(df, ca, cb, k)
    n = len(types)
    Ca, Ta = clan_transition(df, ca, types, ALPHA)
    Cb, Tb = clan_transition(df, cb, types, ALPHA)
    dens = 0.5 * (Ca.sum() + Cb.sum()) / (n * n)

    rec = qap_recover(Ta, Tb, n_restarts=QAP_RESTARTS, seed=seed)
    qap_acc = accuracy_at_1(rec.perm)             # truth = identity over shared idx
    w = Ca.sum(0) + Ca.sum(1) + Cb.sum(0) + Cb.sum(1)
    qap_fw = freq_weighted_accuracy(rec.perm, w.astype(float))
    base = accuracy_at_1(frequency_rank_baseline(Ca, Cb))

    null = []
    for i in range(NULL_REPS):
        sa = shuffle_types_within_repertoire(df, ca, types, 500 + i)
        sb = shuffle_types_within_repertoire(df, cb, types, 900 + i)
        # rebuild transitions from the shuffled clan subsets
        na, _ = _counts(sa, types); nb, _ = _counts(sb, types)
        from .transitions import row_normalise
        nr = qap_recover(row_normalise(na, ALPHA), row_normalise(nb, ALPHA),
                         n_restarts=8, seed=seed, refine_2opt=False)
        null.append(accuracy_at_1(nr.perm))
    null = np.array(null)
    return {
        "clan_a": ca, "clan_b": cb, "n_shared_types": n,
        "trans_per_cell": round(dens, 2),
        "qap_acc": round(qap_acc, 4), "qap_freq_weighted": round(qap_fw, 4),
        "baseline_acc": round(base, 4),
        "null_mean": round(float(null.mean()), 4),
        "null_p95": round(float(np.percentile(null, 95)), 4),
        "beats_baseline": bool(qap_acc > base),
        "beats_null": bool(qap_acc > np.percentile(null, 95)),
    }


def within_clan_easy(df, clan, k, nseeds=10, seed0=0):
    """Positive control / base-case replication on one Pacific clan: build the
    real-order adjacent-pair pool, randomly split the PAIRS in half (both halves
    sample the same sequences — the easiest rung), recover, grade vs identity.
    This is what must work if the pipeline is sound; the cross-clan null is only
    interpretable against it."""
    freq = df[df.clan_name == clan].coda_type.value_counts()
    types = freq.head(k).index.tolist()
    idx = {t: i for i, t in enumerate(types)}
    pr = clan_pairs(df, clan, types, 1)
    A, B = pr["a"].to_numpy(), pr["b"].to_numpy()
    qap, base = [], []
    for s in range(seed0, seed0 + nseeds):
        rng = np.random.default_rng(s)
        half = rng.integers(0, 2, len(A))
        Ca = np.zeros((k, k)); Cb = np.zeros((k, k))
        for x, y, h in zip(A, B, half):
            (Ca if h == 0 else Cb)[idx[x], idx[y]] += 1
        from .transitions import row_normalise
        rec = qap_recover(row_normalise(Ca, ALPHA), row_normalise(Cb, ALPHA),
                          n_restarts=25, seed=s)
        qap.append(accuracy_at_1(rec.perm))
        base.append(accuracy_at_1(frequency_rank_baseline(Ca, Cb)))
    return {"clan": clan, "k": k, "codas_pairs": len(A),
            "trans_per_cell": round(0.5 * len(A) / k ** 2, 2),
            "qap_acc": round(float(np.mean(qap)), 4),
            "baseline_acc": round(float(np.mean(base)), 4)}


def _counts(sub, types):
    """Count matrix from an already-subset/shuffled clan frame (grpvar order)."""
    idx = {t: i for i, t in enumerate(types)}
    n = len(types)
    C = np.zeros((n, n), dtype=np.int64)
    s = sub.sort_values(["grpvar", "coda_number"])
    a = s.iloc[:-1]; b = s.iloc[1:]
    same = a["grpvar"].to_numpy() == b["grpvar"].to_numpy()
    contig = (b["coda_number"].to_numpy() - a["coda_number"].to_numpy()) <= 1
    keep = same & contig
    for x, y in zip(a["coda_type"].to_numpy()[keep], b["coda_type"].to_numpy()[keep]):
        C[idx[x], idx[y]] += 1
    return C, None


def main():
    df = load_hersh()

    # --- positive control: within-clan base-case replication (easy split) ---
    print("===== WITHIN-CLAN replication (easy split, top-15 types) =====")
    print(f"{'clan':<8}{'pairs':>7}{'t/cell':>8}{'QAP':>7}{'base':>7}")
    within = []
    for clan in CLANS:
        w = within_clan_easy(df, clan, k=15)
        within.append(w)
        print(f"{clan:<8}{w['codas_pairs']:>7}{w['trans_per_cell']:>8}"
              f"{w['qap_acc']:>7.2f}{w['baseline_acc']:>7.2f}")
    wq = np.mean([w["qap_acc"] for w in within])
    wb = np.mean([w["baseline_acc"] for w in within])
    print(f"  mean: QAP={wq:.3f}  baseline={wb:.3f}  -> position recovers type "
          f"WITHIN a clan\n")
    with (REPO / "results" / "within_pacific.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(within[0].keys()))
        wr.writeheader(); wr.writerows(within)

    # --- the test: cross-clan alignment (gradeable via shared type labels) ---
    print("===== CROSS-CLAN alignment (top-20 shared types) =====")
    rows = []
    print(f"{'pair':<12}{'n':>4}{'t/cell':>8}{'QAP':>7}{'base':>7}"
          f"{'null':>7}{'>base':>7}{'>null':>7}")
    for ca, cb in itertools.combinations(CLANS, 2):
        r = run_pair(df, ca, cb)
        rows.append(r)
        print(f"{ca+'-'+cb:<12}{r['n_shared_types']:>4}{r['trans_per_cell']:>8}"
              f"{r['qap_acc']:>7.2f}{r['baseline_acc']:>7.2f}{r['null_mean']:>7.2f}"
              f"{str(r['beats_baseline']):>7}{str(r['beats_null']):>7}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    qap = np.array([r["qap_acc"] for r in rows])
    base = np.array([r["baseline_acc"] for r in rows])
    null = np.array([r["null_mean"] for r in rows])
    nfrac = np.mean([r["beats_null"] for r in rows])
    print("\n===== SUMMARY =====")
    print(f"  WITHIN-clan (positive control): QAP={wq:.3f} vs baseline={wb:.3f}"
          f"  -> type IS recoverable from position within a clan")
    print(f"  CROSS-clan (21 pairs, top-{K}):  QAP={qap.mean():.3f} "
          f"baseline={base.mean():.3f} null={null.mean():.3f}")
    print(f"    QAP − baseline: {qap.mean()-base.mean():+.3f}; "
          f"pairs beating null(p95): {nfrac*100:.0f}%")
    conserved = qap.mean() > base.mean() + 0.02 and qap.mean() > null.mean() + 0.02
    print(f"  VERDICT: combinatorial role is "
          f"{'CONSERVED across clans' if conserved else 'CLAN-SPECIFIC — it does NOT transfer across clans'}")
    print(f"  Reading: the acoustic type inventory is shared across clans, but the")
    print(f"  sequencing that identifies a type within its clan does not carry over.")
    print(f"\nwrote {OUT} and within_pacific.csv")


if __name__ == "__main__":
    main()

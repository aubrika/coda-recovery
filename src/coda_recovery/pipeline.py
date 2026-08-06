"""Split-half experiment orchestration (spec Section 6.4, 7).

Ground truth is the identity: both halves are the same clan, so a correctly
recovered permutation maps every type to itself. Every experiment emits one CSV
row carrying the full config plus every metric, so no result lives only in
scrollback (spec 7).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

import numpy as np
import pandas as pd

from .inventory import coda_mask, session_key_codanumber_gaps, UNATTRIBUTED_SPEAKER
from .transitions import (
    coda_type_index,
    row_normalise,
    TransitionSet,
)
from .recover import (
    qap_recover,
    procrustes_recover,
    frequency_rank_baseline,
    accuracy_at_1,
    freq_weighted_accuracy,
)
from .nulls import shuffle_within_segments, random_permutation_null

SPLIT_TYPES = ("random", "by_date", "by_individual", "by_unit")


def assign_halves(df: pd.DataFrame, split_type: str, seed: int) -> pd.Series:
    """Return a Series over the coda rows with values 'A'/'B' (or '' for rows
    excluded from this split, e.g. unattributed codas under by_individual)."""
    codas = df[coda_mask(df)]
    rng = np.random.default_rng(seed)

    def half_map(keys):
        uniq = np.array(sorted(pd.unique(keys)))
        rng.shuffle(uniq)
        cut = len(uniq) // 2
        m = {k: ("A" if i < cut else "B") for i, k in enumerate(uniq)}
        return m

    if split_type == "random":
        vals = rng.integers(0, 2, size=len(codas))
        return pd.Series(np.where(vals == 0, "A", "B"), index=codas.index)
    if split_type == "by_date":
        m = half_map(codas["Date"])
        return codas["Date"].map(m)
    if split_type == "by_unit":
        m = half_map(codas["Unit"])
        return codas["Unit"].map(m)
    if split_type == "by_individual":
        attr = codas[codas["WhaleID"] != UNATTRIBUTED_SPEAKER]
        m = half_map(attr["WhaleID"])
        return codas["WhaleID"].map(lambda w: m.get(w, ""))
    raise ValueError(f"unknown split_type {split_type!r}")


def _labeled_pairs(
    df: pd.DataFrame,
    half: pd.Series,
    speaker_mode: str,
    session_cols,
    max_codanumber_gap: int,
) -> pd.DataFrame:
    """Same-segment adjacent pairs, carrying each endpoint's half and speaker."""
    codas = df[coda_mask(df)].copy()
    seg = session_key_codanumber_gaps(codas, session_cols, max_codanumber_gap)
    codas = codas.assign(_seg=seg, _half=half).sort_values("CodaNumber").reset_index(drop=True)
    a = codas.iloc[:-1].reset_index(drop=True)
    b = codas.iloc[1:].reset_index(drop=True)
    same_seg = a["_seg"].to_numpy() == b["_seg"].to_numpy()
    p = pd.DataFrame(
        {
            "a_type": a["CodaName"].to_numpy(),
            "b_type": b["CodaName"].to_numpy(),
            "a_spk": a["WhaleID"].to_numpy(),
            "b_spk": b["WhaleID"].to_numpy(),
            "a_half": a["_half"].to_numpy(),
            "b_half": b["_half"].to_numpy(),
        }
    )[same_seg].reset_index(drop=True)

    if speaker_mode != "pooled":
        attr = (p["a_spk"] != UNATTRIBUTED_SPEAKER) & (p["b_spk"] != UNATTRIBUTED_SPEAKER)
        p = p[attr]
        same_spk = p["a_spk"] == p["b_spk"]
        p = p[same_spk] if speaker_mode == "within" else p[~same_spk]
    return p.reset_index(drop=True)


def _count_matrix(pairs: pd.DataFrame, types: list[str]) -> np.ndarray:
    idx = {t: i for i, t in enumerate(types)}
    n = len(types)
    C = np.zeros((n, n), dtype=np.int64)
    for a, b in zip(pairs["a_type"], pairs["b_type"]):
        C[idx[a], idx[b]] += 1
    return C


def build_split_sets(
    df: pd.DataFrame,
    types: list[str],
    split_type: str,
    speaker_mode: str,
    alpha: float,
    seed: int,
    session_cols=("Date",),
    max_codanumber_gap: int = 1,
) -> tuple[TransitionSet, TransitionSet]:
    """Build TransitionSet for half A and half B under a split. A pair counts for
    a half only if BOTH endpoints are in that half (so a random split keeps only
    within-half adjacencies; a by-date split keeps all within-date pairs)."""
    half = assign_halves(df, split_type, seed)
    pairs = _labeled_pairs(df, half, speaker_mode, session_cols, max_codanumber_gap)

    def mk(tag):
        sub = pairs[(pairs["a_half"] == tag) & (pairs["b_half"] == tag)]
        C = _count_matrix(sub, types)
        return TransitionSet(list(types), C, row_normalise(C, alpha),
                             int(C.sum()), speaker_mode, alpha)

    return mk("A"), mk("B")


@dataclass
class ExperimentResult:
    split_type: str
    speaker_mode: str
    alpha: float
    max_codanumber_gap: int
    seed: int
    n_types: int
    n_trans_A: int
    n_trans_B: int
    transitions_per_cell_A: float
    transitions_per_cell_B: float
    qap_accuracy: float
    qap_freq_weighted_accuracy: float
    qap_objective: float
    qap_restart_obj_min: float
    qap_restart_obj_max: float
    baseline_accuracy: float
    baseline_freq_weighted_accuracy: float
    strong_null_accuracy_mean: float
    strong_null_accuracy_p95: float
    beats_baseline: bool
    beats_strong_null: bool
    qap_perm: list = field(default_factory=list)

    def row(self) -> dict:
        d = asdict(self)
        d["qap_perm"] = " ".join(map(str, self.qap_perm))
        return d


def run_experiment(
    df: pd.DataFrame,
    types: list[str],
    split_type: str,
    speaker_mode: str = "pooled",
    alpha: float = 1.0,
    max_codanumber_gap: int = 1,
    seed: int = 0,
    qap_restarts: int = 30,
    strong_null_reps: int = 40,
) -> ExperimentResult:
    """Run the full recovery + controls for one config and return a result row.

    The strong null (spec 6.3) reruns the ENTIRE pipeline on sequence-shuffled
    data: for each rep, shuffle types within segments, rebuild both halves under
    the same split, recover by QAP, record accuracy@1. The observed recovery is
    meaningful only relative to this distribution and the frequency baseline."""
    n = len(types)
    weights = None

    # Observed recovery.
    A, B = build_split_sets(df, types, split_type, speaker_mode, alpha, seed,
                            max_codanumber_gap=max_codanumber_gap)
    weights = (A.C.sum() + B.C.sum())  # scalar guard below
    type_freq = A.C.sum(axis=1) + A.C.sum(axis=0) + B.C.sum(axis=1) + B.C.sum(axis=0)

    rec = qap_recover(A.T, B.T, n_restarts=qap_restarts, seed=seed)
    qap_acc = accuracy_at_1(rec.perm)
    qap_fw = freq_weighted_accuracy(rec.perm, type_freq.astype(float))

    base_perm = frequency_rank_baseline(A.C, B.C)
    base_acc = accuracy_at_1(base_perm)
    base_fw = freq_weighted_accuracy(base_perm, type_freq.astype(float))

    # Strong null: rebuild + recover on shuffled sequences.
    null_accs = []
    for i in range(strong_null_reps):
        sh = shuffle_within_segments(df, seed=1000 + i)
        # keep the SAME half assignment structure by re-splitting the shuffled df
        nA, nB = build_split_sets(sh, types, split_type, speaker_mode, alpha,
                                  seed, max_codanumber_gap=max_codanumber_gap)
        nrec = qap_recover(nA.T, nB.T, n_restarts=max(8, qap_restarts // 3),
                           seed=seed, refine_2opt=False)
        null_accs.append(accuracy_at_1(nrec.perm))
    null_accs = np.array(null_accs)

    return ExperimentResult(
        split_type=split_type,
        speaker_mode=speaker_mode,
        alpha=alpha,
        max_codanumber_gap=max_codanumber_gap,
        seed=seed,
        n_types=n,
        n_trans_A=A.n_transitions,
        n_trans_B=B.n_transitions,
        transitions_per_cell_A=round(A.transitions_per_cell, 3),
        transitions_per_cell_B=round(B.transitions_per_cell, 3),
        qap_accuracy=round(qap_acc, 4),
        qap_freq_weighted_accuracy=round(qap_fw, 4),
        qap_objective=round(rec.objective, 6),
        qap_restart_obj_min=round(min(rec.all_objectives), 6) if rec.all_objectives else round(rec.objective, 6),
        qap_restart_obj_max=round(max(rec.all_objectives), 6) if rec.all_objectives else round(rec.objective, 6),
        baseline_accuracy=round(base_acc, 4),
        baseline_freq_weighted_accuracy=round(base_fw, 4),
        strong_null_accuracy_mean=round(float(null_accs.mean()), 4),
        strong_null_accuracy_p95=round(float(np.percentile(null_accs, 95)), 4),
        beats_baseline=bool(qap_acc > base_acc),
        beats_strong_null=bool(qap_acc > np.percentile(null_accs, 95)),
        qap_perm=rec.perm.tolist(),
    )

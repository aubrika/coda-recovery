"""Controls (spec Section 6).

- random_permutation_null (6.2, weak): objective under random relabellings.
- sequence_shuffle_null (6.3, strong): shuffle coda order *within segments*,
  preserving each segment's type composition and length, then rebuild the whole
  transition structure. Destroys sequential structure while preserving marginals,
  sparsity pattern and sample size — isolating whether recovery comes from
  transitions rather than from frequency and matrix shape. This is the null that
  matters; it runs the entire pipeline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .inventory import coda_mask, session_key_codanumber_gaps
from .recover import frobenius_objective, perm_to_matrix


def random_permutation_null(TA, TB, n: int = 2000, seed: int = 0) -> np.ndarray:
    """Objective of n random permutations (6.2)."""
    rng = np.random.default_rng(seed)
    k = TA.shape[0]
    out = np.empty(n)
    for i in range(n):
        out[i] = frobenius_objective(perm_to_matrix(rng.permutation(k)), TA, TB)
    return out


def shuffle_within_segments(
    df: pd.DataFrame, seed: int, session_cols=("Date",), max_codanumber_gap: int = 1
) -> pd.DataFrame:
    """Return a copy of the coda rows with CodaName shuffled within each segment
    (composition and length preserved, order destroyed). Speaker labels are kept
    attached to their original CodaNumber slot, so the speaker *sequence* is
    intact while the *type* sequence is randomised — the null then measures type
    transition structure specifically."""
    rng = np.random.default_rng(seed)
    codas = df[coda_mask(df)].copy()
    seg = session_key_codanumber_gaps(codas, session_cols, max_codanumber_gap)
    codas = codas.assign(_seg=seg)
    out = codas.copy()
    for _, idx in codas.groupby("_seg").groups.items():
        names = codas.loc[idx, "CodaName"].to_numpy().copy()
        rng.shuffle(names)
        out.loc[idx, "CodaName"] = names
    return out.drop(columns="_seg")

from collections import Counter

import numpy as np

from coda_recovery.coda_ordering import count_table
from coda_recovery.ordering_checks import simulate_shared, to_pairs

SEQS = [("rec1", [(0, 0), (1, 1), (0, 0), (2, 1), (1, 0)], [True, True, False, True]),
        ("rec2", [(2, 0), (2, 0), (0, 1)], [True, True])]


def test_pairs_respect_broken_links():
    pairs = to_pairs(SEQS)
    assert len(pairs) == 5
    assert ("rec1", (0, 0), (2, 1)) not in pairs          # the link between positions 2 and 3 is broken


def test_shuffle_keeps_each_recordings_codas_and_pair_count():
    rng = np.random.default_rng(0)
    for _ in range(20):
        shuffled = to_pairs(SEQS, rng)
        assert Counter(u for u, _, _ in shuffled) == Counter(u for u, _, _ in to_pairs(SEQS))
        assert {t for u, a, b in shuffled if u == "rec2" for t in (a, b)} <= {(2, 0), (0, 1)}


def test_simulation_keeps_recording_sizes_and_uses_only_its_codas():
    rng = np.random.default_rng(1)
    kernel = np.exp(rng.normal(0, 1, (3, 2, 3, 2)))
    sim = simulate_shared({"A": SEQS}, kernel, 1.0, rng)["A"]
    assert Counter(u for u, _, _ in sim) == Counter(u for u, _, _ in to_pairs(SEQS))
    real = to_pairs(SEQS)
    for rec in ("rec1", "rec2"):
        assert {a for u, a, _ in sim if u == rec} <= {a for u, a, _ in real if u == rec}
        assert {b for u, _, b in sim if u == rec} <= {b for u, _, b in real if u == rec}


def test_simulated_order_follows_the_kernel():
    """A kernel that strongly favours one transition shows up in the simulated pairs."""
    rng = np.random.default_rng(2)
    tokens = [(int(r), 0) for r in rng.integers(0, 3, 4000)]
    seqs = [("rec", tokens, [True] * (len(tokens) - 1))]
    kernel = np.ones((3, 1, 3, 1))
    kernel[0, 0, 1, 0] = 20.0
    favoured = count_table(simulate_shared({"A": seqs}, kernel, 1.0, rng)["A"], 3, 1)[0, 0, 1, 0]
    neutral = count_table(simulate_shared({"A": seqs}, kernel, 0.0, rng)["A"], 3, 1)[0, 0, 1, 0]
    assert favoured > 1.5 * neutral

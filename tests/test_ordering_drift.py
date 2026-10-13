import numpy as np

from coda_recovery.ordering_drift import count_matrix, ordering_lost, rake, transfer_gain


def sample(rng, P, n, start=0):
    """n transitions from a Markov chain with transition matrix P, as recording pairs."""
    out, x = [], start
    for _ in range(n):
        y = rng.choice(len(P), p=P[x])
        out.append(("rec", x, y))
        x = y
    return out


def chain(freq, ratio):
    """Transition matrix proportional to freq[next] * ratio[current, next]."""
    P = freq[None, :] * ratio
    return P / P.sum(1, keepdims=True)


RATIO = np.array([[1.0, 4.0, 0.5, 1.0],
                  [0.5, 1.0, 4.0, 1.0],
                  [1.0, 0.5, 1.0, 4.0],
                  [4.0, 1.0, 0.5, 1.0]])


def test_shared_ordering_transfers_across_different_inventories():
    """Two clans with the same ordering but very different coda frequencies."""
    rng = np.random.default_rng(0)
    A = chain(np.array([0.55, 0.25, 0.15, 0.05]), RATIO)
    B = chain(np.array([0.05, 0.15, 0.25, 0.55]), RATIO)
    a = count_matrix(sample(rng, A, 40000), 4)
    b_train = count_matrix(sample(rng, B, 40000), 4)
    b_test = count_matrix(sample(rng, B, 40000), 4)
    for changes in (False, True):
        own = transfer_gain(b_train, b_train, b_test, changes)
        foreign = transfer_gain(a, b_train, b_test, changes)
        assert own > 0.1
        assert foreign > 0.9 * own


def test_unordered_source_neither_helps_nor_hurts():
    rng = np.random.default_rng(1)
    flat = chain(np.array([0.7, 0.1, 0.1, 0.1]), np.ones((4, 4)))
    B = chain(np.array([0.1, 0.2, 0.3, 0.4]), RATIO)
    a = count_matrix(sample(rng, flat, 40000), 4)
    b_train = count_matrix(sample(rng, B, 40000), 4)
    b_test = count_matrix(sample(rng, B, 40000), 4)
    for changes in (False, True):
        assert abs(transfer_gain(a, b_train, b_test, changes)) < 0.01


def test_independent_target_gains_nothing_from_its_own_ordering():
    rng = np.random.default_rng(2)
    flat = chain(np.array([0.4, 0.3, 0.2, 0.1]), np.ones((4, 4)))
    train = count_matrix(sample(rng, flat, 40000), 4)
    test = count_matrix(sample(rng, flat, 40000), 4)
    for changes in (False, True):
        assert abs(transfer_gain(train, train, test, changes)) < 0.01


def test_ordering_lost_is_symmetric_with_zero_diagonal():
    G = np.array([[0.5, 0.1], [0.3, 0.4]])
    L = ordering_lost(G)
    assert np.allclose(np.diag(L), 0.0)
    assert np.isclose(L[0, 1], L[1, 0])
    assert np.isclose(L[0, 1], ((0.4 - 0.1) + (0.5 - 0.3)) / 2)


def test_rake_matches_margins_and_keeps_odds_ratios():
    M = np.array([[4.0, 1.0, 2.0], [1.0, 3.0, 1.0], [2.0, 1.0, 5.0]])
    rows, cols = np.array([10.0, 20.0, 30.0]), np.array([25.0, 15.0, 20.0])
    R = rake(M, rows, cols)
    assert np.allclose(R.sum(1), rows) and np.allclose(R.sum(0), cols)
    odds = lambda X: X[0, 0] * X[1, 1] / (X[0, 1] * X[1, 0])
    assert np.isclose(odds(R), odds(M))

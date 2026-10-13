import numpy as np

from coda_recovery.drift import inventory_divergence, mantel, mutual_loss


def distances(rng, n):
    pts = rng.normal(size=(n, 3))
    return np.linalg.norm(pts[:, None] - pts[None], axis=2)


def test_mantel_enumerates_every_relabelling():
    D = distances(np.random.default_rng(0), 5)
    result = mantel(D, D)
    assert result["permutations"] == 120
    assert np.isclose(result["rho"], 1.0)
    # only relabellings that reproduce the matrix can tie a perfect correlation
    assert result["p_positive"] <= 2 / 120


def test_mantel_does_not_flag_unrelated_matrices():
    rng = np.random.default_rng(1)
    result = mantel(distances(rng, 6), distances(rng, 6))
    assert result["p_two_sided"] > 0.05


def test_partial_mantel_removes_a_shared_driver():
    rng = np.random.default_rng(2)
    Z = distances(rng, 6)
    noise_x, noise_y = distances(rng, 6), distances(rng, 6)
    X, Y = Z + 0.05 * noise_x, Z + 0.05 * noise_y
    assert mantel(X, Y)["rho"] > 0.9
    assert abs(mantel(X, Y, Z)["rho"]) < 0.5


def test_mutual_loss_is_symmetric_and_flips_sign():
    T = np.array([[0.5, -1.0], [-3.0, 0.2]])
    L = mutual_loss(T)
    assert L[0, 1] == L[1, 0] == 2.0


def test_inventory_divergence_bounds():
    pairs = {"A": [("r", 1, 1), ("r", 1, 2)], "B": [("r", 1, 1), ("r", 1, 2)], "C": [("r", 3, 4)]}
    J = inventory_divergence(pairs, clans=["A", "B", "C"])
    assert np.isclose(J[0, 1], 0.0)
    assert np.isclose(J[0, 2], 1.0)   # disjoint inventories: one bit

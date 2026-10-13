"""Synthetic checks: the whole-coda model must separate ordering from inventory."""
import numpy as np

from coda_recovery.coda_ordering import (INVENTORY, MODELS, ORDERING, allowed, fit, fit_model, gain,
                                         margin, smoothed, with_inventory)

R, T = 4, 3


def ordering_kernel(rng, cross=0.0):
    """exp of additive rhythm→rhythm and tempo→tempo terms, plus optional cross terms."""
    rr, tt = rng.normal(0, 1.0, (R, R)), rng.normal(0, 1.0, (T, T))
    rt, tr = cross * rng.normal(0, 1.0, (R, T)), cross * rng.normal(0, 1.0, (T, R))
    return np.exp(rr[:, None, :, None] + tt[None, :, None, :] + rt[:, None, None, :] + tr[None, :, :, None])


def clan(kernel, inventory, changes=False):
    """A true transition table: the kernel's ordering on the given coda inventory."""
    target = np.einsum("ij,kl->ijkl", inventory, inventory) * allowed(R, T, changes)
    return fit(target, INVENTORY, kernel * allowed(R, T, changes))


def sample(rng, table, n):
    p = (table / table.sum()).ravel()
    return rng.multinomial(n, p).reshape(table.shape).astype(float)


def inventories(rng):
    """Two inventories that favour different coda types but both use every rhythm and tempo."""
    a = rng.dirichlet(np.full(R * T, 0.4)).reshape(R, T) + 0.01
    b = np.roll(a[::-1], 1, axis=1)
    return a / a.sum(), b / b.sum()


def score(source, train, test, changes):
    base = fit(smoothed(train, changes), INVENTORY, allowed(R, T, changes))
    return gain(with_inventory(source, smoothed(train, changes)), base, test)


def test_fit_reproduces_every_margin_it_is_given():
    rng = np.random.default_rng(0)
    N = sample(rng, clan(ordering_kernel(rng), inventories(rng)[0]), 5000)
    M, X = fit_model(N, False, MODELS["factored"]), smoothed(N, False)
    for axes in INVENTORY + list(ORDERING.values()):
        assert np.allclose(margin(M, axes), margin(X, axes), rtol=1e-5)


def test_shared_ordering_transfers_across_different_inventories():
    for changes in (False, True):
        rng = np.random.default_rng(1)
        kernel = ordering_kernel(rng)
        inv_a, inv_b = inventories(rng)
        a = sample(rng, clan(kernel, inv_a, changes), 60000)
        b_train = sample(rng, clan(kernel, inv_b, changes), 60000)
        b_test = sample(rng, clan(kernel, inv_b, changes), 60000)
        own = score(fit_model(b_train, changes, MODELS["factored"]), b_train, b_test, changes)
        foreign = score(fit_model(a, changes, MODELS["factored"]), b_train, b_test, changes)
        assert own > 0.05
        assert foreign > 0.9 * own


def test_unrelated_ordering_misleads_on_average():
    """Two random orderings can agree a little by chance, so this is checked over several draws."""
    for changes in (False, True):
        foreign, own = [], []
        for seed in range(8):
            rng = np.random.default_rng(100 + seed)
            inv_a, inv_b = inventories(rng)
            a = sample(rng, clan(ordering_kernel(rng), inv_a, changes), 60000)
            truth_b = clan(ordering_kernel(rng), inv_b, changes)
            b_train, b_test = sample(rng, truth_b, 60000), sample(rng, truth_b, 60000)
            own.append(score(fit_model(b_train, changes, MODELS["factored"]), b_train, b_test, changes))
            foreign.append(score(fit_model(a, changes, MODELS["factored"]), b_train, b_test, changes))
        assert np.mean(foreign) < 0
        assert all(f < o for f, o in zip(foreign, own))


def test_unordered_source_neither_helps_nor_hurts():
    for changes in (False, True):
        rng = np.random.default_rng(3)
        inv_a, inv_b = inventories(rng)
        a = sample(rng, clan(np.ones((R, T, R, T)), inv_a, changes), 60000)
        truth_b = clan(ordering_kernel(rng), inv_b, changes)
        b_train, b_test = sample(rng, truth_b, 60000), sample(rng, truth_b, 60000)
        assert abs(score(fit_model(a, changes, MODELS["factored"]), b_train, b_test, changes)) < 0.01


def test_cross_terms_are_detected_only_when_present():
    for cross, expect_more in ((0.0, False), (1.0, True)):
        rng = np.random.default_rng(4)
        truth = clan(ordering_kernel(rng, cross), inventories(rng)[0])
        train, test = sample(rng, truth, 80000), sample(rng, truth, 80000)
        plain = score(fit_model(train, False, MODELS["both, no cross terms"]), train, test, False)
        full = score(fit_model(train, False, MODELS["factored"]), train, test, False)
        assert (full > plain + 0.02) == expect_more

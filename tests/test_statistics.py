import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import chi2
from cmb_lab.statistics import (dl_to_cl, correlation_matrix, s_kernel, s_stat,
    simulate, lower_tail, parity, family_min_p, metrics)


def test_units():
    ell = np.array([2, 3, 17])
    assert np.allclose(dl_to_cl(ell, ell * (ell + 1) / (2 * np.pi)), 1.)


def test_kernel_matches_independent_adaptive_integration():
    ell = np.arange(2, 17)
    cl = np.random.default_rng(14).uniform(1, 20, len(ell))
    for endpoint in [.5, -.2, 1.]:
        expected = quad(lambda x: float((correlation_matrix(ell, [x]) @ cl)[0])**2, -1, endpoint, epsabs=1e-9)[0]
        assert np.isclose(s_stat(cl, s_kernel(ell, endpoint)), expected, rtol=1e-11)


def test_full_sphere_legendre_orthogonality():
    ell = np.arange(2, 30)
    expected = np.diag((2 * ell + 1) / (8 * np.pi**2))
    np.testing.assert_allclose(s_kernel(ell, 1), expected, atol=2e-12)


def test_gaussian_cosmic_variance_and_quad_tail():
    ell = np.arange(2, 9)
    theory = np.arange(1, 8) * 100
    sims = simulate(ell, theory, 150000, np.random.default_rng(32))
    np.testing.assert_allclose(sims.mean(0), theory, rtol=.008)
    np.testing.assert_allclose(sims.var(0), 2 * theory**2 / (2 * ell + 1), rtol=.025)
    obs = .2 * theory[0]
    assert abs(lower_tail(sims[:, 0], obs)["p"] - chi2.cdf(1, 5)) < .002


def test_equal_dl_parity_is_one_even_for_unequal_counts():
    ell = np.arange(2, 30)
    cl = dl_to_cl(ell, np.ones(len(ell)))
    assert parity(ell, cl, 28) == pytest.approx(1)
    assert parity(ell, cl, 29) == pytest.approx(1)


def test_zero_and_all_hits_are_finite():
    a = lower_tail(np.arange(10.), -1)
    b = lower_tail(np.arange(10.), 100)
    assert a["p"] == 1 / 11 and a["ci95"][0] == 0 and a["ci95"][1] > 0
    assert b["p"] == 1 and b["ci95"][1] == 1
    with pytest.raises(ValueError):
        lower_tail([], 1)


def test_family_calibration_matches_uniform_independent_case():
    rng = np.random.default_rng(41)
    reference = rng.uniform(size=(100000, 4))
    calibration = rng.uniform(size=(100000, 4))
    result = family_min_p(reference, calibration, np.array([.02, .5, .6, .7]))
    assert abs(result["p"] - (1 - .98**4)) < .004


def test_duplicate_tests_do_not_add_trial_penalty():
    rng = np.random.default_rng(9)
    ref = rng.uniform(size=(40000, 1))
    cal = rng.uniform(size=(40000, 1))
    a = family_min_p(ref, cal, [.05])
    b = family_min_p(np.repeat(ref, 4, axis=1), np.repeat(cal, 4, axis=1), [.05] * 4)
    assert a["p"] == b["p"]


def test_metrics_batch_and_scalar_agree():
    ell = np.arange(2, 33)
    cl = np.random.default_rng(24).uniform(1, 100, size=(8, len(ell)))
    np.testing.assert_allclose(metrics(ell, cl), np.stack([metrics(ell, a) for a in cl]))


def test_cancellation_stationary_point():
    ell = np.arange(2, 65)
    k = s_kernel(ell)
    cl = 1000 / ell**2
    stationary = -(k[0, 1:] @ cl[1:]) / k[0, 0]
    cl[0] = stationary
    assert abs((k @ cl)[0]) < 1e-10
    for delta in (-1, 1):
        test = cl.copy()
        test[0] += delta
        assert s_stat(test, k) > s_stat(cl, k)

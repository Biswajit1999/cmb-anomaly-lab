"""Independent identities for the cut-sky operators, not snapshot tests."""
import numpy as np
import pytest
hp = pytest.importorskip('healpy')
from numpy.polynomial.legendre import legval
from cmb_lab.map_statistics import MapEstimator, gaussian_alm, transfer


def setup_small():
    nside = 4
    vec = np.asarray(hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))).T
    return MapEstimator(abs(vec[:, 2]) > .25, lmax=10, axis_nside=1, nquad=48)


def test_projection_annihilates_monopole_and_dipole():
    e = setup_small()
    sky = e.x @ np.array([12., -4., 2., 9.])
    np.testing.assert_allclose(e.project(sky), 0, atol=2e-14)
    rng = np.random.default_rng(31)
    sky = rng.normal(size=len(e.mask))
    np.testing.assert_allclose(e.project(sky + e.x @ np.arange(4)), e.project(sky), atol=1e-14)


def test_addition_theorem_matches_discrete_pair_kernel():
    e = setup_small()
    sky = np.random.default_rng(4).normal(size=len(e.mask))
    values, cl, _ = e.evaluate(sky)
    y = e.project(sky)
    cosines = np.clip(e.vec @ e.vec.T, -1, 1)
    # Sum pairs directly; independent of map2alm and alm2cl implementation.
    pairs = np.outer(y, y)
    area = 4*np.pi/len(y)
    for ell in [0, 2, 5, 10]:
        coeff = np.zeros(ell+1); coeff[-1] = 1
        direct = area**2/(4*np.pi)*np.sum(pairs*legval(cosines, coeff))
        np.testing.assert_allclose(cl[ell], direct, rtol=2e-12, atol=1e-14)
    assert np.isfinite(values).all()


def test_analytic_variance_matches_dense_covariance():
    e = setup_small()
    cl = np.zeros(11); cl[2:] = 2/np.arange(2,11)**2
    cov = legval(np.clip(e.vec @ e.vec.T,-1,1), (2*np.arange(11)+1)*cl/(4*np.pi))
    cov = cov[np.ix_(e.mask,e.mask)]
    projection = np.eye(e.mask.sum())-e.design @ e.pinv
    expected = np.trace(projection @ cov @ projection.T)/e.mask.sum()
    np.testing.assert_allclose(e.expected_variance(cl), expected, rtol=1e-12)


def test_gaussian_modes_have_real_mzero_and_correct_power():
    cl = np.zeros(11); cl[2:] = 1
    rng = np.random.default_rng(71)
    a = np.array([gaussian_alm(cl,rng) for _ in range(1500)])
    ell, m = hp.Alm.getlm(10)
    assert np.all(a[:,m==0].imag == 0)
    np.testing.assert_allclose(np.mean(abs(a[:,ell>=2])**2),1,atol=.015)


def test_full_sky_mask_and_quadrature_convergence():
    e = MapEstimator(np.ones(hp.nside2npix(16),dtype=bool),lmax=32,nquad=64)
    cl=np.zeros(33); cl[2:]=1/np.arange(2,33)**2
    sky=hp.alm2map(gaussian_alm(cl,np.random.default_rng(6)),16,pol=False)
    dense=MapEstimator(e.mask,lmax=32,nquad=128)
    np.testing.assert_allclose(e.evaluate(sky)[0][0],dense.evaluate(sky)[0][0],rtol=2e-7)
    # Finite equal-area pixel quadrature leaves tiny nonzero mask harmonics.
    np.testing.assert_allclose(e.denominator,1,atol=3e-5)

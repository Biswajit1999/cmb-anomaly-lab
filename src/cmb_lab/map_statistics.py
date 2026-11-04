"""Finite-band cut-sky diagnostics with the same linear operators on every sky.

This module deliberately does not interpret masked pseudo-C_l as full-sky C_l.
Equal-area harmonic quadrature uses iter=0, making the estimator an explicit
discrete quadratic form that can be checked against the addition theorem.
"""
from dataclasses import dataclass
import healpy as hp
import numpy as np
from numpy.polynomial.legendre import leggauss
from .statistics import correlation_matrix, parity

MAP_NAMES = ["cut_sky_s_half", "masked_variance", "pseudo_parity", "hemisphere_max_contrast"]
TAIL_SIGNS = np.array([1., 1., 1., -1.])


def gaussian_alm(cl, rng):
    ell, m = hp.Alm.getlm(len(cl) - 1)
    a = (rng.normal(size=len(ell)) + 1j * rng.normal(size=len(ell))) * np.sqrt(cl[ell] / 2)
    real = m == 0
    a[real] = rng.normal(size=real.sum()) * np.sqrt(cl[ell[real]])
    return a


def transfer(nside, lmax, fwhm_deg):
    return hp.gauss_beam(np.deg2rad(fwhm_deg), lmax=lmax) * hp.pixwin(nside, lmax=lmax)


@dataclass
class MapEstimator:
    mask: np.ndarray
    lmax: int = 95
    axis_nside: int = 2
    nquad: int = 192

    def __post_init__(self):
        self.mask = np.asarray(self.mask, dtype=bool)
        self.nside = hp.npix2nside(len(self.mask))
        self.vec = np.asarray(hp.pix2vec(self.nside, np.arange(len(self.mask)))).T
        self.x = np.column_stack([np.ones(len(self.mask)), self.vec])
        self.design = self.x[self.mask]
        self.pinv = np.linalg.pinv(self.design)
        axis = np.asarray(hp.pix2vec(self.axis_nside, np.arange(hp.nside2npix(self.axis_nside)))).T
        # Antipodal axes define the same absolute contrast: keep one of each pair.
        keep = (axis[:, 2] > 1e-12) | ((abs(axis[:, 2]) < 1e-12) & (axis[:, 1] > 1e-12))
        keep |= (abs(axis[:, 2]) < 1e-12) & (abs(axis[:, 1]) < 1e-12) & (axis[:, 0] > 0)
        self.axes = axis[keep]
        self.north = (self.vec[self.mask] @ self.axes.T > 0).astype(float).T
        self.south = 1 - self.north
        self.north /= self.north.sum(axis=1, keepdims=True)
        self.south /= self.south.sum(axis=1, keepdims=True)
        nodes, weights = leggauss(self.nquad)
        self.nodes, self.weights = .75 * nodes - .25, .75 * weights
        self.basis = correlation_matrix(np.arange(self.lmax + 1), self.nodes)
        self.mask_cl = hp.anafast(self.mask.astype(float), lmax=self.lmax, iter=0)
        self.denominator = self.basis @ self.mask_cl
        if np.min(self.denominator) <= 0:
            raise ValueError("Mask pair correlation must stay positive over the integration domain")

    def project(self, sky):
        """OLS monopole/dipole subtraction fitted only on retained pixels."""
        y = np.asarray(sky)[self.mask]
        residual = y - self.design @ (self.pinv @ y)
        out = np.zeros(len(self.mask))
        out[self.mask] = residual
        return out

    def evaluate(self, sky):
        residual = self.project(sky)
        cl = hp.anafast(residual, lmax=self.lmax, iter=0)
        corr = (self.basis @ cl) / self.denominator
        y = residual[self.mask]
        vn = self.north @ (y*y) - (self.north @ y)**2
        vs = self.south @ (y*y) - (self.south @ y)**2
        contrast = np.abs(vn-vs) / (vn+vs)
        values = np.array([np.sum(self.weights*corr*corr), np.mean(y*y),
                           parity(np.arange(2, min(29, self.lmax)+1), cl[2:min(29, self.lmax)+1]), contrast.max()])
        return values, cl, contrast

    def correlation(self, cl, theta):
        basis = correlation_matrix(np.arange(self.lmax+1), np.cos(np.deg2rad(theta)))
        return (basis @ cl) / (basis @ self.mask_cl)

    def expected_variance(self, smoothed_cl):
        """Exact discrete Gaussian mean after projection, to harmonic roundoff.

        tr(P C)/N = C(0) - tr[(X'X)^-1 X'C X]/N. C is applied with
        spherical harmonics instead of allocating a dense 12288^2 matrix.
        """
        gram = self.design.T @ self.design
        xc = np.empty((4, 4))
        npix = len(self.mask)
        for j in range(4):
            field = self.mask * self.x[:, j]
            alm = hp.map2alm(field, lmax=len(smoothed_cl)-1, iter=0)
            applied = hp.alm2map(hp.almxfl(alm, smoothed_cl), self.nside, pol=False) * npix/(4*np.pi)
            xc[:, j] = self.design.T @ applied[self.mask]
        ell = np.arange(len(smoothed_cl))
        c0 = np.sum((2*ell+1)*smoothed_cl)/(4*np.pi)
        return float(c0 - np.trace(np.linalg.solve(gram, xc))/self.mask.sum())

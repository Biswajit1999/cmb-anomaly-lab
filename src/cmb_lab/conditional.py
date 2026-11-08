"""Conditional harmonic sampling, Haar rotations and split-calibrated diagnostics.

Conditioning fixes a different null hypothesis; probabilities from these ensembles
must never be multiplied or ranked as competing estimates of one significance.
"""
from dataclasses import dataclass
import healpy as hp
import numpy as np
from scipy.stats import beta
from .map_statistics import gaussian_alm


def fixed_power_alm(cl, rng):
    """Uniform real harmonic direction at each ell, at exactly specified power.

    Normalized Gaussian vectors sample S^(2ell). This randomizes both relative
    amplitudes and phases, not only the complex phases of the measured a_lm.
    """
    cl = np.asarray(cl, dtype=float)
    if cl.ndim != 1 or not np.isfinite(cl).all() or np.any(cl < 0):
        raise ValueError('Require a finite, nonnegative one-dimensional spectrum')
    draw = gaussian_alm(cl, rng)
    power = hp.alm2cl(draw)
    scale = np.sqrt(np.divide(cl, power, out=np.zeros_like(cl), where=power > 0))
    return hp.almxfl(draw, scale)


def haar_angles(rng, size=None):
    """Haar SO(3): uniform azimuths and uniform cos(beta), NOT uniform beta."""
    return (rng.uniform(0, 2*np.pi, size), np.arccos(rng.uniform(-1, 1, size)),
            rng.uniform(0, 2*np.pi, size))


def rotated_alm(alm, rng):
    """Rotate the entire measured pattern, preserving all relative geometry."""
    result = np.array(alm, dtype=np.complex128, copy=True)
    psi, theta, phi = haar_angles(rng)
    hp.rotate_alm(result, psi=psi, theta=theta, phi=phi)
    return result


def binomial_rate(hits, n, confidence=.95):
    """Raw detection/coverage rate and exact Clopper-Pearson counting interval."""
    if not 0 <= hits <= n or n < 1 or not 0 < confidence < 1:
        raise ValueError('Invalid binomial counts or confidence')
    alpha = 1-confidence
    return {'hits': int(hits), 'n': int(n), 'rate': hits/n,
            'ci95': [float(beta.ppf(alpha/2, hits, n-hits+1)) if hits else 0.,
                     float(beta.ppf(1-alpha/2, hits+1, n-hits)) if hits < n else 1.]}


def upper_threshold(scores, alpha=.05):
    """Finite-sample upper threshold; reject strictly above this order statistic.

    For an exchangeable continuous new score, the marginal false-alarm rate is
    at most alpha. Infinity is returned when the calibration set is too small.
    """
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all() or not 0 < alpha < 1:
        raise ValueError('Finite scores and alpha in (0,1) required')
    rank = int(np.ceil((len(scores)+1)*(1-alpha)))
    return float(np.sort(scores)[rank-1]) if rank <= len(scores) else float('inf')


@dataclass
class SimultaneousBand:
    """A max-studentized finite-grid prediction envelope, fitted on reference only."""
    center: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, reference):
        reference = np.asarray(reference, dtype=float)
        if reference.ndim != 2 or len(reference) < 2 or not np.isfinite(reference).all():
            raise ValueError('Need finite reference curves')
        scale = reference.std(axis=0, ddof=1)
        if np.any(scale <= 0):
            raise ValueError('Every grid point must have positive reference variance')
        return cls(reference.mean(axis=0), scale)

    def score(self, curves):
        return np.max(np.abs((np.asarray(curves)-self.center)/self.scale), axis=-1)

    def bounds(self, calibration, alpha=.05):
        cutoff = upper_threshold(self.score(calibration), alpha)
        return self.center-cutoff*self.scale, self.center+cutoff*self.scale, cutoff


def modulate_smoothed_sky(sky, vectors, axis, amplitude):
    """Toy modulation AFTER smoothing; not a primordial transfer calculation."""
    axis = np.asarray(axis, dtype=float)
    if axis.shape != (3,) or not np.isfinite(axis).all() or np.linalg.norm(axis) == 0:
        raise ValueError('Require a finite nonzero 3-vector')
    if not np.isfinite(amplitude) or not 0 <= amplitude < 1:
        raise ValueError('Amplitude must lie in [0,1)')
    return np.asarray(sky)*(1+amplitude*(np.asarray(vectors) @ (axis/np.linalg.norm(axis))))

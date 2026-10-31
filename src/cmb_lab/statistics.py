"""Full-sky, noise-free Gaussian reference model; units are microkelvin."""
import numpy as np
from numpy.polynomial.legendre import leggauss, legvander
from scipy.stats import beta

NAMES = ["quadrupole", "s_half", "parity_2_29", "variance_2_29"]


def dl_to_cl(ell, dl):
    ell = np.asarray(ell)
    if np.any(ell < 2):
        raise ValueError("Only ell >= 2 is supported")
    return np.asarray(dl) * (2 * np.pi / (ell * (ell + 1)))


def correlation_matrix(ell, x):
    ell = np.asarray(ell, dtype=int)
    return legvander(np.atleast_1d(x), int(ell.max()))[:, ell] * (2 * ell + 1) / (4 * np.pi)


def s_kernel(ell, x=0.5, nquad=None):
    """Exact Gaussian quadrature for the polynomial C(x)^2 up to roundoff."""
    if not -1 < x <= 1:
        raise ValueError("Integration endpoint must lie in (-1, 1]")
    ell = np.asarray(ell)
    nodes, weights = leggauss(nquad or (int(ell.max()) + 1))
    nodes = (x + 1) / 2 * nodes + (x - 1) / 2
    weights = (x + 1) / 2 * weights
    basis = correlation_matrix(ell, nodes)
    return basis.T @ (weights[:, None] * basis)


def s_stat(cl, kernel):
    cl = np.asarray(cl)
    return np.einsum("...i,ij,...j->...", cl, kernel, cl, optimize=True)


def parity(ell, cl, lmax=29, lmin=2):
    ell = np.asarray(ell)
    dl = np.asarray(cl) * (ell * (ell + 1) / (2 * np.pi))
    use = (ell >= lmin) & (ell <= lmax)
    even = use & (ell % 2 == 0)
    odd = use & (ell % 2 == 1)
    if not even.any() or not odd.any():
        raise ValueError("Parity needs at least one even and one odd multipole")
    return dl[..., even].mean(axis=-1) / dl[..., odd].mean(axis=-1)


def metrics(ell, cl, kernel=None):
    ell = np.asarray(ell)
    cl = np.asarray(cl)
    if kernel is None:
        kernel = s_kernel(ell)
    band = ell <= 29
    return np.stack([
        cl[..., np.flatnonzero(ell == 2)[0]],
        s_stat(cl, kernel),
        parity(ell, cl),
        np.sum(cl[..., band] * (2 * ell[band] + 1) / (4 * np.pi), axis=-1),
    ], axis=-1)


def simulate(ell, theory_cl, n, rng):
    """Exact distribution of full-sky C_ell for independent Gaussian a_lm."""
    df = 2 * np.asarray(ell) + 1
    return np.asarray(theory_cl) * rng.chisquare(df, size=(n, len(df))) / df


def lower_tail(samples, observed):
    """Plus-one estimate with exact binomial 95% interval for the exceedance rate."""
    samples = np.asarray(samples)
    if samples.ndim != 1 or len(samples) == 0 or not np.isfinite(samples).all() or not np.isfinite(observed):
        raise ValueError("Finite non-empty 1D samples and finite observed value required")
    n = len(samples)
    k = int(np.count_nonzero(samples <= observed))
    return {"p": (k + 1) / (n + 1), "hits": k, "n": n,
            "ci95": [float(beta.ppf(.025, k, n - k + 1)) if k else 0.,
                     float(beta.ppf(.975, k + 1, n - k)) if k < n else 1.]}


def empirical_p(reference, values):
    """Map each column to a lower-tail rank using an independent reference set."""
    reference, values = np.asarray(reference), np.asarray(values)
    one = values.ndim == 1
    values = np.atleast_2d(values)
    out = np.empty_like(values, dtype=float)
    for j in range(reference.shape[1]):
        out[:, j] = (1 + np.searchsorted(np.sort(reference[:, j]), values[:, j], side="right")) / (len(reference) + 1)
    return out[0] if one else out


def family_min_p(reference, calibration, observed):
    """Calibrate the minimum marginal p over the explicitly supplied test family."""
    obs = empirical_p(reference, observed)
    null = empirical_p(reference, calibration).min(axis=1)
    result = lower_tail(null, float(obs.min()))
    result.update({"min_local_p": float(obs.min()), "n_tests": len(obs)})
    return result


def replacement_effects(ell, observed, theory, kernel):
    """Counterfactual diagnostic, not a fit: replace one measured C_l at a time."""
    baseline = float(s_stat(observed, kernel))
    effects = []
    for i, l in enumerate(ell):
        changed = observed.copy()
        changed[i] = theory[i]
        effects.append([int(l), float(s_stat(changed, kernel)) - baseline])
    return np.array(effects)

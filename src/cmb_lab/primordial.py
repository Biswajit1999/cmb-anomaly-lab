"""Likelihood proxy and a positive primordial suppression family."""
import numpy as np


def primordial_power(k, amplitude, cutoff, As=2.1e-9, ns=.9649, pivot=.05):
    k = np.asarray(k)
    if not 0 <= amplitude <= 1 or cutoff <= 0 or np.any(k <= 0):
        raise ValueError('Require positive k and cutoff, and amplitude in [0,1]')
    # expm1 avoids subtractive cancellation when amplitude=1 and k/kc is tiny.
    suppression = (1-amplitude) - amplitude*np.expm1(-(k/cutoff)**2)
    return As*(k/pivot)**(ns-1)*suppression


def improvement_grid(observed, baseline, models, ell):
    """2 log[L(model)/L(baseline)] for ideal full-sky TT bandpowers.

    Supports a batch of skies. Constants independent of the model cancel.
    The likelihood is exact for noise-free full-sky C_hat, but only a proxy
    when evaluated on the published Planck estimator.
    """
    baseline, models, observed = map(np.asarray, (baseline, models, observed))
    if np.any(baseline <= 0) or np.any(models <= 0):
        raise ValueError('Positive model power required')
    dof=2*np.asarray(ell)+1
    offset=np.sum(dof*np.log(baseline/models),axis=-1)
    slope=dof*(1/baseline-1/models)
    return observed @ slope.T + offset


def conditional_ee(tt, ee, te, measured_tt):
    """Mean full-sky EE power conditional on measured temperature power.

    This is a model prediction, not a measurement of polarization.
    """
    residual=np.asarray(ee)-np.asarray(te)**2/np.asarray(tt)
    if np.any(residual < -1e-10):
        raise ValueError('TT/TE/EE covariance is not positive semidefinite')
    return np.maximum(residual,0)+(np.asarray(te)/tt)**2*measured_tt

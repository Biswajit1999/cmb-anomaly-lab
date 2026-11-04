import numpy as np
from cmb_lab.primordial import primordial_power, improvement_grid, conditional_ee


def test_primordial_limits_and_linearity():
    k=np.geomspace(1e-7,1,100)
    base=primordial_power(k,0,.001)
    full=primordial_power(k,1,.001)
    np.testing.assert_allclose(primordial_power(k,.3,.001),.7*base+.3*full,rtol=1e-14)
    assert np.all(full>0) and full[0]/base[0]<1e-7
    np.testing.assert_allclose(full[-1],base[-1])


def test_likelihood_identity_and_scalar_derivation():
    ell=np.arange(2,10); base=np.ones(8); obs=np.linspace(.2,2,8)
    models=np.array([base,.7*base])
    score=improvement_grid(obs,base,models,ell)
    assert score[0]==0
    manual=sum((2*l+1)*(np.log(1/.7)+c*(1-1/.7)) for l,c in zip(ell,obs))
    np.testing.assert_allclose(score[1],manual)


def test_conditional_polarization_total_expectation():
    tt=np.array([2.,3.]); ee=np.array([1.,4.]); te=np.array([.4,-.3])
    np.testing.assert_allclose(conditional_ee(tt,ee,te,tt),ee)
    np.testing.assert_allclose(conditional_ee(tt,ee,np.zeros(2),100*tt),ee)

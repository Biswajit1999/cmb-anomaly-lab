import healpy as hp
import numpy as np
import pytest
from cmb_lab.conditional import (fixed_power_alm, haar_angles, rotated_alm,
    binomial_rate, upper_threshold, SimultaneousBand, modulate_smoothed_sky)
from cmb_lab.map_statistics import gaussian_alm


def test_fixed_power_preserves_every_multipole_and_zero_modes():
    cl = np.r_[0., 0., np.linspace(2, .01, 31)]
    a = fixed_power_alm(cl, np.random.default_rng(11))
    np.testing.assert_allclose(hp.alm2cl(a), cl, atol=2e-14, rtol=2e-14)
    ell, m = hp.Alm.getlm(len(cl)-1)
    assert np.all(a[ell < 2] == 0)
    assert np.all(a[m == 0].imag == 0)


def test_fixed_power_uniform_real_sphere_second_and_fourth_moments():
    # For a uniform direction in five real dimensions: E[x_i^2]=1,
    # E[x_i^4]=3*d/(d+2) at radius sqrt(d). Also checks sqrt(2) m>0 weights.
    rng = np.random.default_rng(2026)
    rows=[]
    for _ in range(6000):
        a=fixed_power_alm([0,0,1],rng)
        ids=hp.Alm.getidx(2,2,np.arange(3))
        rows.append([a[ids[0]].real, np.sqrt(2)*a[ids[1]].real,
                     np.sqrt(2)*a[ids[1]].imag, np.sqrt(2)*a[ids[2]].real,
                     np.sqrt(2)*a[ids[2]].imag])
    rows=np.array(rows)
    np.testing.assert_allclose(np.mean(rows**2,axis=0),1,atol=.055)
    np.testing.assert_allclose(np.mean(rows**4,axis=0),15/7,atol=.16)


def test_haar_pushforward_on_sphere_has_isotropic_moments():
    psi, theta, phi=haar_angles(np.random.default_rng(19),40000)
    vectors=np.column_stack([np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)])
    np.testing.assert_allclose(vectors.mean(axis=0),0,atol=.012)
    np.testing.assert_allclose(vectors.T@vectors/len(vectors),np.eye(3)/3,atol=.008)
    assert abs(np.mean(np.exp(1j*psi))) < .015


def test_rotation_preserves_power_and_does_not_mutate_input():
    rng=np.random.default_rng(90)
    a=gaussian_alm(np.r_[0,0,np.ones(15)],rng); original=a.copy()
    b=rotated_alm(a,rng)
    np.testing.assert_array_equal(a,original)
    np.testing.assert_allclose(hp.alm2cl(a),hp.alm2cl(b),rtol=3e-13,atol=1e-14)
    assert not np.allclose(a,b)


def test_split_band_scores_and_independent_coverage():
    rng=np.random.default_rng(23)
    loading=rng.normal(size=(4,17))
    curves=rng.normal(size=(15000,4))@loading
    band=SimultaneousBand.fit(curves[:2000])
    lo,hi,cutoff=band.bounds(curves[2000:7000])
    direct=np.all((curves[7000:]>=lo)&(curves[7000:]<=hi),axis=1)
    np.testing.assert_array_equal(direct,band.score(curves[7000:])<=cutoff)
    assert .93 < direct.mean() < .97


def test_order_statistic_threshold_and_small_sample_limit():
    assert upper_threshold(np.arange(99),.05)==94
    assert np.isinf(upper_threshold(np.arange(5),.05))


def test_binomial_interval_endpoints_and_counting_rate():
    assert binomial_rate(0,10)['ci95'][0]==0
    assert binomial_rate(10,10)['ci95'][1]==1
    r=binomial_rate(5,10)
    assert r['rate']==.5 and r['ci95'][0]<.5<r['ci95'][1]


def test_modulation_identity_and_antipodal_response():
    vectors=np.array([[1,0,0],[-1,0,0],[0,1,0]])
    sky=np.array([2.,2.,2.])
    np.testing.assert_array_equal(modulate_smoothed_sky(sky,vectors,[3,0,0],0),sky)
    np.testing.assert_allclose(modulate_smoothed_sky(sky,vectors,[3,0,0],.2),[2.4,1.6,2])


@pytest.mark.parametrize('cl', [[1,-1], [1,np.nan]])
def test_invalid_power_rejected(cl):
    with pytest.raises(ValueError): fixed_power_alm(cl,np.random.default_rng(1))

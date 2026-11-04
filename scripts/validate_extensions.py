"""Independent map seed, numerical convergence and executed-source audit."""
from pathlib import Path
import json
import numpy as np
import healpy as hp
from cmb_lab.data import sha256, load_spectra
from cmb_lab.statistics import dl_to_cl, lower_tail
from cmb_lab.map_statistics import MapEstimator, gaussian_alm, transfer, MAP_NAMES, TAIL_SIGNS
from analyze_maps import prepare

root=Path(__file__).resolve().parents[1]
m=json.loads((root/'results/masked_sky/results.json').read_text())
p=json.loads((root/'results/primordial/results.json').read_text())
for result in [m,p]:
    for path,digest in result['source_sha256'].items():
        assert sha256(root/path)==digest, f'Executed source changed: {path}'
config=m['config']
alm,fraction=prepare(root,config,m['source'])
window=transfer(config['nside'],config['input_lmax'],config['smoothing_fwhm_deg'])
e=MapEstimator(fraction>=config['mask_min_fraction'],config['correlation_lmax'],config['axis_nside'])
observed_sky=hp.alm2map(hp.almxfl(alm,window),config['nside'],pol=False)
observed=e.evaluate(observed_sky)[0]
_,t=load_spectra(root,config['input_lmax'])
cl=np.zeros(config['input_lmax']+1); cl[2:]=dl_to_cl(t[:,0],t[:,1])
seed=731444; n=2048; rng=np.random.default_rng(seed)
values=np.array([e.evaluate(hp.alm2map(hp.almxfl(gaussian_alm(cl,rng),window),config['nside'],pol=False))[0] for _ in range(n)])
checks={}
for j,name in enumerate(MAP_NAMES):
    repeat=lower_tail(TAIL_SIGNS[j]*values[:,j],TAIL_SIGNS[j]*observed[j])
    first=m['variants']['baseline']['statistics'][name]
    se=np.sqrt(first['p']*(1-first['p'])/first['n']+repeat['p']*(1-repeat['p'])/n)
    z=abs(repeat['p']-first['p'])/se
    assert z<5, f'Independent map seed unstable: {name}'
    checks[name]={'repeat':repeat,'difference_in_combined_mc_sd':float(z)}
low=MapEstimator(e.mask,lmax=64,axis_nside=config['axis_nside'])
low_value=low.evaluate(observed_sky)[0]
# Refine quadrature pixels while preserving the same continuous bandlimited
# sky and the same union of NSIDE=32 mask cells (including its pixel window).
mask64=hp.ud_grade(e.mask.astype(float),64,order_in='RING',order_out='RING')>.5
refined=MapEstimator(mask64,lmax=95,axis_nside=config['axis_nside'])
sky64=hp.alm2map(hp.almxfl(alm,window),64,pol=False)
fine=refined.evaluate(sky64)[0]
convergence={'L64_relative_to_L95':dict(zip(MAP_NAMES,(low_value/observed-1).tolist())),
             'Nside64_quadrature_relative_to_Nside32':dict(zip(MAP_NAMES,(fine/observed-1).tolist())),
             'scope':'Numerical estimator sensitivity with fixed smoothed harmonic sky and same mask footprint; not an independently recalibrated significance or a native-mask-resolution test.'}
assert abs(low_value[0]/observed[0]-1)<.05, 'Investigate correlation bandlimit sensitivity'
assert np.max(abs(fine/observed-1))<.05, 'Investigate pixel quadrature sensitivity'
for name,variant in m['variants'].items():
    assert abs(variant['variance_closure']['standard_errors'])<5
    assert variant['quadrature_relative_change']<1e-5
out={'status':'passed','source_hashes_verified':True,'independent_seed':seed,'independent_maps':n,
     'checks':checks,'numerical_convergence':convergence,
     'scope':'Numerical validation of the stated models; does not validate absent foreground, noise or parameter uncertainty.'}
(root/'results/extension_validation.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps(out,indent=2))

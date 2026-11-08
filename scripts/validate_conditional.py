"""Validate saved conditional results against source, counting and analytic checks."""
from pathlib import Path
import json
import numpy as np
from cmb_lab.data import sha256
from cmb_lab.statistics import lower_tail
from cmb_lab.map_statistics import MAP_NAMES, TAIL_SIGNS
from cmb_lab.conditional import binomial_rate

root=Path(__file__).resolve().parents[1]
folder=root/'results/conditional'
r=json.loads((folder/'results.json').read_text())
c=r['config']; nr,nc,nv=c['n_reference'],c['n_calibration'],c['n_validation']
assert c==json.loads((root/'config/conditional_analysis.json').read_text())
for path,digest in r['source_sha256'].items():
    assert sha256(root/path)==digest, f'Source changed since execution: {path}'
checks={}
for name,e in r['ensembles'].items():
    data=np.loadtxt(folder/f'{name}_statistics.csv',delimiter=',',skiprows=1)
    assert data.shape==(nr+nc+nv,6) and np.isfinite(data).all()
    for j,key in enumerate(MAP_NAMES):
        s=e['statistics'][key]
        assert lower_tail(TAIL_SIGNS[j]*data[nr:nr+nc,j+2],TAIL_SIGNS[j]*s['observed'])=={k:s[k] for k in ['p','hits','n','ci95']}
    closure=abs(e['variance_closure']['standard_errors'])
    assert closure < 5, f'Analytic variance closure failed: {name}'
    if name!='gaussian': assert e['max_relative_power_preservation_error'] < 1e-10
    cov=e['simultaneous_band']['independent_validation_coverage']
    # A stochastic check at broad tolerance: do not force exactly 95% coverage.
    assert .90 < cov['rate'] < .99
    checks[name]={'variance_closure_standard_errors':closure,'held_out_coverage':cov,
                  'max_tail_validation_difference_standard_errors':max(abs(s['validation_difference_standard_errors']) for s in e['statistics'].values())}
trials=np.loadtxt(folder/'injection_trials.csv',delimiter=',',skiprows=1)
for j,row in enumerate(r['injection']['rows']):
    assert row['detection']==binomial_rate(int(np.sum(trials[:,j+1]>r['injection']['threshold'])),len(trials))
assert .01 < r['injection']['rows'][0]['detection']['rate'] < .10
result={'checks':checks,'source_hashes_valid':True,'csv_tail_counts_valid':True,'injection_counts_valid':True,
        'interpretation':'Numerical and ideal-null calibration validation; does not validate missing observational systematics.'}
(folder/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

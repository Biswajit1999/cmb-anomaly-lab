"""Build the advanced, independently executable Colab research notebook."""
from pathlib import Path
import subprocess
import nbformat as nbf
root=Path(__file__).resolve().parents[1]
revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
cells=[]
def md(s): cells.append(nbf.v4.new_markdown_cell(s))
def code(s): cells.append(nbf.v4.new_code_cell(s))
md('''# Planck CMB: beyond low power
**Author: Biswajit Jana · CMB Anomaly Lab · Research extension v0.3**

This notebook separates angular power, harmonic morphology and orientation relative to the Galactic mask. It executes three ensembles, simultaneous correlation envelopes and a dipole-modulation injection experiment using actual Planck PR3 SMICA measurements.

The saved outputs were executed in a local Python kernel. This notebook is Google Colab compatible; Google infrastructure execution is not claimed. A fresh run downloads about 2 GB, needs sufficient RAM for native map extraction, and runs a CPU Monte Carlo calculation. No Google Drive access is required. ESA/Planck owns the measurements; AI coding/drafting assistance is disclosed in the repository.''')
md('## 1. Set up the pinned scientific code\nThe commit pins the model, configuration and validation code. Results generated later are outputs, not prerequisites.')
code('''import os, sys, subprocess, platform, json, importlib.metadata
from pathlib import Path
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
REVISION='''+repr(revision)+'''
WORK=Path(os.environ.get('CMB_WORKSPACE',str(Path.cwd()/'cmb-advanced-runtime'))).resolve()
if not (WORK/'.git').exists():
    subprocess.run(['git','clone','--quiet','https://github.com/Biswajit1999/cmb-anomaly-lab.git',str(WORK)],check=True)
    subprocess.run(['git','-C',str(WORK),'checkout','--quiet',REVISION],check=True)
actual=subprocess.check_output(['git','-C',str(WORK),'rev-parse','HEAD'],text=True).strip()
assert actual==REVISION, 'Use a clean pinned checkout or a fresh Colab workspace'
subprocess.run([sys.executable,'-m','pip','install','-q','-e',str(WORK)+'[maps]'],check=True,capture_output=True)
sys.path[:0]=[str(WORK/'src'),str(WORK/'scripts')]
print('Author: Biswajit Jana | Python:',platform.python_version())
print('Scientific source revision:',actual)
print('Execution kernel:','Google Colab' if 'google.colab' in sys.modules else 'Local Python / Jupyter')''')
md('## 2. Verify the official data\nThe downloader checks the SHA-256 fingerprint. These are released component-separated measurements, not raw detector timelines.')
code('''import numpy as np
import healpy as hp
import matplotlib.pyplot as plt
from IPython.display import display, Image, Markdown
from cmb_lab.data import fetch
from cmb_lab.conditional import fixed_power_alm, rotated_alm
from cmb_lab.map_statistics import MapEstimator, transfer
from cmb_lab.plots import style, save
from analyze_maps import prepare
from analyze_conditional import run
style()
manifest=fetch(WORK,include_map=True)
print('SMICA bytes:',manifest['smica']['bytes'])
print('SMICA SHA-256:',manifest['smica']['sha256'])
print('Archive:',manifest['smica']['url'])
print({p:importlib.metadata.version(p) for p in ['numpy','scipy','healpy','astropy','SciencePlots']})''')
md('## 3. Prepare measured harmonics and the actual mask\nExtract ell≤128 at native resolution before applying the 5-degree beam and NSIDE=32 pixel window. Fitting monopole/dipole on retained pixels is repeated for every sky.')
code('''config=json.loads((WORK/'config/conditional_analysis.json').read_text())
observed_alm,fraction=prepare(WORK,config,manifest['smica'])
measured=hp.alm2cl(observed_alm)
window=transfer(config['nside'],config['input_lmax'],config['smoothing_fwhm_deg'])
estimator=MapEstimator(fraction>=config['mask_min_fraction'],config['correlation_lmax'],config['axis_nside'])
observed_sky=hp.alm2map(hp.almxfl(observed_alm,window),config['nside'],pol=False)
print('Sky fraction:',estimator.mask.mean(),'| measured full-sky C2:',measured[2])
print('Measured diagnostics [S, variance, pseudo-parity, hemisphere contrast]:')
print(estimator.evaluate(observed_sky)[0])''')
md(r'''## 4. Change morphology while preserving every power
$$\mathbf u_\ell^*=\sqrt{(2\ell+1)\widehat C_\ell}\,\mathbf z_\ell/\|\mathbf z_\ell\|.$$
Normalize the independent real Gaussian harmonic directions. Relative amplitudes and phases change; this is not just multiplying measured complex coefficients by random phases.''')
code('''demo_rng=np.random.default_rng(45871)
conditional_alm=fixed_power_alm(measured,demo_rng)
rotated=rotated_alm(observed_alm,demo_rng)
print('Fixed-power maximum fractional error:',np.max(abs(hp.alm2cl(conditional_alm)[2:]/measured[2:]-1)))
print('Rotation maximum fractional error:',np.max(abs(hp.alm2cl(rotated)[2:]/measured[2:]-1)))''')
md(r'''## 5. See the distinction
$$d\mu(R)=d\alpha\,d\gamma\,d(\cos\beta)/(8\pi^2).$$
A single Haar-uniform global rotation preserves the entire pattern's relative geometry. Independent conditional harmonic directions do not. The mask is fixed in all panels. Synthetic examples below are clearly labelled.''')
code('''OUT=WORK/'results/conditional'
OUT.mkdir(parents=True,exist_ok=True)
fig=plt.figure(figsize=(11,8))
for j,(a,label) in enumerate([(observed_alm,'Measured SMICA'),(conditional_alm,'Synthetic: measured powers fixed'),(rotated,'Measured pattern: random rotation')],1):
    sky=hp.alm2map(hp.almxfl(a,window),config['nside'],pol=False)
    visible=hp.ma(estimator.project(sky)); visible.mask=~estimator.mask
    hp.mollview(visible,fig=fig.number,sub=(3,1,j),min=-120,max=120,cmap='RdBu_r',badcolor='#dddddd',title=label,unit='microkelvin')
save(fig,OUT,'notebook_conditional_maps')
display(Image(filename=str(OUT/'notebook_conditional_maps.png')))''')
md('## 6. Inspect the frozen protocol\nReference sets fit ranks and envelope scales; calibration sets set thresholds and compute tails; held-out sets check behavior. The three nulls ask different questions and their probabilities must not be pooled.')
code('''print(json.dumps(config,indent=2))
print('Null realizations:',3*sum(config[k] for k in ['n_reference','n_calibration','n_validation']))
print('Paired injected maps:',config['n_injection']*len(config['injection_amplitudes']))''')
md('## 7. Execute the full analysis\nThis cell runs the actual ensembles, all four masked-sky diagnostics, finite-grid envelopes, power-preservation checks and paired injections. It does not substitute previously saved results.')
code('''result=run(WORK,config,OUT)
print('Elapsed seconds:',result['elapsed_seconds'])''')
md('## 8. Compare the conditional questions\nThe table reports one-sided local tails and the four-diagnostic family calibration within each ensemble. A conditional probability is not a corrected version of the Gaussian probability.')
code('''summary=(OUT/'SUMMARY.md').read_text()
table=summary.split('![Conditional tails]')[0]
display(Markdown(table))
display(Image(filename=str(OUT/'figures/conditional_tails.png')))''')
md(r'''## 9. Check entire correlation curves
$$M(C)=\max_{\theta\in\{60^\circ,\ldots,180^\circ\}} |(C(\theta)-\mu_{\rm ref}(\theta))/s_{\rm ref}(\theta)|.$$
The envelope is calibrated on an independent sample and checked on held-out skies. It is simultaneous only on the declared 121-angle grid. Its two-sided score does not measure the same event as a small S integral.''')
code('''display(Image(filename=str(OUT/'figures/simultaneous_envelopes.png')))
for name,r in result['ensembles'].items():
    print(name,'coverage:',r['simultaneous_band']['independent_validation_coverage'])
    print('Analytic projected-variance closure:',r['variance_closure'])''')
md(r'''## 10. Measure the detector's sensitivity
$$T_A(\hat n)=[1+A\hat n\cdot\hat p]T_{\rm smoothed}(\hat n).$$
This illustrative signal is injected **after smoothing**. It is not a primordial transfer model or a measurement of A. Each amplitude uses the same underlying skies, with a fixed axis chosen before execution. Every trial repeats the 24-axis search.''')
code('''display(Image(filename=str(OUT/'figures/injection_recovery.png')))
print('Fixed detection threshold:',result['injection']['threshold'])
for row in result['injection']['rows']:
    print('A=',row['amplitude'],'detection:',row['detection'],'median unsigned axis error:',row['median_axis_error_deg'])''')
md('## 11. Independently validate saved results\nRecount the published CSV tails and injected detections, check source hashes, exact power conservation, ensemble variance closure and held-out envelope coverage.')
code('''check=subprocess.run([sys.executable,str(WORK/'scripts/validate_conditional.py')],check=True,capture_output=True,text=True)
print(check.stdout)''')
md('## 12. Inspect the limits before interpreting the numbers\nFull-sky component-separated harmonics include uncertain Galactic regions. Filtering before masking can mix those regions into retained pixels. Noise, foreground residuals and cosmological-parameter uncertainty are not propagated. These retrospective randomization diagnostics establish neither a new physical origin nor a project-wide discovery significance.')
code('''print(result['interpretation'])
print(result['injection']['interpretation'])
print('Executed scientific source hashes:')
print(json.dumps(result['source_sha256'],indent=2))''')
md('## 13. Export the numerical work\nDownloadable CSV, JSON and figures are included. Raw FITS and intermediate ensembles are excluded from this small archive.')
code('''from zipfile import ZipFile, ZIP_DEFLATED
archive=WORK/'results/cmb_conditional_research_outputs.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file() and p.suffix in {'.csv','.json','.png','.pdf','.md'}:
            z.write(p,p.relative_to(WORK/'results'))
print('Export:',archive.name,'| bytes:',archive.stat().st_size)
from IPython.display import FileLink
display(FileLink(str(archive)))''')
md('''## Sources and credit
- [Planck 2018 VII](https://arxiv.org/abs/1906.02552)
- [Efstathiou, Ma and Hanson (2010)](https://arxiv.org/abs/0911.5399)
- [Akrami et al. (2014)](https://arxiv.org/abs/1402.0870)
- [Full method derivation and limitations](https://biswajit1999.github.io/cmb-anomaly-lab/docs/conditional-methods.html)

**Biswajit Jana · CMB Anomaly Lab.** Measurements: ESA/Planck; distribution: NASA/IPAC IRSA. Software: HEALPix/healpy, NumPy, SciPy, SciencePlots. AI assistance is disclosed in AUTHORS.md.''')
nb=nbf.v4.new_notebook(cells=cells,metadata={'authors':[{'name':'Biswajit Jana'}],
    'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
    'language_info':{'name':'python'},'research':{'source_revision':revision,'execution':'Local kernel; Colab compatible'}})
nbf.write(nb,root/'notebooks/Planck_CMB_Advanced_Inference.ipynb')
print(f'Created {len(cells)} cells, {sum(c.cell_type=="code" for c in cells)} code cells, revision {revision}')

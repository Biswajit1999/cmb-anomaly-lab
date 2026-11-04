"""Run SMICA cut-sky diagnostics and an independent Gaussian calibration."""
from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime, timezone
import importlib.metadata
import json
import time
import numpy as np
import healpy as hp
from astropy.io import fits
from cmb_lab.data import sha256, load_spectra
from cmb_lab.statistics import dl_to_cl, lower_tail, family_min_p
from cmb_lab.map_statistics import MapEstimator, gaussian_alm, transfer, MAP_NAMES, TAIL_SIGNS
from cmb_lab.plots import style, save, BLUE, RED
import matplotlib.pyplot as plt


def prepare(root, config, record):
    source = root / record['path']
    if sha256(source) != record['sha256']:
        raise ValueError('SMICA checksum mismatch')
    cache = root / 'tmp/map-input.npz'
    cache.parent.mkdir(exist_ok=True)
    key = f"{record['sha256']}:{config['input_lmax']}:{config['nside']}:v2"
    if cache.exists():
        with np.load(cache) as z:
            if str(z['key']) == key:
                return z['alm'], z['mask_fraction']
    with fits.open(source, memmap=True) as hdus:
        hdu = hdus[1]
        if hdu.columns['I_STOKES'].unit != 'K_CMB' or hdu.header['ORDERING'] != 'NESTED':
            raise ValueError('Unexpected map units/order')
        native = np.asarray(hdu.data['I_STOKES'].ravel(), dtype=float)*1e6
        if not np.isfinite(native).all() or np.any(abs(native) > 1e9):
            raise ValueError('Invalid native temperature pixels')
        native = hp.reorder(native, n2r=True)
        # Extract low harmonics at native resolution, BEFORE any degradation.
        alm = hp.map2alm(native, lmax=config['input_lmax'], iter=0)
        native_window = hp.gauss_beam(np.deg2rad(5/60), lmax=config['input_lmax'])
        native_window *= hp.pixwin(hdu.header['NSIDE'], lmax=config['input_lmax'])
        alm = hp.almxfl(alm, 1/native_window)
        ls, _ = hp.Alm.getlm(config['input_lmax'])
        alm[ls < 2] = 0
        fraction = hp.ud_grade(hdu.data['TMASK'].ravel().astype(float), config['nside'], order_in='NESTED', order_out='RING')
    np.savez_compressed(cache, alm=alm, mask_fraction=fraction, key=key)
    return alm, fraction


def run(root, config, out):
    start = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root/'data/manifest.json').read_text())
    print('Verifying native SMICA input and extracting low harmonics...', flush=True)
    observed_alm, fraction = prepare(root, config, manifest['smica'])
    _, tt = load_spectra(root, config['input_lmax'])
    cl = np.zeros(config['input_lmax']+1)
    cl[2:] = dl_to_cl(tt[:, 0], tt[:, 1])
    variants = [dict(name='baseline', mask_min_fraction=config['mask_min_fraction'],
                     smoothing_fwhm_deg=config['smoothing_fwhm_deg'])] + config['robustness']
    estimators = [MapEstimator(fraction >= v['mask_min_fraction'], config['correlation_lmax'], config['axis_nside']) for v in variants]
    windows = [transfer(config['nside'], config['input_lmax'], v['smoothing_fwhm_deg']) for v in variants]
    observed = []
    maps, cls, contrasts = [], [], []
    for e, w in zip(estimators, windows):
        sky = hp.alm2map(hp.almxfl(observed_alm, w), config['nside'], pol=False)
        value, power, contrast = e.evaluate(sky)
        observed.append(value)
        maps.append(sky); cls.append(power); contrasts.append(contrast)
    observed = np.array(observed)
    seeds = np.random.SeedSequence(config['seed']).spawn(2)
    batches, corr_samples = [], []
    theta = np.linspace(0, 180, 181)
    for batch, n in enumerate([config['n_reference'], config['n_calibration']]):
        rng = np.random.default_rng(seeds[batch])
        values = np.empty((n, len(variants), len(MAP_NAMES)))
        for i in range(n):
            alm = gaussian_alm(cl, rng)
            for j, (e, w) in enumerate(zip(estimators, windows)):
                sky = hp.alm2map(hp.almxfl(alm, w), config['nside'], pol=False)
                values[i, j], power, _ = e.evaluate(sky)
                if batch == 1 and j == 0:
                    corr_samples.append(e.correlation(power, theta))
            if (i+1) % 512 == 0:
                print(f'Batch {batch+1}: {i+1}/{n} skies; {time.perf_counter()-start:.0f}s', flush=True)
        batches.append(values)
    reference, calibration = batches
    result = {'config': config, 'variants': {}, 'source': manifest['smica'],
              'interpretation': 'Matched finite-band map estimators under an ideal Gaussian CMB-only null; not Planck end-to-end likelihood significances.',
              'packages': {p: importlib.metadata.version(p) for p in ['numpy','scipy','healpy','astropy','SciencePlots']},
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'source_sha256': {str(p.relative_to(root)): sha256(p) for p in [Path(__file__).resolve(), root/'src/cmb_lab/map_statistics.py']}}
    for j, (v, e, w) in enumerate(zip(variants, estimators, windows)):
        rows = {}
        for k, name in enumerate(MAP_NAMES):
            rows[name] = dict(observed=float(observed[j, k]), tail='upper' if TAIL_SIGNS[k]<0 else 'lower',
                             **lower_tail(TAIL_SIGNS[k]*calibration[:, j, k], TAIL_SIGNS[k]*observed[j, k]))
        analytic = e.expected_variance(cl*w*w)
        sample = calibration[:, j, 1]
        closure_z = (sample.mean()-analytic)/(sample.std(ddof=1)/np.sqrt(len(sample)))
        strict = MapEstimator(e.mask, e.lmax, e.axis_nside, nquad=384)
        quad_s = strict.evaluate(maps[j])[0][0]
        result['variants'][v['name']] = dict(settings=v, f_sky=float(e.mask.mean()), statistics=rows,
            family=family_min_p(reference[:, j]*TAIL_SIGNS, calibration[:, j]*TAIL_SIGNS, observed[j]*TAIL_SIGNS),
            variance_closure=dict(analytic=analytic, simulation_mean=float(sample.mean()), standard_errors=float(closure_z)),
            quadrature_relative_change=float(abs(quad_s/observed[j, 0]-1)),
            axis_count=len(e.axes), maximizing_axis_galactic_lon_lat_deg=[float(x.item()) for x in hp.vec2ang(e.axes[np.argmax(contrasts[j])], lonlat=True)])
    signed_ref = (reference*TAIL_SIGNS).reshape(len(reference), -1)
    signed_cal = (calibration*TAIL_SIGNS).reshape(len(calibration), -1)
    result['all_variants_family'] = family_min_p(signed_ref, signed_cal, (observed*TAIL_SIGNS).ravel())
    result['elapsed_seconds'] = time.perf_counter()-start
    np.savez_compressed(out/'ensembles.npz', reference=reference, calibration=calibration,
                        observed=observed, correlations=np.array(corr_samples), theta=theta)
    np.savetxt(out/'simulation_statistics.csv', np.column_stack([np.arange(len(calibration)), calibration.reshape(len(calibration), -1)]), delimiter=',',
        header='id,'+','.join(v['name']+'_'+name for v in variants for name in MAP_NAMES), comments='')
    np.savetxt(out/'observed_correlation.csv', np.column_stack([theta, estimators[0].correlation(cls[0], theta)]), delimiter=',', header='theta_deg,correlation_uK2', comments='')
    (out/'results.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    plot(out, estimators, maps, observed, calibration, np.array(corr_samples), theta, cls, result)
    lines = ['# Measured SMICA map analysis', '', result['interpretation'], '', '| Variant | Statistic | Observed | Tail p | 95% MC interval |','|---|---|---:|---:|---|']
    for v, r in result['variants'].items():
        for name, s in r['statistics'].items():
            lines.append(f"| {v} | {name} | {s['observed']:.6g} | {s['p']:.5f} | {s['ci95'][0]:.5f} - {s['ci95'][1]:.5f} |")
    lines += ['', f"Twelve-column family calibration: {result['all_variants_family']['p']:.5f}. This covers these variants, not historical statistic selection.", '', 'The hemisphere statistic includes the complete finite direction search on every realization. The pseudo-parity statistic is a mask-dependent diagnostic, not a full-sky power estimate.']
    (out/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result['variants']['baseline'], indent=2), flush=True)


def plot(out, estimators, maps, observed, calibration, curves, theta, cls, result):
    style(); folder = out/'figures'; folder.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9,4.5), layout='constrained')
    q = np.quantile(curves,[.025,.16,.5,.84,.975],axis=0)
    ax.fill_between(theta,q[0],q[4],color=BLUE,alpha=.12,label='95% pointwise Gaussian range')
    ax.fill_between(theta,q[1],q[3],color=BLUE,alpha=.23,label='68% pointwise range')
    ax.plot(theta,q[2],color=BLUE,label='Simulation median')
    ax.plot(theta,estimators[0].correlation(cls[0],theta),color=RED,label='Measured SMICA, masked and projected')
    ax.axvline(60,color='gray',ls='--'); ax.axhline(0,color='gray',lw=.5)
    ax.set(xlim=(0,180),xlabel=r'$\theta$ [degrees]',ylabel=r'$\widehat C_W(\theta)$ [$\mu$K$^2$]',title='Cut-sky correlation: matched finite-band estimator')
    ax.legend(fontsize=8); save(fig,folder,'cut_sky_correlation')
    fig, axes = plt.subplots(2,2,figsize=(10,7),layout='constrained')
    labels=[r'$S^{W}_{1/2}$ [$\mu$K$^4$]',r'$V_W$ [$\mu$K$^2$]',r'$R^{\rm pseudo}_{2:29}$',r'$A_{\rm max}$']
    for k,ax in enumerate(axes.flat):
        sample=calibration[:,0,k]
        bins=np.geomspace(max(sample.min(),1e-9),sample.max(),55) if k==0 else 45
        ax.hist(sample,bins=bins,density=True,color=BLUE,alpha=.7)
        ax.axvline(observed[0,k],color=RED,label='SMICA')
        if k==0: ax.set_xscale('log')
        r=result['variants']['baseline']['statistics'][MAP_NAMES[k]]
        ax.set(xlabel=labels[k],ylabel='Density',title=f"{r['tail'].capitalize()} tail p = {r['p']:.4f}"); ax.legend(fontsize=8)
    save(fig,folder,'map_null_distributions')
    fig,ax=plt.subplots(figsize=(9,4.4),layout='constrained')
    for j,(name,r) in enumerate(result['variants'].items()):
        p=np.array([r['statistics'][n]['p'] for n in MAP_NAMES])
        ci=np.array([r['statistics'][n]['ci95'] for n in MAP_NAMES]).T
        # Clopper-Pearson interval describes the underlying rate; plus-one point can
        # lie outside it in extreme cases, so draw intervals independently.
        x=np.arange(4)+.18*(j-1)
        ax.vlines(x,ci[0],ci[1],color=[BLUE,RED,'#4477AA'][j])
        ax.plot(x,p,'o',color=[BLUE,RED,'#4477AA'][j],label=name.replace('_',' '))
    ax.set_xticks(range(4),['Large-angle correlation','Variance','Pseudo-parity','Direction scan'])
    ax.set(yscale='log',ylabel='Local tail probability',title='Processing sensitivity with Monte Carlo intervals')
    ax.legend(fontsize=8); save(fig,folder,'map_robustness')
    visible=hp.ma(estimators[0].project(maps[0])); visible.mask=~estimators[0].mask
    fig=plt.figure(figsize=(10,5.4))
    hp.mollview(visible,fig=fig.number,min=-120,max=120,cmap='RdBu_r',badcolor='#dddddd',title='SMICA analysis sky: 5 degree beam, NSIDE 32',unit=r'$\mu$K')
    save(fig,folder,'analysis_sky')


if __name__ == '__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--quick',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'config/map_analysis.json').read_text())
    if args.quick: config.update(n_reference=32,n_calibration=32)
    run(root,config,args.output or root/('results/quick/maps' if args.quick else 'results/masked_sky'))

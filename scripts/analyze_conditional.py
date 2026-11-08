"""Separate angular power, harmonic morphology and mask orientation on real SMICA."""
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
import importlib.metadata
import json
import time
import numpy as np
import healpy as hp
import matplotlib.pyplot as plt
from analyze_maps import prepare
from cmb_lab.data import sha256, load_spectra
from cmb_lab.statistics import dl_to_cl, lower_tail, family_min_p
from cmb_lab.map_statistics import MapEstimator, gaussian_alm, transfer, MAP_NAMES, TAIL_SIGNS
from cmb_lab.conditional import (fixed_power_alm, rotated_alm, SimultaneousBand,
    upper_threshold, binomial_rate, modulate_smoothed_sky)
from cmb_lab.plots import style, save, BLUE, RED

LABELS={'gaussian':'Gaussian theory', 'fixed_power':'Measured powers fixed', 'rotation':'Measured pattern rotated'}


def sample_ensemble(name, observed_alm, theory, measured, window, estimator, theta, config, seed):
    rng=np.random.default_rng(seed)
    n=config['n_reference']+config['n_calibration']+config['n_validation']
    values=np.empty((n,4)); curves=np.empty((n,len(theta)))
    max_power_error=0.; start=time.perf_counter()
    for i in range(n):
        if name=='gaussian': alm=gaussian_alm(theory,rng)
        elif name=='fixed_power': alm=fixed_power_alm(measured,rng)
        else: alm=rotated_alm(observed_alm,rng)
        if name!='gaussian':
            error=np.max(np.abs(hp.alm2cl(alm)[2:]/measured[2:]-1))
            max_power_error=max(max_power_error,float(error))
        sky=hp.alm2map(hp.almxfl(alm,window),config['nside'],pol=False)
        values[i],pseudo,_=estimator.evaluate(sky)
        curves[i]=estimator.correlation(pseudo,theta)
        if (i+1)%512==0 or i+1==n:
            print(f'{name}: {i+1}/{n}; {time.perf_counter()-start:.1f}s',flush=True)
    return values,curves,max_power_error


def summarize(values,curves,observed,observed_curve,config,analytic_variance):
    nr,nc=config['n_reference'],config['n_calibration']
    reference,calibration,validation=values[:nr],values[nr:nr+nc],values[nr+nc:]
    rows={}
    for k,name in enumerate(MAP_NAMES):
        primary=lower_tail(TAIL_SIGNS[k]*calibration[:,k],TAIL_SIGNS[k]*observed[k])
        check=lower_tail(TAIL_SIGNS[k]*validation[:,k],TAIL_SIGNS[k]*observed[k])
        pooled=(primary['hits']+check['hits'])/(nc+len(validation))
        se=np.sqrt(max(pooled*(1-pooled),1/(nc+len(validation)))*(1/nc+1/len(validation)))
        rows[name]={'observed':float(observed[k]),'tail':'upper' if TAIL_SIGNS[k]<0 else 'lower',
                    **primary,'validation':check,'validation_difference_standard_errors':float((primary['p']-check['p'])/se)}
    band=SimultaneousBand.fit(curves[:nr])
    low,high,cutoff=band.bounds(curves[nr:nr+nc],config['alpha'])
    cal_scores=band.score(curves[nr:nr+nc])
    obs_score=float(band.score(observed_curve))
    validation_scores=band.score(curves[nr+nc:])
    coverage=binomial_rate(int(np.sum(validation_scores<=cutoff)),len(validation_scores))
    sample=calibration[:,1]
    result={'statistics':rows,
            'four_diagnostic_family':family_min_p(reference*TAIL_SIGNS,calibration*TAIL_SIGNS,observed*TAIL_SIGNS),
            'simultaneous_band':{'alpha':config['alpha'],'cutoff':cutoff,'observed_max_studentized_deviation':obs_score,
                'upper_tail':lower_tail(-cal_scores,-obs_score),'independent_validation_coverage':coverage,
                'scope':'Two-sided prediction envelope on the declared finite angular grid; not a low-correlation S test, not a confidence interval for the mean.'},
            'variance_closure':{'analytic':analytic_variance,'calibration_mean':float(sample.mean()),
                'standard_errors':float((sample.mean()-analytic_variance)/(sample.std(ddof=1)/np.sqrt(nc)))}}
    return result,np.column_stack([band.center,low,high])


def injection_study(estimator,window,theory,config,seed,threshold,out):
    rng=np.random.default_rng(seed)
    axis=np.array(hp.ang2vec(*config['injection_axis_lon_lat_deg'],lonlat=True))
    amplitudes=config['injection_amplitudes']; n=config['n_injection']
    contrasts=np.empty((n,len(amplitudes))); errors=np.empty_like(contrasts)
    for i in range(n):
        sky=hp.alm2map(hp.almxfl(gaussian_alm(theory,rng),window),config['nside'],pol=False)
        for j,a in enumerate(amplitudes):
            injected=modulate_smoothed_sky(sky,estimator.vec,axis,a)
            _,_,directions=estimator.evaluate(injected)
            best=int(np.argmax(directions)); contrasts[i,j]=directions[best]
            errors[i,j]=np.rad2deg(np.arccos(np.clip(abs(estimator.axes[best]@axis),0,1)))
        if (i+1)%256==0 or i+1==n: print(f'Paired injections: {i+1}/{n}',flush=True)
    rows=[]
    for j,a in enumerate(amplitudes):
        rows.append({'amplitude':a,'detection':binomial_rate(int(np.sum(contrasts[:,j]>threshold)),n),
                     'median_axis_error_deg':float(np.median(errors[:,j])),
                     'axis_error_interval68_deg':[float(x) for x in np.quantile(errors[:,j],[.16,.84])]})
    np.savetxt(out/'injection_trials.csv',np.column_stack([np.arange(n),contrasts,errors]),delimiter=',',
        header='id,'+','.join(f'contrast_A{a}' for a in amplitudes)+','+','.join(f'axis_error_deg_A{a}' for a in amplitudes),comments='')
    return {'threshold':threshold,'alpha':config['alpha'],'rows':rows,'axis_lon_lat_deg':config['injection_axis_lon_lat_deg'],
            'interpretation':'Detection power of a toy dipole modulation applied AFTER 5-degree smoothing; not an inferred primordial amplitude. Each row uses the same underlying skies, so rates across amplitudes are correlated. The maximizing axis is unsigned and searched over 24 directions.'}


def plot(out,result,curves_table):
    style(); folder=out/'figures'; folder.mkdir(exist_ok=True)
    palette=[BLUE,RED,'#4477AA']
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    for j,(name,r) in enumerate(result['ensembles'].items()):
        x=np.arange(4)+.2*(j-1)
        p=[r['statistics'][k]['p'] for k in MAP_NAMES]
        ci=np.array([r['statistics'][k]['ci95'] for k in MAP_NAMES])
        ax.vlines(x,ci[:,0],ci[:,1],color=palette[j]); ax.plot(x,p,'o',color=palette[j],label=LABELS[name])
    ax.set_xticks(range(4),['Large-angle\ncorrelation','Masked\nvariance','Pseudo-\nparity','Hemisphere\nsearch'])
    ax.set(yscale='log',ylabel='Conditional or unconditional tail probability',title='Different questions, different null ensembles')
    ax.legend(fontsize=8); save(fig,folder,'conditional_tails')
    fig,axes=plt.subplots(3,1,figsize=(9,9),sharex=True,layout='constrained')
    for j,(name,r) in enumerate(result['ensembles'].items()):
        t=curves_table[name]; ax=axes[j]
        ax.fill_between(t[:,0],t[:,3],t[:,4],color=palette[j],alpha=.18,label='95% finite-grid simultaneous envelope')
        ax.plot(t[:,0],t[:,2],color=palette[j],lw=1,label='Reference mean')
        ax.plot(t[:,0],t[:,1],color='#222222',lw=1.4,label='Measured SMICA')
        ax.axhline(0,color='gray',lw=.5)
        ax.set(ylabel=r'$C_W(\theta)$ [$\mu$K$^2$]',title=LABELS[name]+f"; two-sided max-deviation p={r['simultaneous_band']['upper_tail']['p']:.3f}")
        if j==0: ax.legend(fontsize=7,loc='lower right')
    axes[-1].set(xlabel=r'$\theta$ [degrees]',xlim=(60,180)); save(fig,folder,'simultaneous_envelopes')
    rows=result['injection']['rows']; amps=[r['amplitude'] for r in rows]
    rates=np.array([r['detection']['rate'] for r in rows]); ci=np.array([r['detection']['ci95'] for r in rows])
    fig,axes=plt.subplots(1,2,figsize=(9,4),layout='constrained')
    axes[0].vlines(amps,ci[:,0],ci[:,1],color=BLUE)
    axes[0].plot(amps,rates,'o-',color=BLUE)
    axes[0].axhline(.05,color=RED,ls='--',label='Nominal false-alarm level')
    axes[0].set(xlabel='Injected modulation amplitude',ylabel='Detection fraction',ylim=(0,1),title='Power of the 24-axis test'); axes[0].legend(fontsize=7)
    errors=np.array([r['axis_error_interval68_deg'] for r in rows])
    axes[1].fill_between(amps,errors[:,0],errors[:,1],color=BLUE,alpha=.15,label='Central 68% of trials')
    axes[1].plot(amps,[r['median_axis_error_deg'] for r in rows],'o-',color=BLUE,label='Median, all trials')
    axes[1].set(xlabel='Injected modulation amplitude',ylabel='Unsigned direction error [degrees]',ylim=(0,90),title='Direction recovery'); axes[1].legend(fontsize=7)
    save(fig,folder,'injection_recovery')


def run(root,config,out):
    start=time.perf_counter(); out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((root/'data/manifest.json').read_text())
    observed_alm,fraction=prepare(root,config,manifest['smica'])
    measured=hp.alm2cl(observed_alm)
    _,tt=load_spectra(root,config['input_lmax'])
    theory=np.zeros(config['input_lmax']+1); theory[2:]=dl_to_cl(tt[:,0],tt[:,1])
    estimator=MapEstimator(fraction>=config['mask_min_fraction'],config['correlation_lmax'],config['axis_nside'])
    window=transfer(config['nside'],config['input_lmax'],config['smoothing_fwhm_deg'])
    observed,pseudo,_=estimator.evaluate(hp.alm2map(hp.almxfl(observed_alm,window),config['nside'],pol=False))
    theta=np.arange(config['theta_min_deg'],config['theta_max_deg']+1,config['theta_step_deg'])
    observed_curve=estimator.correlation(pseudo,theta)
    seeds=np.random.SeedSequence(config['seed']).spawn(4)
    code=[Path(__file__).resolve(),root/'src/cmb_lab/conditional.py',root/'src/cmb_lab/map_statistics.py',root/'scripts/analyze_maps.py']
    result={'config':config,'created_utc':datetime.now(timezone.utc).isoformat(),'ensembles':{},'f_sky':float(estimator.mask.mean()),
        'source':manifest['smica'],'source_sha256':{str(p.relative_to(root)):sha256(p) for p in code},
        'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','healpy','astropy','SciencePlots']},
        'seed_spawn_keys':{n:list(s.spawn_key) for n,s in zip([*LABELS,'injection'],seeds)},
        'interpretation':'Exploratory CMB-only randomization diagnostics. The fixed powers and rotated pattern come from a processed full-sky component-separated map, including uncertain foreground regions. Smoothing before masking can mix these regions into retained pixels. Neither conditional ensemble removes this systematic uncertainty or constitutes an independent observation.'}
    tables={}; nr,nc=config['n_reference'],config['n_calibration']
    for name,seed in zip(LABELS,seeds):
        values,curves,power_error=sample_ensemble(name,observed_alm,theory,measured,window,estimator,theta,config,seed)
        analytic=estimator.expected_variance((theory if name=='gaussian' else measured)*window**2)
        r,band=summarize(values,curves,observed,observed_curve,config,analytic)
        r['max_relative_power_preservation_error']=power_error if name!='gaussian' else None
        result['ensembles'][name]=r
        tables[name]=np.column_stack([theta,observed_curve,band])
        np.savetxt(out/f'{name}_correlation.csv',tables[name],delimiter=',',header='theta_deg,observed,reference_mean,simultaneous_low,simultaneous_high',comments='')
        split=np.r_[np.zeros(nr),np.ones(nc),np.full(config['n_validation'],2)]
        np.savetxt(out/f'{name}_statistics.csv',np.column_stack([np.arange(len(values)),split,values]),delimiter=',',header='id,split_0reference_1calibration_2validation,'+','.join(MAP_NAMES),comments='')
        np.savez_compressed(out/f'{name}_ensembles.npz',values=values,curves=curves)
        if name=='gaussian': threshold=upper_threshold(values[nr:nr+nc,3],config['alpha'])
    result['injection']=injection_study(estimator,window,theory,config,seeds[3],threshold,out)
    result['elapsed_seconds']=time.perf_counter()-start
    (out/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    np.savetxt(out/'conditioning_spectrum.csv',np.column_stack([np.arange(len(theory)),theory,measured,window]),delimiter=',',header='ell,theory_Cl_uK2,measured_fullsky_Cl_uK2,beam_times_pixel_window',comments='')
    plot(out,result,tables)
    lines=['# Conditional morphology and orientation experiments','','Author: Biswajit Jana','',result['interpretation'],'',
        '| Ensemble | S lower tail | Variance lower tail | Pseudo-parity lower tail | Hemisphere upper tail | Four-test family |',
        '|---|---:|---:|---:|---:|---:|']
    for name,r in result['ensembles'].items():
        lines.append('| '+LABELS[name]+' | '+' | '.join(f"{r['statistics'][k]['p']:.5f}" for k in MAP_NAMES)+f" | {r['four_diagnostic_family']['p']:.5f} |")
    lines+=['','These are three different null hypotheses; their p-values are not multiplied, pooled, or combined with earlier studies. Counting intervals, independent validation and analytic closure are in [results.json](results.json).',
        '',f"Per ensemble: {nr} reference, {nc} calibration and {config['n_validation']} held-out validation skies. Three ensembles total {3*(nr+nc+config['n_validation']):,} realizations.",'',
        '![Conditional tails](figures/conditional_tails.png)','','![Finite-grid envelopes](figures/simultaneous_envelopes.png)','','![Injection recovery](figures/injection_recovery.png)','',
        result['injection']['interpretation'],'','| Injected A | Detection rate | 95% counting interval | Median unsigned axis error |','|---|---:|---|---:|']
    for row in result['injection']['rows']:
        d=row['detection']; lines.append(f"| {row['amplitude']:.2f} | {d['rate']:.4f} | {d['ci95'][0]:.4f} - {d['ci95'][1]:.4f} | {row['median_axis_error_deg']:.1f} deg |")
    (out/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print(f'Completed in {result["elapsed_seconds"]:.1f}s: {out}',flush=True)
    return result


if __name__=='__main__':
    parser=ArgumentParser(description=__doc__); parser.add_argument('--quick',action='store_true'); parser.add_argument('--output',type=Path)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'config/conditional_analysis.json').read_text())
    if args.quick: config.update(n_reference=32,n_calibration=32,n_validation=32,n_injection=32)
    run(root,config,args.output or root/('results/quick/conditional' if args.quick else 'results/conditional'))

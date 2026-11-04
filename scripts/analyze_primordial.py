"""CAMB transfer calculation, finite model search, and parametric bootstrap."""
from pathlib import Path
from datetime import datetime, timezone
import json
import importlib.metadata
import numpy as np
import camb
from cmb_lab.data import load_spectra, sha256
from cmb_lab.statistics import dl_to_cl, simulate, lower_tail
from cmb_lab.primordial import primordial_power, improvement_grid, conditional_ee
from cmb_lab.plots import style, save, BLUE, RED
import matplotlib.pyplot as plt


def camb_transfer(config, accuracy=1):
    pars=camb.set_params(**config['cosmology'], lmax=config['prediction_lmax'])
    pars.DoLensing=False
    pars.NonLinear=camb.model.NonLinear_none
    pars.set_accuracy(AccuracyBoost=accuracy, lAccuracyBoost=accuracy, lSampleBoost=accuracy)
    return camb.get_transfer_functions(pars)


def spectrum(results, config, amplitude, cutoff):
    k=np.geomspace(1e-7,10,5000)
    p=primordial_power(k,amplitude,cutoff,As=config['cosmology']['As'],ns=config['cosmology']['ns'])
    initial=camb.initialpower.SplinedInitialPower()
    initial.set_scalar_table(k,p)
    results.power_spectra_from_transfer(initial)
    return results.get_unlensed_scalar_cls(lmax=config['prediction_lmax'],CMB_unit='muK',raw_cl=True)


def main():
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'config/primordial_analysis.json').read_text())
    out=root/'results/primordial'; out.mkdir(parents=True,exist_ok=True)
    kcs=np.geomspace(config['cutoff_min_mpc_inverse'],config['cutoff_max_mpc_inverse'],config['cutoff_count'])
    amps=np.linspace(0,1,config['amplitude_steps'])
    print('Computing CAMB scalar transfer functions...',flush=True)
    transfer=camb_transfer(config)
    base=spectrum(transfer,config,0,kcs[0])
    full=np.array([spectrum(transfer,config,1,k) for k in kcs])
    # Unlensed scalar spectra depend linearly on the primordial power.
    grid=np.array([base+a*(f-base) for a in amps for f in full])
    ell=np.arange(config['fit_lmin'],config['fit_lmax']+1)
    observed, official=load_spectra(root,config['prediction_lmax'])
    obs=dl_to_cl(observed[:,0],observed[:,1])
    theory=dl_to_cl(official[:,0],official[:,1])
    scores=improvement_grid(obs[:len(ell)],base[ell,0],grid[:,ell,0],ell)
    best=int(np.argmax(scores)); ai,ki=np.unravel_index(best,(len(amps),len(kcs)))
    rng=np.random.default_rng(config['seed'])
    sims=simulate(ell,base[ell,0],config['n_calibration'],rng)
    # Chunking keeps memory bounded even for a much larger model grid.
    maxima=np.concatenate([improvement_grid(sims[i:i+2000],base[ell,0],grid[:,ell,0],ell).max(axis=1)
                           for i in range(0,len(sims),2000)])
    calibrated=lower_tail(-maxima,-float(scores[best]))
    high=camb_transfer(config,accuracy=2)
    high_base=spectrum(high,config,0,kcs[0])
    high_best=spectrum(high,config,float(amps[ai]),float(kcs[ki]))
    high_score=float(improvement_grid(obs[:len(ell)],high_base[ell,0],high_best[None,ell,0],ell)[0])
    selected=grid[best]
    predictions=[]
    for name,c in [('baseline',base),('fitted',selected)]:
        predictions.append(conditional_ee(c[2:,0],c[2:,1],c[2:,3],obs))
    result={'config':config,'created_utc':datetime.now(timezone.utc).isoformat(),
        'best_amplitude':float(amps[ai]),'best_cutoff_mpc_inverse':float(kcs[ki]),
        'best_twice_log_likelihood_improvement':float(scores[best]),'search_calibrated_p':calibrated,
        'grid_entries':len(grid),'distinct_models':1+(len(amps)-1)*len(kcs),
        'baseline_max_fractional_TT_difference_from_official_ell2_29':float(np.max(abs(base[ell,0]/theory[:len(ell)]-1))),
        'accuracy_check':{'accuracy_boost':2,'best_model_improvement':high_score,
            'improvement_absolute_difference':abs(high_score-float(scores[best])),
            'max_TT_fractional_change_ell2_29':float(np.max(abs(high_best[ell,0]/selected[ell,0]-1)))},
        'interpretation':'Exploratory fixed-background, unlensed linear scalar transfer model. Published TT points enter an ideal full-sky likelihood proxy. Search-calibrated frequentist p, not a Bayes factor or posterior. EE/TE are predictions only.',
        'packages':{p:importlib.metadata.version(p) for p in ['camb','numpy','scipy','SciencePlots']},
        'input_sha256':{k:v['sha256'] for k,v in json.loads((root/'data/manifest.json').read_text()).items() if k in ['observed','theory']},
        'source_sha256':{str(p.relative_to(root)):sha256(p) for p in [Path(__file__).resolve(),root/'src/cmb_lab/primordial.py']}}
    (out/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    np.savetxt(out/'model_grid.csv',np.column_stack([np.repeat(amps,len(kcs)),np.tile(kcs,len(amps)),scores]),delimiter=',',header='amplitude,cutoff_Mpc_inverse,twice_log_likelihood_improvement',comments='')
    np.savetxt(out/'predictions.csv',np.column_stack([np.arange(2,len(base)),base[2:,0],selected[2:,0],base[2:,1],selected[2:,1],base[2:,3],selected[2:,3],*predictions]),delimiter=',',header='ell,baseline_TT,fitted_TT,baseline_EE,fitted_EE,baseline_TE,fitted_TE,baseline_EE_given_TT,fitted_EE_given_TT',comments='')
    np.savez_compressed(out/'bootstrap.npz',maxima=maxima)
    style(); folder=out/'figures'; folder.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained')
    im=axes[0].pcolormesh(kcs,amps,scores.reshape(len(amps),len(kcs)),shading='nearest',cmap='RdBu_r')
    axes[0].plot(kcs[ki],amps[ai],'kx'); axes[0].set(xscale='log',xlabel=r'$k_c$ [Mpc$^{-1}$]',ylabel=r'Suppression $A$',title=r'Ideal TT $2\Delta\ln\mathcal{L}$')
    fig.colorbar(im,ax=axes[0])
    axes[1].hist(maxima,bins=60,density=True,color=BLUE,alpha=.75)
    axes[1].axvline(scores[best],color=RED,label='Observed best grid fit')
    axes[1].set(xlabel=r'Maximum $2\Delta\ln\mathcal{L}$',ylabel='Density',title=f"Search-calibrated p = {calibrated['p']:.4f}")
    axes[1].legend(fontsize=8); save(fig,folder,'primordial_search')
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    ls=np.arange(2,65); f=ls*(ls+1)/(2*np.pi)
    for ax,index,name in zip(axes,[0,1,3],['TT','EE','TE']):
        ax.plot(ls,f*base[ls,index],color=BLUE,label='Baseline theory')
        ax.plot(ls,f*selected[ls,index],color=RED,label='TT-fitted suppression')
        if index==0: ax.plot(ls,f*obs[:len(ls)],'.',color='gray',ms=3,label='Published TT')
        if index==1:
            ax.plot(ls,f*predictions[0][:len(ls)],ls='--',color=BLUE,label='Baseline conditioned on TT')
            ax.plot(ls,f*predictions[1][:len(ls)],ls='--',color=RED,label='Fitted conditioned on TT')
        ax.set(xlabel=r'$\ell$',ylabel=r'$D_\ell$ [$\mu$K$^2$]',title=name+(' (prediction)' if index else ''))
        ax.legend(fontsize=6)
    save(fig,folder,'transfer_predictions')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__': main()

from __future__ import annotations
import numpy as np
from .modes import transverse_mode_series


def _polyfit_summary(t, phase, degree):
    t=np.asarray(t,float); phase=np.asarray(phase,float)
    coeff=np.polyfit(t,phase,int(degree))
    pred=np.polyval(coeff,t)
    resid=phase-pred
    rss=float(np.sum(resid*resid))
    centered=phase-float(np.mean(phase))
    sst=float(np.sum(centered*centered))
    r2=float(1.0-rss/sst) if sst>0 else 1.0
    n=max(len(t),1); k=int(degree)+1
    scale=max(rss/n,np.finfo(float).tiny)
    bic=float(n*np.log(scale)+k*np.log(n))
    return {'degree':int(degree),'coefficients':coeff.tolist(),'r2':r2,'rss':rss,'bic':bic,'residual':resid}


def _residual_whiteness(residual, lags, sigma):
    x=np.asarray(residual,float)
    x=x-np.mean(x) if len(x) else x
    denom=float(np.dot(x,x))
    bound=float(sigma)/np.sqrt(max(len(x),1))
    if len(x)<3 or denom<=1e-20:
        return {'pass':True,'max_abs_acf':0.0,'bound':bound,'lags_used':0,'acf':[]}
    vals=[]
    for lag in range(1,min(int(lags),len(x)-2)+1):
        vals.append(float(np.dot(x[:-lag],x[lag:])/denom))
    mx=float(max(map(abs,vals))) if vals else 0.0
    return {'pass':bool(mx<=bound),'max_abs_acf':mx,'bound':bound,'lags_used':len(vals),'acf':vals}


def _segment_frequencies(t, phase, count, minimum_segment_samples):
    idx=np.arange(len(t),dtype=int)
    rows=[]
    for j,part in enumerate(np.array_split(idx,int(count))):
        if len(part)<int(minimum_segment_samples):
            continue
        slope,intercept=np.polyfit(t[part],phase[part],1)
        rows.append({'segment':int(j),'frequency':float(slope),'sample_count':int(len(part))})
    f=np.asarray([r['frequency'] for r in rows],float)
    if len(f)>=2 and np.all(np.isfinite(f)):
        mean=float(np.mean(f)); span=float((np.max(f)-np.min(f))/max(abs(mean),1e-12)); cv=float(np.std(f)/max(abs(mean),1e-12))
    else:
        mean=float('nan'); span=float('inf'); cv=float('inf')
    return {'rows':rows,'mean_frequency':mean,'relative_span':span,'cv':cv}


def phase_drift_from_series(times, coeff, cfg):
    t=np.asarray(times,float); z=np.asarray(coeff,complex); amp=np.abs(z)
    max_amp=float(np.nanmax(amp)) if len(amp) else 0.0
    floor=max(1e-14,float(cfg['amplitude_floor_fraction'])*max_amp)
    mask=np.isfinite(amp)&(amp>=floor)&np.isfinite(t)
    active=int(np.sum(mask)); active_fraction=float(active/max(len(t),1))
    if active<int(cfg['minimum_active_samples']) or active_fraction<float(cfg['minimum_active_fraction']):
        return {'status':'INSUFFICIENT_PHASE_SUPPORT','classification':'INCOHERENT_OR_UNRESOLVED','pass':False,'active_samples':active,'active_fraction':active_fraction,'amplitude_floor':floor}
    tt=t[mask]; ph=np.unwrap(np.angle(z[mask])); cycles=float(abs(ph[-1]-ph[0])/(2*np.pi)) if len(ph)>1 else 0.0
    lin=_polyfit_summary(tt,ph,1); quad=_polyfit_summary(tt,ph,2)
    delta_bic=float(lin['bic']-quad['bic'])
    seg=_segment_frequencies(tt,ph,cfg['segment_count'],cfg['minimum_segment_samples'])
    inst=np.gradient(ph,tt)
    finite=inst[np.isfinite(inst)]
    if len(finite):
        sign=1.0 if float(np.median(finite))>=0 else -1.0
        sign_consistency=float(np.mean(sign*finite>=0.0))
    else: sign_consistency=0.0
    lw=_residual_whiteness(lin.pop('residual'),cfg['residual_acf_lags'],cfg['residual_acf_sigma'])
    qw=_residual_whiteness(quad.pop('residual'),cfg['residual_acf_lags'],cfg['residual_acf_sigma'])
    qcoef=quad['coefficients']; a2,a1=float(qcoef[0]),float(qcoef[1])
    omega_start=float(a1+2*a2*tt[0]); omega_end=float(a1+2*a2*tt[-1]); omega_mean=float(0.5*(omega_start+omega_end))
    drift_rel=float(abs(omega_end-omega_start)/max(abs(omega_mean),1e-12))
    stationary=bool(cycles>=float(cfg['minimum_phase_cycles']) and lin['r2']>=float(cfg['stationary_linear_r2_min']) and seg['relative_span']<=float(cfg['stationary_segment_frequency_relative_span_max']) and lw['pass'])
    drifting=bool(cycles>=float(cfg['minimum_phase_cycles']) and quad['r2']>=float(cfg['quadratic_r2_min']) and delta_bic>=float(cfg['quadratic_delta_bic_min']) and seg['relative_span']>float(cfg['stationary_segment_frequency_relative_span_max']) and sign_consistency>=float(cfg['instantaneous_frequency_sign_consistency_min']) and qw['pass'])
    if stationary:
        classification='STATIONARY_COHERENT'
    elif drifting:
        classification='COHERENT_DRIFTING'
    else:
        classification='INCOHERENT_OR_UNRESOLVED'
    return {
        'status':'PHASE_DIAGNOSTIC_COMPLETE','classification':classification,'pass':bool(stationary or drifting),
        'active_samples':active,'active_fraction':active_fraction,'amplitude_floor':floor,'phase_cycles':cycles,
        'linear_fit':lin,'quadratic_fit':quad,'delta_bic_quadratic_over_linear':delta_bic,
        'segmented_frequency':seg,'instantaneous_frequency_sign_consistency':sign_consistency,
        'quadratic_frequency_start':omega_start,'quadratic_frequency_end':omega_end,'quadratic_frequency_relative_change':drift_rel,
        'linear_residual_whiteness':lw,'quadratic_residual_whiteness':qw,
    }


def phase_drift_metrics(frames, dt, persistence, kelvin_cfg, cfg):
    modes,coeff=transverse_mode_series(frames,frames[0],kelvin_cfg['mode_min'],kelvin_cfg['mode_max'])
    energy=np.mean(np.abs(coeff)**2,axis=0) if len(coeff) else np.zeros(len(modes),float)
    preferred=persistence.get('persistent_mode')
    if preferred is not None and int(preferred) in set(map(int,modes)):
        selected=int(preferred); policy='persistence_winner'
    elif len(modes):
        selected=int(modes[int(np.argmax(energy))]); policy='full_horizon_energy_max'
    else:
        return {'status':'NO_MODE_AVAILABLE','classification':'INCOHERENT_OR_UNRESOLVED','pass':False,'selected_mode':None,'selection_policy':'none'}
    ix=int(np.where(modes==selected)[0][0]); times=np.arange(len(frames),dtype=float)*float(dt)
    out=phase_drift_from_series(times,coeff[:,ix],cfg)
    out['selected_mode']=selected; out['selection_policy']=policy; out['selected_mode_energy_fraction']=float(energy[ix]/max(float(np.sum(energy)),1e-30))
    return out

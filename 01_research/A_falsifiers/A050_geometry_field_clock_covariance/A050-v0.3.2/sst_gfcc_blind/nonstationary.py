from __future__ import annotations
import numpy as np


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
    span=max(float(np.max(phase)-np.min(phase)),1e-12)
    nrmse=float(np.sqrt(rss/n)/span)
    return {'degree':int(degree),'coefficients':coeff.tolist(),'r2':r2,'rss':rss,'bic':bic,'nrmse':nrmse}


def branch_identity_metrics(persistence, cfg):
    checkpoints=list(persistence.get('checkpoints') or [])
    modes=[z.get('selected_mode') for z in checkpoints if z.get('selected_mode') is not None]
    if not modes:
        return {
            'reference_mode':None,'selection_policy':'no_checkpoint_mode','checkpoint_mode_fraction':0.0,
            'checkpoint_count':len(checkpoints),'resolved_checkpoint_count':0,'mode_switch_count':0,
            'stable':False,'persistence_gate_pass':bool(persistence.get('pass',False))
        }
    counts={}
    for m in modes:
        m=int(m); counts[m]=counts.get(m,0)+1
    reference=min(counts,key=lambda m:(-counts[m],m))
    fraction=float(counts[reference]/len(modes))
    switches=sum(1 for a,b in zip(modes[:-1],modes[1:]) if a!=b)
    stable=bool(
        fraction>=float(cfg['minimum_branch_identity_checkpoint_fraction']) and
        switches<=int(cfg['maximum_branch_mode_switches'])
    )
    return {
        'reference_mode':int(reference),'selection_policy':'checkpoint_majority_mode_then_lowest_mode_tiebreak',
        'checkpoint_mode_fraction':fraction,'checkpoint_count':len(checkpoints),
        'resolved_checkpoint_count':len(modes),'mode_switch_count':int(switches),'stable':stable,
        'persistence_gate_pass':bool(persistence.get('pass',False)),
        'checkpoint_mode_counts':{str(k):int(v) for k,v in sorted(counts.items())}
    }


def branch_retained(baseline_branch, holdout_branch):
    return bool(
        baseline_branch.get('stable',False) and holdout_branch.get('stable',False) and
        baseline_branch.get('reference_mode') is not None and
        baseline_branch.get('reference_mode')==holdout_branch.get('reference_mode')
    )


def _segment_metrics(t, phase, count, minimum_segment_samples):
    idx=np.arange(len(t),dtype=int)
    rows=[]; total_rss=0.0; total_n=0
    for j,part in enumerate(np.array_split(idx,int(count))):
        if len(part)<int(minimum_segment_samples):
            continue
        fit=_polyfit_summary(t[part],phase[part],1)
        slope=float(fit['coefficients'][0])
        rows.append({'segment':int(j),'angular_rate':slope,'r2':float(fit['r2']),'nrmse':float(fit['nrmse']),'sample_count':int(len(part))})
        total_rss+=float(fit['rss']); total_n+=len(part)
    rates=np.asarray([r['angular_rate'] for r in rows],float)
    if len(rates)>=2 and np.all(np.isfinite(rates)):
        mean=float(np.mean(rates)); cv=float(np.std(rates)/max(abs(mean),1e-12))
    else:
        mean=float('nan'); cv=float('inf')
    phase_span=max(float(np.max(phase)-np.min(phase)),1e-12) if len(phase) else 1e-12
    piecewise_nrmse=float(np.sqrt(total_rss/max(total_n,1))/phase_span) if total_n else float('inf')
    return {'rows':rows,'mean_angular_rate':mean,'angular_rate_cv':cv,'piecewise_nrmse':piecewise_nrmse}


def phase_drift_from_series(times, coeff, cfg):
    t=np.asarray(times,float); z=np.asarray(coeff,complex); amp=np.abs(z)
    max_amp=float(np.nanmax(amp)) if len(amp) else 0.0
    floor=max(1e-14,float(cfg['amplitude_floor_fraction'])*max_amp)
    mask=np.isfinite(amp)&(amp>=floor)&np.isfinite(t)
    active=int(np.sum(mask)); active_fraction=float(active/max(len(t),1))
    if active<int(cfg['minimum_active_samples']) or active_fraction<float(cfg['minimum_active_fraction']):
        return {
            'status':'INSUFFICIENT_PHASE_SUPPORT','classification':'INCOHERENT_OR_UNRESOLVED','coherent':False,
            'active_samples':active,'active_fraction':active_fraction,'amplitude_floor':floor,
            'angular_rate_units':'radian per dimensionless time unit'
        }
    tt=t[mask]; ph=np.unwrap(np.angle(z[mask]))
    dph=np.diff(ph)
    net_cycles=float(abs(ph[-1]-ph[0])/(2*np.pi)) if len(ph)>1 else 0.0
    path_cycles=float(np.sum(np.abs(dph))/(2*np.pi)) if len(ph)>1 else 0.0
    lin=_polyfit_summary(tt,ph,1); quad=_polyfit_summary(tt,ph,2)
    delta_bic=float(lin['bic']-quad['bic'])
    seg=_segment_metrics(tt,ph,cfg['segment_count'],cfg['minimum_segment_samples'])
    rows=seg['rows']; rates=np.asarray([r['angular_rate'] for r in rows],float)
    locally_coherent_fraction=float(np.mean([r['r2']>=float(cfg['segment_linear_r2_min']) for r in rows])) if rows else 0.0
    scale=float(np.median(np.abs(rates))) if len(rates) else 0.0
    rate_floor=max(1e-12,float(cfg['significant_segment_rate_fraction'])*scale)
    signed=[int(np.sign(x)) for x in rates if abs(x)>=rate_floor]
    reversals=sum(1 for a,b in zip(signed[:-1],signed[1:]) if a!=b)
    pos=sum(s>0 for s in signed); neg=sum(s<0 for s in signed)
    qcoef=quad['coefficients']; a2,a1=float(qcoef[0]),float(qcoef[1])
    omega_start=float(a1+2*a2*tt[0]); omega_end=float(a1+2*a2*tt[-1])
    drift_rel=float(abs(omega_end-omega_start)/max(max(abs(omega_start),abs(omega_end)),1e-12))
    support=bool(path_cycles>=float(cfg['minimum_total_path_cycles']))
    local_coherent=bool(
        locally_coherent_fraction>=float(cfg['minimum_locally_coherent_segment_fraction']) and
        seg['piecewise_nrmse']<=float(cfg['piecewise_nrmse_max'])
    )
    enough_signed=len(signed)>=int(cfg['minimum_significant_rate_segments'])
    stationary=bool(
        support and local_coherent and reversals==0 and
        lin['r2']>=float(cfg['stationary_linear_r2_min']) and
        seg['angular_rate_cv']<=float(cfg['stationary_segment_angular_rate_cv_max'])
    )
    reversing=bool(support and local_coherent and enough_signed and pos>0 and neg>0 and reversals>=1)
    drifting=bool(
        support and local_coherent and enough_signed and reversals==0 and
        quad['r2']>=float(cfg['quadratic_r2_min']) and
        delta_bic>=float(cfg['quadratic_delta_bic_min']) and
        quad['nrmse']<=float(cfg['quadratic_nrmse_max']) and
        drift_rel>=float(cfg['drift_relative_change_min'])
    )
    if stationary:
        classification='STATIONARY_COHERENT'
    elif reversing:
        classification='COHERENT_REVERSING'
    elif drifting:
        classification='COHERENT_DRIFTING'
    elif support and local_coherent:
        classification='COHERENT_NONSTATIONARY_COMPLEX'
    else:
        classification='INCOHERENT_OR_UNRESOLVED'
    coherent=classification!='INCOHERENT_OR_UNRESOLVED'
    return {
        'status':'PHASE_DIAGNOSTIC_COMPLETE','classification':classification,'coherent':coherent,
        'active_samples':active,'active_fraction':active_fraction,'amplitude_floor':floor,
        'net_phase_cycles':net_cycles,'total_phase_path_cycles':path_cycles,
        'linear_fit':lin,'quadratic_fit':quad,'delta_bic_quadratic_over_linear':delta_bic,
        'segmented_angular_rate':seg,'locally_coherent_segment_fraction':locally_coherent_fraction,
        'significant_segment_angular_rate_floor':rate_floor,'significant_rate_segment_count':len(signed),
        'positive_rate_segment_count':int(pos),'negative_rate_segment_count':int(neg),
        'angular_rate_sign_reversal_count':int(reversals),
        'quadratic_angular_rate_start':omega_start,'quadratic_angular_rate_end':omega_end,
        'quadratic_angular_rate_relative_change':drift_rel,
        'angular_rate_units':'radian per dimensionless time unit',
        'cycle_rate_relation':'f = omega / (2*pi)'
    }


def branch_phase_metrics(frames, dt, persistence, kelvin_cfg, cfg):
    # Import lazily so pure phase-series unit tests do not depend on the geometry stack.
    from .modes import transverse_mode_series
    branch=branch_identity_metrics(persistence,cfg)
    modes,coeff=transverse_mode_series(frames,frames[0],kelvin_cfg['mode_min'],kelvin_cfg['mode_max'])
    energy=np.mean(np.abs(coeff)**2,axis=0) if len(coeff) else np.zeros(len(modes),float)
    selected=branch.get('reference_mode')
    if selected is not None and selected in set(map(int,modes)):
        policy='checkpoint_majority_mode'
    elif len(modes):
        selected=int(modes[int(np.argmax(energy))]); policy='full_horizon_energy_fallback'
    else:
        return {'branch_identity':branch,'phase':{'status':'NO_MODE_AVAILABLE','classification':'INCOHERENT_OR_UNRESOLVED','coherent':False},'selected_mode':None,'selection_policy':'none'}
    ix=int(np.where(modes==int(selected))[0][0]); times=np.arange(len(frames),dtype=float)*float(dt)
    phase=phase_drift_from_series(times,coeff[:,ix],cfg)
    frac=float(energy[ix]/max(float(np.sum(energy)),1e-30)) if len(energy) else 0.0
    return {'branch_identity':branch,'phase':phase,'selected_mode':int(selected),'selection_policy':policy,'selected_mode_energy_fraction':frac}

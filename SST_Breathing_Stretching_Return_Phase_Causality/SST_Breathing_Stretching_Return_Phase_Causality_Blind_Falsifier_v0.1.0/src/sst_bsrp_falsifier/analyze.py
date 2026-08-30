from pathlib import Path
import json,csv,hashlib
import numpy as np
from .blind import load_catalog
from .observables import packet_track,dominant_period,breathing_harmonic_phase,second_derivative,interp
from .stats import fit_circular,loco_cv,grouped_permutation_p
from .util import clean_json

def _load(p): return np.load(p,allow_pickle=False)

def pair_analysis(a,b,cfg):
    za,zb=a,b
    t=za['t'];
    if len(t)!=len(zb['t']) or np.max(np.abs(t-zb['t']))>1e-12: return {'valid':False,'reason':'TIME_GRID_MISMATCH'}
    # orient the pair using anonymous packet arm: caller passes arm + then arm -
    dsig=.5*(za['sigma']-zb['sigma'])
    track=packet_track(dsig,t,float(cfg.get('min_packet_corr',.15)))
    rg0=.5*(za['rg'][0]+zb['rg'][0]); q=.5*(za['rg']+zb['rg'])/rg0-1.0
    period,power=dominant_period(t,q); breathing_rms=float(np.sqrt(np.mean((q-np.mean(q))**2))); acc_a=second_derivative(t,za['rg']/rg0-1); acc_b=second_derivative(t,zb['rg']/rg0-1); dacc=.5*(acc_a-acc_b)
    base={'valid':False,'packet_available':bool(track.get('available',False)),'packet_reason':track.get('reason'),'breathing_period_fft':period,'breathing_peak_power_fraction':power,'breathing_rms':breathing_rms,'max_ds_cv':float(max(np.max(za['ds_cv']),np.max(zb['ds_cv'])))}
    if not track.get('available',False): return base|{k:v for k,v in track.items() if k not in ('phase_series','corr_series')}
    tau=float(track['tau_return'])
    bfit=breathing_harmonic_phase(t,q,tau,int(cfg.get('breathing_frequency_scan_points',161)))
    if not bfit.get('available',False): return base|{'packet_reason':'BREATHING_PHASE_'+str(bfit.get('reason'))}
    period=float(bfit['period']); omega_b=float(bfit['omega'])
    tau_unc=float(track.get('tau_uncertainty',0.0)); phase_unc=float(np.hypot(float(bfit['phase_uncertainty_without_return_time_rad']),omega_b*tau_unc))
    w=float(cfg.get('post_return_window_fraction',.15))*period
    def response_at(tc):
        tc=float(tc); t2=min(float(t[-1]),tc+w)
        if t2<=tc+1e-12: return (np.nan,np.nan,np.nan)
        mask=(t>=tc)&(t<=t2); resp0=float(np.mean(dacc[mask])) if mask.sum() else interp(t,dacc,tc)
        q0=interp(t,q,tc); ph=breathing_harmonic_phase(t,q,tc,int(cfg.get('breathing_frequency_scan_points',161)))
        return ((ph.get('phase_rad',np.nan) if ph.get('available') else np.nan),resp0,-q0*resp0)
    phi,resp,restoring=response_at(tau)
    if not np.isfinite(resp): return base|{'packet_reason':'NO_POST_RETURN_WINDOW'}
    qret=interp(t,q,tau)
    # explicit temporal-null windows: same observables evaluated before a full packet return
    half_phi,half_resp,half_restore=response_at(.5*tau)
    threeq_phi,threeq_resp,threeq_restore=response_at(.75*tau)
    # pre-return matched window is a diagnostic for nonlocal instantaneous contamination
    p1=max(float(t[0]),tau-w); pmask=(t>=p1)&(t<tau); pre=float(np.mean(dacc[pmask])) if pmask.sum() else np.nan
    ratio=float(abs(pre)/(abs(resp)+1e-15)) if np.isfinite(pre) else np.nan
    valid=(base['max_ds_cv']<=float(cfg.get('max_ds_cv',.35)) and power>=float(cfg.get('min_breathing_peak_power',.12)) and breathing_rms>=float(cfg.get('min_breathing_rms',1e-5)) and float(bfit['harmonic_r2'])>=float(cfg.get('min_breathing_harmonic_r2',.25)) and phase_unc<=float(cfg.get('max_return_phase_uncertainty_rad',.25)) and float(track.get('packet_rms_peak',0.0))>=float(cfg.get('min_packet_rms_peak',1e-8)) and track.get('monotonic_fraction',0)>=float(cfg.get('min_packet_monotonic_fraction',.65)))
    return base|{'valid':bool(valid),'reason':'OK' if valid else 'QUALITY_GATE','tau_return':tau,'tau_return_uncertainty':tau_unc,'return_phase_rad':phi,'return_phase_uncertainty_rad':phase_unc,'breathing_period':period,'breathing_harmonic_r2':float(bfit['harmonic_r2']),'breathing_harmonic_amplitude':float(bfit['amplitude']),'q_at_return':qret,'differential_post_accel':resp,'restoring_response':restoring,'differential_pre_accel':pre,'pre_to_post_abs_ratio':ratio,'half_return_phase_rad':half_phi,'half_return_restoring_response':half_restore,'threequarter_return_phase_rad':threeq_phi,'threequarter_return_restoring_response':threeq_restore,'packet_rms_peak':float(track.get('packet_rms_peak',np.nan)),'packet_median_corr':track['median_corr'],'packet_monotonic_fraction':track['monotonic_fraction'],'packet_total_cycles':track['total_cycles']}

def analyze(work,cfg):
    work=Path(work); cat=load_catalog(work); bypair={}
    for r in cat: bypair.setdefault(r['pair_id'],[]).append(r)
    rows=[]
    for pid,rr in sorted(bypair.items()):
        if len(rr)!=2: continue
        rp=next((r for r in rr if int(r['packet_arm'])==1),None); rm=next((r for r in rr if int(r['packet_arm'])==-1),None)
        if rp is None or rm is None: continue
        pa=work/'results/candidates'/f"{rp['candidate_id']}.npz"; pb=work/'results/candidates'/f"{rm['candidate_id']}.npz"
        if not pa.exists() or not pb.exists(): continue
        d=pair_analysis(_load(pa),_load(pb),cfg)
        rows.append({'pair_id':pid,'carrier_id':rp['carrier_id'],'breathing_arm':rp['breathing_arm'],'packet_center_frac':rp['packet_center_frac'],**d})
    out=work/'results'; out.mkdir(exist_ok=True,parents=True)
    fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['pair_id']
    with open(out/'blind_pair_results.csv','w',newline='',encoding='utf-8') as f:
        ww=csv.DictWriter(f,fieldnames=fields); ww.writeheader(); ww.writerows(rows)
    valid=[r for r in rows if r.get('valid') and np.isfinite(r.get('return_phase_rad',np.nan)) and np.isfinite(r.get('restoring_response',np.nan))]
    summary={'format':'SST-BSRP-BLIND-1.0','n_pairs':len(rows),'n_valid_pairs':len(valid),'carrier_identity_read':False,'condition_semantics_read':False,'explicit_delay_parameter_used':False,'target_phase_used_in_dynamics':False,'delay_source':'measured packet return only'}
    if len(valid)>=6 and len(set(r['carrier_id'] for r in valid))>=3:
        phi=np.array([r['return_phase_rad'] for r in valid]); y=np.array([r['restoring_response'] for r in valid]); g=np.array([r['carrier_id'] for r in valid])
        fit=fit_circular(phi,y); cv=loco_cv(phi,y,g); nperm=int(cfg.get('n_permutations',499)); p,obs=grouped_permutation_p(phi,y,g,nperm=nperm,seed=int(cfg.get('stats_seed',314159)))
        summary.update({'phase_fit':fit,'loco_cv_r2':float(cv),'grouped_permutation_p':p,'n_permutations':nperm,'median_pre_to_post_abs_ratio':float(np.nanmedian([r['pre_to_post_abs_ratio'] for r in valid]))})
        controls={}
        for tag,pk,yk in [('half','half_return_phase_rad','half_return_restoring_response'),('threequarter','threequarter_return_phase_rad','threequarter_return_restoring_response')]:
            vv=[r for r in valid if np.isfinite(r.get(pk,np.nan)) and np.isfinite(r.get(yk,np.nan))]
            if len(vv)>=6 and len(set(r['carrier_id'] for r in vv))>=3:
                cp=np.array([r[pk] for r in vv]); cy=np.array([r[yk] for r in vv]); cg=np.array([r['carrier_id'] for r in vv])
                controls[tag]={'n':len(vv),'loco_cv_r2':float(loco_cv(cp,cy,cg)),'fit':fit_circular(cp,cy)}
        summary['temporal_null_controls']=controls
        ctrl=max([v['loco_cv_r2'] for v in controls.values() if np.isfinite(v['loco_cv_r2'])],default=-np.inf)
        summary['return_minus_best_prereturn_cv_r2']=float(cv-ctrl) if np.isfinite(ctrl) else None
        temporal_ok=(not np.isfinite(ctrl)) or (cv-ctrl>=float(cfg.get('gate_min_return_over_prereturn_delta_r2',.03)))
        gate=(cv>=float(cfg.get('gate_min_loco_r2',.10)) and p<=float(cfg.get('gate_max_perm_p',.01)) and summary['median_pre_to_post_abs_ratio']<=float(cfg.get('gate_max_prepost_ratio',.75)) and temporal_ok)
        summary['primary_phase_causality_gate']='PASS' if gate else 'FAIL'
    else: summary['primary_phase_causality_gate']='INDETERMINATE_INSUFFICIENT_VALID_PAIRS'
    (out/'blind_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    return summary

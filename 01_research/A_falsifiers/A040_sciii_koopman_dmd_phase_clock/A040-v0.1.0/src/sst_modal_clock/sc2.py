from __future__ import annotations

from pathlib import Path
import csv, json, math
import numpy as np

from .blind import load_catalog
from .modal import (
    analytic_signal,
    natural_response,
    odd_response,
    even_probe_contamination,
    learn_modes,
    project,
    mode_strain_weights,
    _harmonic_fit,
)
from .analyze import _stage_a_geometry_metrics
from .util import clean_json


def _savecsv(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted(set().union(*(r.keys() for r in rows))) if rows else ['carrier_id']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        w.writerows([{k:(json.dumps(clean_json(v), sort_keys=True) if isinstance(v,(list,dict,tuple)) else v) for k,v in r.items()} for r in rows])


def _pairs(work):
    pairs = {}
    for r in load_catalog(work): pairs.setdefault(r['pair_id'], []).append(r)
    return pairs


def _arm(rr, arm):
    return next((r for r in rr if int(r['probe_arm']) == int(arm)), None)


def _stage_a_file(work, r, branch='stage_a'):
    return Path(work) / f'results_{branch}/candidates' / f'{r["candidate_id"]}.npz'


def _stage_b_file(work, branch, r):
    return Path(work) / f'results_{branch}/candidates' / f'{r["candidate_id"]}.npz'


def _cut(z, n):
    return {
        'x': np.asarray(z['x'][:n]),
        'x_reference': np.asarray(z['x_reference']),
        'component_offsets': np.asarray(z['component_offsets'], dtype=np.int64) if 'component_offsets' in z.files else np.asarray([0, len(z['x_reference'])], dtype=np.int64),
    }


def _linfit_phase(t, ph):
    t=np.asarray(t,float); ph=np.asarray(ph,float)
    A=np.c_[np.ones(len(t)), t]
    b=np.linalg.lstsq(A, ph, rcond=None)[0]
    pred=A@b
    ss=float(np.sum((ph-ph.mean())**2)); rss=float(np.sum((ph-pred)**2))
    r2=float(1-rss/ss) if ss>1e-30 else 0.0
    return float(b[0]), float(b[1]), pred, r2


def _crossing_times(t, ph):
    t=np.asarray(t,float); ph=np.asarray(ph,float)
    if len(t)<2: return np.asarray([],float)
    twopi=2*np.pi
    lo=int(math.ceil(ph[0]/twopi)); hi=int(math.floor(ph[-1]/twopi))
    out=[]
    for k in range(lo,hi+1):
        target=k*twopi; d=ph-target
        idx=np.where((d[:-1] <= 0) & (d[1:] > 0))[0]
        if len(idx):
            i=int(idx[0]); den=float(d[i+1]-d[i]); f=0.0 if abs(den)<1e-30 else float(-d[i]/den)
            out.append(float(t[i]+f*(t[i+1]-t[i])))
    return np.asarray(out,float)


def phase_clock_metrics(t, y, cfg):
    """SC-II phase metrics for one frozen modal coordinate.

    No shape-recurrence is required.  A deterministic linear detrend is removed,
    the analytic-signal phase is unwrapped/oriented, and phase stability is
    evaluated on the holdout only.  The phase-prediction gate fits constant
    angular velocity on an early calibration fraction and predicts the later
    holdout without refitting.
    """
    t=np.asarray(t,float); y=np.asarray(y,float)
    if len(t)<48 or len(y)!=len(t): return {'valid':False,'reason':'TOO_SHORT'}
    # deterministic affine slow-manifold removal; not tuned per candidate
    B=np.c_[np.ones(len(t)), t-t[0]]; beta=np.linalg.lstsq(B,y,rcond=None)[0]; yd=y-B@beta
    fit=_harmonic_fit(t,yd)
    if not fit: return {'valid':False,'reason':'NO_OSCILLATORY_SUPPORT'}
    z=analytic_signal(yd); env=np.abs(z); ph=np.unwrap(np.angle(z))
    trim=float(cfg.get('sc2_phase_edge_trim_fraction',0.05)); m=max(2,int(round(trim*len(t))))
    if 2*m>=len(t)-16: m=2
    t=t[m:len(t)-m]; yd=yd[m:len(yd)-m]; env=env[m:len(env)-m]; ph=ph[m:len(ph)-m]
    if len(t)<40: return {'valid':False,'reason':'TOO_SHORT_AFTER_TRIM'}
    # orient so the net phase direction is positive
    _,slope0,_,_= _linfit_phase(t,ph)
    if slope0<0: ph=-ph
    ph=ph-ph[0]
    dph=np.diff(ph); monotonic=float(np.mean(dph>0)) if len(dph) else 0.0
    wraps=float((ph[-1]-ph[0])/(2*np.pi))
    intercept,omega,pred,r2=_linfit_phase(t,ph)
    resid=ph-pred
    crossings=_crossing_times(t,ph); periods=np.diff(crossings)
    period_cv=float(np.std(periods)/max(np.mean(periods),1e-15)) if len(periods)>=2 else np.inf
    period_med=float(np.median(periods)) if len(periods) else (2*np.pi/max(omega,1e-15) if omega>0 else np.inf)
    # one-cycle phase diffusion of residual phase
    dt=float(np.median(np.diff(t))); lag=max(1,int(round(period_med/dt))) if np.isfinite(period_med) else len(t)
    phase_diff=float(np.sqrt(np.mean((resid[lag:]-resid[:-lag])**2))) if lag<len(resid)-4 else np.inf
    env_mean=float(np.mean(env)); env_cv=float(np.std(env)/max(env_mean,1e-15))
    q=max(4,len(env)//4); env_start=float(np.median(env[:q])); env_end=float(np.median(env[-q:])); retention=float(env_end/max(env_start,1e-15))
    amp=float(np.median(env))
    # constant-frequency out-of-sample phase prediction
    frac=float(cfg.get('sc2_phase_calibration_fraction',0.40)); split=max(12,min(len(t)-12,int(round(frac*len(t)))))
    c0,w0,_,cal_r2=_linfit_phase(t[:split],ph[:split]); pp=c0+w0*t[split:]
    err=ph[split:]-pp
    pred_rms=float(np.sqrt(np.mean(err*err))) if len(err) else np.inf
    terminal=float(abs(err[-1])) if len(err) else np.inf
    reliable=float(np.mean(env>=float(cfg.get('sc2_gate_min_envelope_fraction_of_median',0.25))*max(np.median(env),1e-15)))
    return {
        'valid':True,
        'amplitude':amp,
        'frequency':float(omega/(2*np.pi)),
        'omega':float(omega),
        'period':float(period_med),
        'phase_wraps':wraps,
        'phase_monotonic_fraction':monotonic,
        'phase_linearity_r2':r2,
        'phase_calibration_r2':cal_r2,
        'period_cv':period_cv,
        'phase_diffusion_rms_rad':phase_diff,
        'phase_prediction_rms_rad':pred_rms,
        'phase_prediction_terminal_error_rad':terminal,
        'envelope_cv':env_cv,
        'envelope_retention_ratio':retention,
        'envelope_reliable_fraction':reliable,
        'spectral_power_fraction':float(fit.get('spectral_power_fraction',0.0)),
        'harmonic_r2':float(fit.get('harmonic_r2',0.0)),
        'harmonic_period':float(fit.get('period',np.inf)),
        'n_phase_crossings':int(len(crossings)),
        'cycle_periods':periods.tolist(),
    }


def phase_clock_gates(m, energy, cfg, channel):
    p1=bool(float(energy)>=float(cfg.get('sc2_gate_min_discovery_energy',0.03)) and m.get('amplitude',0)>=float(cfg.get('sc2_gate_min_holdout_amplitude',1e-5)))
    p2=bool(m.get('valid') and m.get('phase_wraps',0)>=float(cfg.get('sc2_gate_min_phase_wraps',4.0)) and m.get('phase_monotonic_fraction',0)>=float(cfg.get('sc2_gate_min_monotonic_fraction',0.90)))
    p3=bool(m.get('phase_linearity_r2',0)>=float(cfg.get('sc2_gate_min_phase_linearity_r2',0.90)) and m.get('period_cv',99)<=float(cfg.get('sc2_gate_max_period_cv',0.15)) and m.get('spectral_power_fraction',0)>=float(cfg.get('sc2_gate_min_spectral_power',0.30)) and m.get('harmonic_r2',0)>=float(cfg.get('sc2_gate_min_harmonic_r2',0.50)))
    lo=float(cfg.get('sc2_gate_min_envelope_retention_ratio',0.40)); hi=float(cfg.get('sc2_gate_max_envelope_retention_ratio',2.50))
    p4=bool(m.get('phase_diffusion_rms_rad',99)<=float(cfg.get('sc2_gate_max_phase_diffusion_rms_rad',0.75)) and m.get('envelope_cv',99)<=float(cfg.get('sc2_gate_max_envelope_cv',0.60)) and lo<=m.get('envelope_retention_ratio',-1)<=hi and m.get('envelope_reliable_fraction',0)>=float(cfg.get('sc2_gate_min_envelope_reliable_fraction',0.95)))
    p5=bool(m.get('phase_prediction_rms_rad',99)<=float(cfg.get('sc2_gate_max_phase_prediction_rms_rad',1.00)) and m.get('phase_prediction_terminal_error_rad',99)<=float(cfg.get('sc2_gate_max_phase_prediction_terminal_error_rad',1.57)))
    natural=bool(channel=='natural')
    return p1,p2,p3,p4,p5,natural


def _coverage_gate(total,valid,priority_total,priority_valid,cfg):
    frac=float(valid/max(total,1)); minfrac=float(cfg.get('gate_min_valid_carrier_fraction_for_global_fail',.80)); mincount=int(cfg.get('gate_min_valid_carriers_for_global_fail',20))
    priority_ok=bool((not cfg.get('gate_require_all_priority_carriers',True)) or priority_total==priority_valid)
    return {'valid_carrier_fraction':frac,'coverage_ok_for_global_fail':bool(valid>=mincount and frac>=minfrac and priority_ok),'priority_coverage_ok':priority_ok,'gate_min_valid_carrier_fraction_for_global_fail':minfrac,'gate_min_valid_carriers_for_global_fail':mincount}


def analyze_sc2_stage_a(work,cfg):
    work=Path(work); out=work/'analysis'; modes_dir=out/'sc2_modes'; modes_dir.mkdir(parents=True,exist_ok=True)
    rows=[]; carriers=[]; candidates=[]; pairs=_pairs(work); disc_t=float(cfg.get('sc2_discovery_time',cfg.get('discovery_time',1.2))); eps=float(cfg.get('probe_eps',0.003)); topk=int(cfg.get('sc2_top_modes',cfg.get('top_modes',7)))
    for pid,rr in sorted(pairs.items()):
        rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); anchor=(rp or rm or r0 or {}); priority=bool(any(bool(r.get('certification_priority',False)) for r in rr)); base={'carrier_id':anchor.get('carrier_id',''),'pair_id':pid,'topology_group_id':anchor.get('topology_group_id',''),'provenance_group_id':anchor.get('provenance_group_id',''),'n_components':int(anchor.get('n_components',1)),'certification_priority':priority}
        if not rp or not rm or not r0:
            carriers.append({**base,'geometry_ok':False,'status':'MISSING_ARM','n_sc2_candidates':0}); continue
        fps=[_stage_a_file(work,r) for r in (rp,rm,r0)]
        if not all(p.exists() for p in fps):
            carriers.append({**base,'geometry_ok':False,'status':'MISSING_TRAJECTORY','n_sc2_candidates':0}); continue
        zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
        # SC-II primary analysis is deliberately only run on numerically certified geometry.
        if not gm['geometry_ok']:
            status='INCOMPLETE_OR_MESH_GATE' if not gm['completion_ok'] else ('MESH_RATIO_GATE' if not gm['mesh_ratio_ok'] else 'DS_CV_GATE')
            carriers.append({**base,**gm,'status':status,'n_sc2_candidates':0}); continue
        n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nd=int(np.searchsorted(t,disc_t,side='right')); nd=max(12,min(n-24,nd))
        if nd>=n-24:
            carriers.append({**base,**gm,'status':'TOO_SHORT_FOR_SCII','n_sc2_candidates':0}); continue
        nat,ref=natural_response(_cut(z0,n)); odd,_=odd_response(_cut(zp,n),_cut(zm,n),eps); even=even_probe_contamination(_cut(zp,n),_cut(zm,n),_cut(z0,n)); even_ratio=float(np.sqrt(np.mean(even[:nd]**2))/max(eps*np.sqrt(np.mean(odd[:nd]**2)),1e-15))
        carrier_candidates=0
        for channel,response in [('natural',nat),('odd',odd)]:
            modes,ev,center=learn_modes(response,nd,topk); amps=project(response,modes,center)
            modefile=modes_dir/f'{rp["carrier_id"]}_{channel}.npz'; np.savez_compressed(modefile,modes=modes,energy=ev,center=center,reference=ref,component_offsets=np.asarray(z0['component_offsets'],dtype=np.int64) if 'component_offsets' in z0.files else np.asarray([0,len(ref)],dtype=np.int64),discovery_time=float(t[nd-1]),channel=channel,phase_definition='Hilbert phase of frozen POD coordinate after affine slow-manifold detrend')
            for k in range(len(modes)):
                pm=phase_clock_metrics(t[nd:],amps[nd:,k],cfg); p1,p2,p3,p4,p5,natural=phase_clock_gates(pm,float(ev[k]),cfg,channel); cand=bool(gm['geometry_ok'] and p1 and p2 and p3 and p4 and p5 and natural)
                row={**base,**gm,'channel':channel,'mode_index':k,'mode_file':str(modefile.relative_to(work)),'discovery_energy_fraction':float(ev[k]),'even_probe_ratio':even_ratio,'SCII_P1_intrinsic_mode':p1,'SCII_P2_monotone_multiphase':p2,'SCII_P3_frequency_coherence':p3,'SCII_P4_phase_envelope_stability':p4,'SCII_P5_out_of_sample_phase_prediction':p5,'SCII_P6_natural_channel':natural,'sc2_provisional_candidate':cand,**{f'phase_{a}':b for a,b in pm.items()}}
                rows.append(row)
                if cand:
                    carrier_candidates+=1; candidates.append({'pair_id':pid,'carrier_id':rp['carrier_id'],'topology_group_id':rp.get('topology_group_id',''),'provenance_group_id':rp.get('provenance_group_id',''),'n_components':int(rp.get('n_components',1)),'channel':channel,'mode_index':k,'mode_file':str(modefile.relative_to(work)),'period':pm.get('period'),'frequency':pm.get('frequency'),'omega':pm.get('omega'),'phase_wraps':pm.get('phase_wraps'),'phase_linearity_r2':pm.get('phase_linearity_r2'),'period_cv':pm.get('period_cv'),'phase_diffusion_rms_rad':pm.get('phase_diffusion_rms_rad'),'phase_prediction_rms_rad':pm.get('phase_prediction_rms_rad'),'amplitude':pm.get('amplitude'),'discovery_energy_fraction':float(ev[k]),'certification_priority':priority})
        carriers.append({**base,**gm,'status':'VALID','even_probe_ratio':even_ratio,'n_sc2_candidates':carrier_candidates})
    _savecsv(out/'blind_sc2_phase_modal_results.csv',rows); _savecsv(out/'blind_sc2_carrier_summary.csv',carriers)
    (out/'sc2_candidates_provisional.json').write_text(json.dumps(clean_json({'format':'SST-SCII-PHASE-CANDIDATES-PROVISIONAL-1.0','candidates':candidates}),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (out/'sc2_candidates.json').write_text(json.dumps({'format':'SST-SCII-PHASE-CANDIDATES-CERTIFIED-1.0','candidates':[]},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    total=len(carriers); valid=sum(int(r.get('geometry_ok',False)) for r in carriers); ptotal=sum(int(r.get('certification_priority',False)) for r in carriers); pvalid=sum(int(r.get('certification_priority',False) and r.get('geometry_ok',False)) for r in carriers); cov=_coverage_gate(total,valid,ptotal,pvalid,cfg)
    if candidates: gate='PASS_SCII_PROVISIONAL_INTRINSIC_PHASE_CLOCK__REQUIRES_MESH_GAUGE_CERTIFICATION'
    elif cov['coverage_ok_for_global_fail']: gate='FAIL_SCII_NO_INTRINSIC_MODAL_PHASE_CLOCK'
    else: gate='INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE'
    summary={'format':'SST-SCII-INTRINSIC-MODAL-PHASE-STAGE-A-BLIND-1.0','definition':'monotone predictive intrinsic modal phase; full-shape recurrence not required','n_carriers':total,'n_geometry_valid_carriers':valid,'n_modes_tested':len(rows),'n_sc2_provisional_candidates':len(candidates),'carriers_with_sc2_provisional_candidates':len(set(c['carrier_id'] for c in candidates)),'carrier_identity_read':False,'primary_channel':'natural','odd_channel_role':'diagnostic/null only','discovery_time_absolute':disc_t,**cov,'primary_gate':gate}
    (out/'blind_sc2_stage_a_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def _load_manifest(work,name):
    p=Path(work)/'analysis'/name
    if not p.exists(): return []
    return json.loads(p.read_text(encoding='utf-8')).get('candidates',[])


def _rel_spread(vals):
    a=np.asarray([float(x) for x in vals if x is not None and np.isfinite(float(x))],float)
    return float((a.max()-a.min())/max(np.median(np.abs(a)),1e-15)) if len(a)>=2 else np.inf


def _gauge_metrics_for_candidate(work,cfg,c,branch,rr):
    rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); fps=[_stage_a_file(work,r,branch) for r in (rp,rm,r0)]
    if not all(p.exists() for p in fps): return {'geometry_ok':False,'reason':'MISSING_GAUGE_TRAJECTORY'}
    zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
    if not gm['geometry_ok']: return gm
    mf=np.load(Path(work)/c['mode_file'],allow_pickle=False); mode=np.asarray(mf['modes'][int(c['mode_index'])],float); center=np.asarray(mf['center'],float); n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nd=int(np.searchsorted(t,float(cfg.get('sc2_discovery_time',cfg.get('discovery_time',1.2))),side='right')); nd=max(12,min(n-24,nd)); resp,_=natural_response(_cut(z0,n)); a=project(resp,np.asarray([mode]),center)[:,0]; pm=phase_clock_metrics(t[nd:],a[nd:],cfg); _,p2,p3,p4,p5,natural=phase_clock_gates(pm,float(c.get('discovery_energy_fraction',1.0)),cfg,'natural'); return {**gm,**pm,'sc2_phase_ok':bool(p2 and p3 and p4 and p5 and natural)}


def analyze_sc2_gauge(work,cfg):
    work=Path(work); out=work/'analysis'; provisional=_load_manifest(work,'sc2_candidates_provisional.json'); pairs=_pairs(work); rows=[]; cert=[]
    for c in provisional:
        rr=pairs.get(c['pair_id'],[]); lo=_gauge_metrics_for_candidate(work,cfg,c,'stage_a_gauge_low',rr); hi=_gauge_metrics_for_candidate(work,cfg,c,'stage_a_gauge_high',rr)
        pspread=_rel_spread([c.get('period'),lo.get('period'),hi.get('period')]); dspread=_rel_spread([c.get('phase_diffusion_rms_rad'),lo.get('phase_diffusion_rms_rad'),hi.get('phase_diffusion_rms_rad')])
        ok=bool(lo.get('geometry_ok') and hi.get('geometry_ok') and lo.get('sc2_phase_ok') and hi.get('sc2_phase_ok') and pspread<=float(cfg.get('sc2_gate_max_mesh_gauge_period_spread',0.15)) and dspread<=float(cfg.get('sc2_gate_max_mesh_gauge_phase_diffusion_spread',0.50)))
        row={**c,'gauge_low_geometry_ok':lo.get('geometry_ok',False),'gauge_high_geometry_ok':hi.get('geometry_ok',False),'mesh_gauge_period_spread':pspread,'mesh_gauge_phase_diffusion_spread':dspread,'mesh_gauge_invariant':ok}; rows.append(row)
        if ok: cert.append(row)
    _savecsv(out/'blind_sc2_gauge_results.csv',rows); (out/'sc2_candidates.json').write_text(json.dumps(clean_json({'format':'SST-SCII-PHASE-CANDIDATES-CERTIFIED-1.0','candidates':cert}),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    base=json.loads((out/'blind_sc2_stage_a_summary.json').read_text(encoding='utf-8'))
    if cert: gate='PASS_SCII_INTRINSIC_PHASE_CLOCK_MESH_GAUGE_CERTIFIED'
    elif provisional: gate='FAIL_OR_INDETERMINATE_SCII_PROVISIONAL_PHASE_NOT_MESH_GAUGE_INVARIANT'
    else: gate=base.get('primary_gate','INDETERMINATE_SCII_NO_STAGE_A_RESULT')
    summary={'format':'SST-SCII-MESH-GAUGE-BLIND-1.0','n_provisional_candidates':len(provisional),'n_mesh_gauge_certified_candidates':len(cert),'carriers_with_mesh_gauge_certified_candidates':len(set(c['carrier_id'] for c in cert)),'carrier_identity_read':False,'primary_gate':gate}; (out/'blind_sc2_gauge_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def analyze_sc2_provenance(work,cfg):
    work=Path(work); out=work/'analysis'; catalog=load_catalog(work); cert=_load_manifest(work,'sc2_candidates.json')
    carrier_meta={}
    for r in catalog: carrier_meta.setdefault(r['carrier_id'],{'topology_group_id':r.get('topology_group_id',''),'provenance_group_id':r.get('provenance_group_id','')})
    by_top={}
    for cid,m in carrier_meta.items(): by_top.setdefault(m['topology_group_id'],{}).setdefault(m['provenance_group_id'],[]).append(cid)
    cert_by={}
    for c in cert: cert_by.setdefault(c['carrier_id'],[]).append(c)
    rows=[]; robust=0
    for top,fams in sorted(by_top.items()):
        fam_pass=[]; periods=[]
        for fam,cids in fams.items():
            cc=[x for cid in cids for x in cert_by.get(cid,[])]
            passed=bool(cc); fam_pass.append(passed)
            if cc: periods.append(float(np.median([float(x['period']) for x in cc if x.get('period') is not None])))
        navail=len(fams); npass=sum(fam_pass); frac=float(npass/max(navail,1)); pspread=_rel_spread(periods)
        ok=bool(npass>=int(cfg.get('sc2_gate_min_provenance_source_families_for_robustness',2)) and frac>=float(cfg.get('sc2_gate_min_provenance_candidate_fraction',2/3)) and pspread<=float(cfg.get('sc2_gate_max_provenance_period_spread',0.30)))
        robust+=int(ok); rows.append({'topology_group_id':top,'n_source_families_available':navail,'n_source_families_with_sc2_clock':npass,'source_family_candidate_fraction':frac,'period_spread':pspread,'provenance_robust_sc2_clock':ok})
    _savecsv(out/'blind_sc2_provenance_results.csv',rows)
    stage_a_path=out/'blind_sc2_stage_a_summary.json'
    stage_a=json.loads(stage_a_path.read_text(encoding='utf-8')) if stage_a_path.exists() else {}
    if robust:
        gate='PASS_SCII_PROVENANCE_ROBUST_PHASE_CLOCK'; provenance_status='PASS_SCII_PROVENANCE_ROBUST_PHASE_CLOCK'
    elif cert:
        gate='PASS_SCII_SEED_SPECIFIC_PHASE_CLOCK__PROVENANCE_NOT_ROBUST'; provenance_status='SCII_CERTIFIED_CLOCK_NOT_PROVENANCE_ROBUST'
    else:
        # v0.1.1 reporting fix: an unreached downstream stage must never overwrite
        # Stage-A's global coverage verdict.  No scientific gate is changed.
        gate=stage_a.get('primary_gate','INDETERMINATE_SCII_NO_STAGE_A_RESULT'); provenance_status='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    summary={'format':'SST-SCII-PROVENANCE-BLIND-1.1','n_topology_groups':len(rows),'n_groups_with_provenance_robust_sc2_clock':robust,'n_certified_sc2_candidates':len(cert),'carrier_identity_read':False,'overall_primary_gate':gate,'provenance_status':provenance_status,'primary_gate':gate}; (out/'blind_sc2_provenance_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def _corr(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); x=x-x.mean(); y=y-y.mean(); d=np.linalg.norm(x)*np.linalg.norm(y); return float(x@y/d) if d>1e-15 else 0.0


def delayed_phase_modulation_test(t,a,stretch,period,cfg):
    t=np.asarray(t,float); a=np.asarray(a,float); s=np.asarray(stretch,float)
    z=analytic_signal(a-np.polyval(np.polyfit(t,a,1),t)); ph=np.unwrap(np.angle(z)); _,om,_,_= _linfit_phase(t,ph)
    if om<0: ph=-ph
    omega=np.gradient(ph,t,edge_order=2); target=omega-np.median(omega)
    # deterministic 5-sample smoothing to suppress Hilbert derivative noise
    if len(target)>=9:
        ker=np.ones(5)/5; target=np.convolve(target,ker,mode='same'); s=np.convolve(s,ker,mode='same')
    disc=float(cfg.get('stage_b_discovery_time',0.8)); nd=int(np.searchsorted(t,disc,side='right')); nd=max(8,min(len(t)-8,nd)); dt=float(np.median(np.diff(t))); maxlag=max(2,min(nd//3,int(round(.75*period/dt)))) if np.isfinite(period) else max(2,nd//4)
    best=(0,0.0)
    for lag in range(1,maxlag+1):
        if nd-lag<6: break
        c=_corr(s[:nd-lag],target[lag:nd])
        if abs(c)>abs(best[1]): best=(lag,c)
    lag,cd=best; hs=s[nd:len(t)-lag] if len(t)-lag>nd else np.asarray([]); ht=target[nd+lag:] if len(t)>nd+lag else np.asarray([]); ch=_corr(hs,ht) if len(hs)>=6 else 0.0; zc=_corr(s[nd:],target[nd:]) if len(t)-nd>=6 else 0.0
    null=[]; nnull=int(cfg.get('n_phase_nulls',31)); m=len(hs)
    if m>=8:
        base=s[nd:].copy()
        for j in range(1,nnull+1):
            sh=max(1,int(round(j*len(base)/(nnull+1)))); null.append(abs(_corr(np.roll(base,sh)[:m],ht)))
    obs=abs(ch); p=(1+sum(v>=obs for v in null))/(1+len(null)) if null else 1.0
    return {'lag_samples':int(lag),'delay':float(lag*dt),'discovery_corr':float(cd),'holdout_corr':float(ch),'zero_lag_holdout_corr':float(zc),'delay_advantage_abs_corr':float(abs(ch)-abs(zc)),'phase_null_p':float(p)}


def analyze_sc2_stage_b(work,cfg):
    work=Path(work); out=work/'analysis'; cert=_load_manifest(work,'sc2_candidates.json'); pairs=_pairs(work); rows=[]
    for c in cert:
        rr=pairs.get(c['pair_id'],[]); rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0)
        if not rp or not rm or not r0: continue
        mf=np.load(work/c['mode_file'],allow_pickle=False); mode=np.asarray(mf['modes'][int(c['mode_index'])],float); center=np.asarray(mf['center'],float); ref=np.asarray(mf['reference'],float); offs=np.asarray(mf['component_offsets'],dtype=np.int64) if 'component_offsets' in mf.files else np.asarray([0,len(ref)],dtype=np.int64); w=mode_strain_weights(mode,ref,offs); met={}
        missing=False
        for branch in ('material','fixed'):
            fps=[_stage_b_file(work,branch,r) for r in (rp,rm,r0)]
            if not all(p.exists() for p in fps): missing=True; break
            zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nat,_=natural_response(_cut(z0,n)); a=project(nat,np.asarray([mode]),center)[:,0]; s=np.asarray(z0['sigma'][:n])@w; actual=float(t[-1]); period=float(c.get('period') or np.nan); minobs=float(cfg.get('sc2_stage_b_min_periods_observed',1.25))*period if np.isfinite(period) else np.inf; geom=bool(actual>=float(cfg.get('stage_b_discovery_time',0.8))+minobs and float(np.max(z0['ds_cv']))<=float(cfg.get('stage_b_hard_ds_cv',0.45))); d=delayed_phase_modulation_test(t,a,s,period,cfg) if geom else {}; met[branch]={'geometry_ok':geom,'actual_t_final':actual,'max_ds_cv':float(np.max(z0['ds_cv'])),**d}
        if missing: continue
        md,fd=met['material'],met['fixed']; sb1=bool(md.get('geometry_ok') and abs(md.get('holdout_corr',0))>=float(cfg.get('sc2_gate_min_stretch_phase_corr',0.30)) and md.get('phase_null_p',1)<=float(cfg.get('gate_max_phase_null_p',0.10))); sb2=bool(sb1 and md.get('delay_advantage_abs_corr',-99)>=float(cfg.get('gate_min_delay_advantage',0.05))); ms=abs(md.get('holdout_corr',0)); fs=abs(fd.get('holdout_corr',0)) if fd.get('geometry_ok') else 0.; sb3=bool(sb2 and (not fd.get('geometry_ok') or ms-fs>=float(cfg.get('gate_min_material_over_fixed_corr',0.08))))
        rows.append({**c,**{f'material_{k}':v for k,v in md.items()},**{f'fixed_{k}':v for k,v in fd.items()},'SCII_B1_stretch_phase_modulation':sb1,'SCII_B2_measured_delay_advantage':sb2,'SCII_B3_material_core_specificity':sb3,'sc2_mechanism_candidate':sb3})
    _savecsv(out/'blind_sc2_stage_b_results.csv',rows); mech=[r for r in rows if r.get('sc2_mechanism_candidate')]
    provp=out/'blind_sc2_provenance_summary.json'; prov=json.loads(provp.read_text(encoding='utf-8')) if provp.exists() else {}
    stageap=out/'blind_sc2_stage_a_summary.json'; stagea=json.loads(stageap.read_text(encoding='utf-8')) if stageap.exists() else {}
    gaugep=out/'blind_sc2_gauge_summary.json'; gauge=json.loads(gaugep.read_text(encoding='utf-8')) if gaugep.exists() else {}
    provisional=_load_manifest(work,'sc2_candidates_provisional.json')
    if mech:
        gate='PASS_SCII_CANDIDATE_PHASE_CLOCK_MECHANISM'; stage_b_status='PASS_SCII_CANDIDATE_PHASE_CLOCK_MECHANISM'
    elif cert:
        gate='PASS_SCII_PHASE_CLOCK__FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'; stage_b_status='FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'
    else:
        # Preserve the highest-level Stage-A verdict (including insufficient
        # coverage) when provenance/Stage B were never scientifically reached.
        gate=stagea.get('primary_gate') or gauge.get('primary_gate') or prov.get('primary_gate') or 'INDETERMINATE_SCII_NO_STAGE_A_RESULT'
        stage_b_status='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    stage_a_candidate_status=('SCII_PROVISIONAL_PHASE_CLOCK_FOUND' if provisional else 'NO_SCII_PROVISIONAL_PHASE_CLOCK')
    if cert:
        mesh_gauge_status='SCII_MESH_GAUGE_CERTIFIED_CANDIDATE_EXISTS'
    elif provisional:
        mesh_gauge_status='NO_SCII_MESH_GAUGE_CERTIFIED_CANDIDATE'
    else:
        mesh_gauge_status='NOT_REACHED_NO_PROVISIONAL_SCII_CANDIDATE'
    provenance_status=prov.get('provenance_status') or ('NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE' if not cert else prov.get('primary_gate'))
    summary={'format':'SST-SCII-INTRINSIC-MODAL-PHASE-CLOCK-BLIND-1.1','n_sc2_stage_a_candidates':len(cert),'n_stage_b_results':len(rows),'n_sc2_mechanism_candidates':len(mech),'stage_a_gate':stagea.get('primary_gate'),'mesh_gauge_gate':gauge.get('primary_gate'),'provenance_gate':prov.get('primary_gate'),'stage_a_candidate_status':stage_a_candidate_status,'mesh_gauge_status':mesh_gauge_status,'provenance_status':provenance_status,'stage_b_status':stage_b_status,'carrier_identity_read':False,'full_shape_recurrence_required':False,'overall_primary_gate':gate,'primary_gate':gate}; (out/'blind_sc2_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def sync_sc2_reporting(work):
    """Reporting-only v0.1.1 synchronizer.

    Reads existing SC-II analysis summaries/manifests and rewrites only
    ``blind_sc2_summary.json`` with the v0.1.1 status precedence.  No trajectory,
    modal metric, gate, candidate selection, or native physics is recomputed.
    """
    work=Path(work); out=work/'analysis'; out.mkdir(parents=True,exist_ok=True)
    def load(name):
        p=out/name
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    stagea=load('blind_sc2_stage_a_summary.json')
    gauge=load('blind_sc2_gauge_summary.json')
    prov=load('blind_sc2_provenance_summary.json')
    old=load('blind_sc2_summary.json')
    provisional=_load_manifest(work,'sc2_candidates_provisional.json')
    cert=_load_manifest(work,'sc2_candidates.json')
    n_stage_b=int(old.get('n_stage_b_results',0) or 0)
    n_mech=int(old.get('n_sc2_mechanism_candidates',0) or 0)
    if n_mech:
        gate='PASS_SCII_CANDIDATE_PHASE_CLOCK_MECHANISM'; stage_b_status=gate
    elif cert:
        gate='PASS_SCII_PHASE_CLOCK__FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'; stage_b_status='FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'
    else:
        # Coverage/status from Stage A is authoritative when no certified clock exists.
        gate=stagea.get('primary_gate') or gauge.get('primary_gate') or prov.get('primary_gate') or old.get('overall_primary_gate') or old.get('primary_gate') or 'INDETERMINATE_SCII_NO_STAGE_A_RESULT'
        stage_b_status='NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE'
    if cert: mesh_status='SCII_MESH_GAUGE_CERTIFIED_CANDIDATE_EXISTS'
    elif provisional: mesh_status='NO_SCII_MESH_GAUGE_CERTIFIED_CANDIDATE'
    else: mesh_status='NOT_REACHED_NO_PROVISIONAL_SCII_CANDIDATE'
    summary={
        'format':'SST-SCII-INTRINSIC-MODAL-PHASE-CLOCK-BLIND-1.1',
        'reporting_sync_only':True,
        'metrics_recomputed':False,
        'n_sc2_stage_a_candidates':len(cert),
        'n_stage_b_results':n_stage_b,
        'n_sc2_mechanism_candidates':n_mech,
        'stage_a_gate':stagea.get('primary_gate'),
        'mesh_gauge_gate':gauge.get('primary_gate'),
        'provenance_gate':prov.get('primary_gate'),
        'stage_a_candidate_status':'SCII_PROVISIONAL_PHASE_CLOCK_FOUND' if provisional else 'NO_SCII_PROVISIONAL_PHASE_CLOCK',
        'mesh_gauge_status':mesh_status,
        'provenance_status':prov.get('provenance_status') or ('NOT_REACHED_NO_CERTIFIED_SCII_CANDIDATE' if not cert else prov.get('primary_gate')),
        'stage_b_status':stage_b_status,
        'carrier_identity_read':False,
        'full_shape_recurrence_required':False,
        'overall_primary_gate':gate,
        'primary_gate':gate,
    }
    (out/'blind_sc2_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\\n',encoding='utf-8')
    return summary

from __future__ import annotations

from itertools import combinations
from pathlib import Path
import csv, json, math
import numpy as np

from .blind import load_catalog
from .modal import (
    analytic_signal, natural_response, odd_response, even_probe_contamination,
    learn_modes, project, mode_strain_weights, _harmonic_fit,
)
from .analyze import _stage_a_geometry_metrics
from .sc2 import (
    _pairs, _arm, _stage_a_file, _stage_b_file, _cut, _linfit_phase,
    _crossing_times, _coverage_gate, _rel_spread, _corr,
)
from .util import clean_json


def _savecsv(path, rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['carrier_id']
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:
            w.writerow({k:(json.dumps(clean_json(v),sort_keys=True) if isinstance(v,(list,dict,tuple)) else v) for k,v in r.items()})


def _fit_affine(t,y):
    # Deliberately freeze only the discovery-window center.  Extrapolating a
    # fitted discovery slope can manufacture a large artificial holdout drift
    # even for a perfect oscillator observed over a non-integer number of cycles.
    # The frozen POD spatial center already removes the dominant shape mean; this
    # scalar offset only fixes the modal-pair rotation origin without reading holdout.
    t=np.asarray(t,float); y=np.asarray(y,float); t0=float(t[0])
    return t0,np.asarray([float(np.mean(y)),0.0],float)


def _apply_affine(t,t0,b):
    t=np.asarray(t,float); b=np.asarray(b,float)
    return b[0]+b[1]*(t-float(t0))


def _wrap_pi(x):
    return float((float(x)+np.pi)%(2*np.pi)-np.pi)


def _pair_discovery_metrics(t,a,b,energy_a,energy_b,cfg,freq_a=None,freq_b=None,analytic_a=None,analytic_b=None):
    """Discovery-only pair eligibility. No holdout samples are read here."""
    t=np.asarray(t,float); a=np.asarray(a,float); b=np.asarray(b,float)
    if len(t)<24: return {'valid':False,'reason':'TOO_SHORT_DISCOVERY'}
    t0,ba=_fit_affine(t,a); _,bb=_fit_affine(t,b)
    x=a-_apply_affine(t,t0,ba); y=b-_apply_affine(t,t0,bb)
    ea=float(energy_a); eb=float(energy_b); total=ea+eb
    bal=float(min(ea,eb)/max(max(ea,eb),1e-30))
    circ=float(2*np.sqrt(max(ea,0)*max(eb,0))/max(total,1e-30))
    if freq_a is None:
        fa=_harmonic_fit(t,x); freq_a=None if not fa else float(fa['frequency'])
    if freq_b is None:
        fb=_harmonic_fit(t,y); freq_b=None if not fb else float(fb['frequency'])
    if freq_a is None or freq_b is None:
        return {'valid':False,'reason':'NO_DISCOVERY_OSCILLATORY_SUPPORT','trend_t0':t0,'trend_a':ba.tolist(),'trend_b':bb.tolist(),'combined_energy_fraction':total,'energy_balance_ratio':bal,'pair_circularity':circ}
    f1=float(freq_a); f2=float(freq_b); fmed=max(.5*(abs(f1)+abs(f2)),1e-15)
    fsplit=float(abs(f1-f2)/fmed)
    za=analytic_signal(x) if analytic_a is None else np.asarray(analytic_a); zb=analytic_signal(y) if analytic_b is None else np.asarray(analytic_b)
    cross=zb*np.conj(za); unit=cross/np.maximum(np.abs(cross),1e-15)
    meanvec=np.mean(unit); plv=float(abs(meanvec)); dphi=float(np.angle(meanvec))
    qerr=min(abs(_wrap_pi(dphi-np.pi/2)),abs(_wrap_pi(dphi+np.pi/2)))
    dx=np.gradient(x,t,edge_order=2); dy=np.gradient(y,t,edge_order=2); L=x*dy-y*dx
    r=np.sqrt(x*x+y*y); rel=r>=float(cfg.get('sciib_gate_min_radius_fraction_of_median',0.25))*max(float(np.median(r)),1e-15)
    Lr=L[rel] if np.any(rel) else L
    pos=float(np.mean(Lr>0)) if len(Lr) else 0.; neg=float(np.mean(Lr<0)) if len(Lr) else 0.; signfrac=max(pos,neg)
    orientation=1 if pos>=neg else -1
    return {
        'valid':True,'trend_t0':t0,'trend_a':ba.tolist(),'trend_b':bb.tolist(),
        'combined_energy_fraction':total,'energy_balance_ratio':bal,'pair_circularity':circ,
        'discovery_frequency_a':f1,'discovery_frequency_b':f2,'discovery_frequency_split':fsplit,
        'discovery_quadrature_plv':plv,'discovery_quadrature_mean_phase_rad':dphi,
        'discovery_quadrature_error_rad':float(qerr),'discovery_rotation_sign_fraction':float(signfrac),
        'orientation':int(orientation),
    }


def _pair_discovery_gate(m,cfg):
    return bool(
        m.get('valid')
        and m.get('combined_energy_fraction',0)>=float(cfg.get('sciib_gate_min_pair_discovery_energy',0.05))
        and m.get('energy_balance_ratio',0)>=float(cfg.get('sciib_gate_min_energy_balance_ratio',0.35))
        and m.get('pair_circularity',0)>=float(cfg.get('sciib_gate_min_pair_circularity',0.80))
        and m.get('discovery_frequency_split',99)<=float(cfg.get('sciib_gate_max_discovery_frequency_split',0.20))
        and m.get('discovery_quadrature_plv',0)>=float(cfg.get('sciib_gate_min_discovery_quadrature_plv',0.60))
        and m.get('discovery_quadrature_error_rad',99)<=float(cfg.get('sciib_gate_max_discovery_quadrature_error_rad',0.55))
        and m.get('discovery_rotation_sign_fraction',0)>=float(cfg.get('sciib_gate_min_discovery_rotation_sign_fraction',0.80))
    )


def _phase_core_metrics(t,x,y,cfg):
    t=np.asarray(t,float); x=np.asarray(x,float); y=np.asarray(y,float)
    if len(t)<40: return {'valid':False,'reason':'TOO_SHORT_HOLDOUT'}
    r=np.sqrt(x*x+y*y); medr=max(float(np.median(r)),1e-15)
    rel=r>=float(cfg.get('sciib_gate_min_radius_fraction_of_median',0.25))*medr
    ph=np.unwrap(np.arctan2(y,x)); ph=ph-ph[0]
    dph=np.diff(ph); monotonic=float(np.mean(dph>0)) if len(dph) else 0.
    wraps=float((ph[-1]-ph[0])/(2*np.pi))
    intercept,omega,pred,r2=_linfit_phase(t,ph); resid=ph-pred
    crossings=_crossing_times(t,ph); periods=np.diff(crossings)
    pcv=float(np.std(periods)/max(np.mean(periods),1e-15)) if len(periods)>=2 else np.inf
    pmed=float(np.median(periods)) if len(periods) else (2*np.pi/max(omega,1e-15) if omega>0 else np.inf)
    dt=float(np.median(np.diff(t))); lag=max(1,int(round(pmed/dt))) if np.isfinite(pmed) else len(t)
    pdiff=float(np.sqrt(np.mean((resid[lag:]-resid[:-lag])**2))) if lag<len(resid)-4 else np.inf
    rc=float(np.std(r)/medr); q=max(4,len(r)//4); ret=float(np.median(r[-q:])/max(np.median(r[:q]),1e-15)); reliable=float(np.mean(rel))
    dx=np.gradient(x,t,edge_order=2); dy=np.gradient(y,t,edge_order=2); L=x*dy-y*dx
    Lr=L[rel] if np.any(rel) else L
    rotfrac=float(np.mean(Lr>0)) if len(Lr) else 0.
    omega_inst=np.divide(Lr,np.maximum((r[rel] if np.any(rel) else r)**2,1e-15)) if len(Lr) else np.asarray([])
    omega_cv=float(np.std(omega_inst)/max(abs(np.mean(omega_inst)),1e-15)) if len(omega_inst)>=4 else np.inf
    frac=float(cfg.get('sciib_phase_calibration_fraction',0.40)); split=max(12,min(len(t)-12,int(round(frac*len(t)))))
    c0,w0,_,calr2=_linfit_phase(t[:split],ph[:split]); pp=c0+w0*t[split:]; err=ph[split:]-pp
    prms=float(np.sqrt(np.mean(err*err))) if len(err) else np.inf; terminal=float(abs(err[-1])) if len(err) else np.inf
    return {
        'valid':True,'radius_median':medr,'radius_cv':rc,'radius_retention_ratio':ret,'radius_reliable_fraction':reliable,
        'phase_wraps':wraps,'phase_monotonic_fraction':monotonic,'phase_linearity_r2':r2,'phase_calibration_r2':calr2,
        'frequency':float(omega/(2*np.pi)),'omega':float(omega),'period':float(pmed),'period_cv':pcv,
        'phase_diffusion_rms_rad':pdiff,'phase_prediction_rms_rad':prms,'phase_prediction_terminal_error_rad':terminal,
        'rotation_sign_fraction':rotfrac,'instantaneous_omega_cv':omega_cv,'n_phase_crossings':int(len(crossings)),
        'cycle_periods':periods.tolist(),
    }


def _basis_gauge_metrics(t,x,y,cfg):
    mats=[]
    for th in (0.0,0.37,0.91,1.31):
        c,s=np.cos(th),np.sin(th); mats.append(np.asarray([[c,-s],[s,c]],float))
    mats += [np.asarray([[0,1],[1,0]],float),np.asarray([[-1,0],[0,1]],float)]
    freq=[]; period=[]; diff=[]; r2=[]
    xy=np.c_[x,y]
    for Q in mats:
        q=xy@Q.T
        if np.linalg.det(Q)<0: q[:,1]*=-1.0
        m=_phase_core_metrics(t,q[:,0],q[:,1],cfg)
        if not m.get('valid'): continue
        freq.append(m['frequency']); period.append(m['period']); diff.append(m['phase_diffusion_rms_rad']); r2.append(m['phase_linearity_r2'])
    def rel(vals,floor=1e-15):
        a=np.asarray(vals,float); return float((np.max(a)-np.min(a))/max(abs(np.median(a)),floor)) if len(a)>=2 else np.inf
    return {'basis_gauge_frequency_rel_spread':rel(freq),'basis_gauge_period_rel_spread':rel(period),'basis_gauge_phase_diffusion_rel_spread':rel(diff,1e-6),'basis_gauge_phase_linearity_range':float(max(r2)-min(r2)) if len(r2)>=2 else np.inf}


def pair_phase_metrics(t,a,b,trend_t0,trend_a,trend_b,orientation,cfg):
    t=np.asarray(t,float); a=np.asarray(a,float); b=np.asarray(b,float)
    x=a-_apply_affine(t,trend_t0,trend_a); y=int(orientation)*(b-_apply_affine(t,trend_t0,trend_b))
    core=_phase_core_metrics(t,x,y,cfg)
    if not core.get('valid'): return core
    return {**core,**_basis_gauge_metrics(t,x,y,cfg)}


def pair_phase_gates(discovery,phase,cfg,channel):
    q1=_pair_discovery_gate(discovery,cfg)
    q2=bool(phase.get('valid') and phase.get('phase_wraps',0)>=float(cfg.get('sciib_gate_min_phase_wraps',4.0)) and phase.get('phase_monotonic_fraction',0)>=float(cfg.get('sciib_gate_min_monotonic_fraction',0.90)) and phase.get('rotation_sign_fraction',0)>=float(cfg.get('sciib_gate_min_rotation_sign_fraction',0.90)))
    q3=bool(phase.get('phase_linearity_r2',0)>=float(cfg.get('sciib_gate_min_phase_linearity_r2',0.90)) and phase.get('period_cv',99)<=float(cfg.get('sciib_gate_max_period_cv',0.15)) and phase.get('instantaneous_omega_cv',99)<=float(cfg.get('sciib_gate_max_instantaneous_omega_cv',0.50)))
    lo=float(cfg.get('sciib_gate_min_radius_retention_ratio',0.40)); hi=float(cfg.get('sciib_gate_max_radius_retention_ratio',2.50))
    q4=bool(phase.get('phase_diffusion_rms_rad',99)<=float(cfg.get('sciib_gate_max_phase_diffusion_rms_rad',0.75)) and phase.get('radius_cv',99)<=float(cfg.get('sciib_gate_max_radius_cv',0.60)) and lo<=phase.get('radius_retention_ratio',-1)<=hi and phase.get('radius_reliable_fraction',0)>=float(cfg.get('sciib_gate_min_radius_reliable_fraction',0.95)))
    q5=bool(phase.get('phase_prediction_rms_rad',99)<=float(cfg.get('sciib_gate_max_phase_prediction_rms_rad',1.00)) and phase.get('phase_prediction_terminal_error_rad',99)<=float(cfg.get('sciib_gate_max_phase_prediction_terminal_error_rad',1.57)))
    tol=float(cfg.get('sciib_gate_max_basis_gauge_rel_spread',1e-6))
    q6=bool(phase.get('basis_gauge_frequency_rel_spread',99)<=tol and phase.get('basis_gauge_period_rel_spread',99)<=tol and phase.get('basis_gauge_phase_diffusion_rel_spread',99)<=float(cfg.get('sciib_gate_max_basis_gauge_phase_diffusion_rel_spread',1e-5)))
    q7=bool(channel=='natural')
    return q1,q2,q3,q4,q5,q6,q7


def _manifest(work,name):
    p=Path(work)/'analysis'/name
    return json.loads(p.read_text(encoding='utf-8')).get('candidates',[]) if p.exists() else []


def analyze_sciib_stage_a(work,cfg):
    work=Path(work); out=work/'analysis'; modes_dir=out/'sciib_modes'; modes_dir.mkdir(parents=True,exist_ok=True)
    rows=[]; carriers=[]; candidates=[]; pairs=_pairs(work); disc_t=float(cfg.get('sciib_discovery_time',cfg.get('discovery_time',1.2))); eps=float(cfg.get('probe_eps',0.003)); topk=int(cfg.get('sciib_top_modes',cfg.get('top_modes',7)))
    for pid,rr in sorted(pairs.items()):
        rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); anchor=(rp or rm or r0 or {}); priority=bool(any(bool(r.get('certification_priority',False)) for r in rr)); base={'carrier_id':anchor.get('carrier_id',''),'pair_id':pid,'topology_group_id':anchor.get('topology_group_id',''),'provenance_group_id':anchor.get('provenance_group_id',''),'n_components':int(anchor.get('n_components',1)),'certification_priority':priority}
        if not rp or not rm or not r0:
            carriers.append({**base,'geometry_ok':False,'status':'MISSING_ARM','n_sciib_candidates':0}); continue
        fps=[_stage_a_file(work,r) for r in (rp,rm,r0)]
        if not all(p.exists() for p in fps):
            carriers.append({**base,'geometry_ok':False,'status':'MISSING_TRAJECTORY','n_sciib_candidates':0}); continue
        zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
        if not gm['geometry_ok']:
            status='INCOMPLETE_OR_MESH_GATE' if not gm['completion_ok'] else ('MESH_RATIO_GATE' if not gm['mesh_ratio_ok'] else 'DS_CV_GATE')
            carriers.append({**base,**gm,'status':status,'n_sciib_candidates':0}); continue
        n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nd=int(np.searchsorted(t,disc_t,side='right')); nd=max(24,min(n-40,nd))
        if nd>=n-40:
            carriers.append({**base,**gm,'status':'TOO_SHORT_FOR_SCIIB','n_sciib_candidates':0}); continue
        nat,ref=natural_response(_cut(z0,n)); carrier_candidates=0; even_ratio=float('nan'); channels=[('natural',nat)]
        if bool(cfg.get('sciib_analyze_odd_control',True)):
            odd,_=odd_response(_cut(zp,n),_cut(zm,n),eps); even=even_probe_contamination(_cut(zp,n),_cut(zm,n),_cut(z0,n)); even_ratio=float(np.sqrt(np.mean(even[:nd]**2))/max(eps*np.sqrt(np.mean(odd[:nd]**2)),1e-15)); channels.append(('odd',odd))
        for channel,response in channels:
            modes,ev,center=learn_modes(response,nd,topk); amps=project(response,modes,center)
            # Discovery frequency/analytic transforms are mode-local, so compute them once
            # rather than refitting the same mode for every O(K^2) pair.
            disc_centered=[amps[:nd,k]-float(np.mean(amps[:nd,k])) for k in range(len(modes))]
            disc_fits=[_harmonic_fit(t[:nd],disc_centered[k]) for k in range(len(modes))]
            disc_freq=[None if f is None else float(f['frequency']) for f in disc_fits]
            disc_analytic=[analytic_signal(disc_centered[k]) for k in range(len(modes))]
            modefile=modes_dir/f'{rp["carrier_id"]}_{channel}.npz'; np.savez_compressed(modefile,modes=modes,energy=ev,center=center,reference=ref,component_offsets=np.asarray(z0['component_offsets'],dtype=np.int64) if 'component_offsets' in z0.files else np.asarray([0,len(ref)],dtype=np.int64),discovery_time=float(t[nd-1]),channel=channel,phase_definition='atan2 of frozen near-degenerate POD mode pair; pair and modal-pair center frozen from discovery only')
            for i,j in combinations(range(len(modes)),2):
                dm=_pair_discovery_metrics(t[:nd],amps[:nd,i],amps[:nd,j],float(ev[i]),float(ev[j]),cfg,disc_freq[i],disc_freq[j],disc_analytic[i],disc_analytic[j]); eligible=_pair_discovery_gate(dm,cfg)
                pm=pair_phase_metrics(t[nd:],amps[nd:,i],amps[nd:,j],dm.get('trend_t0',t[0]),dm.get('trend_a',[0,0]),dm.get('trend_b',[0,0]),dm.get('orientation',1),cfg) if eligible else {'valid':False,'reason':'DISCOVERY_PAIR_GATE'}
                q1,q2,q3,q4,q5,q6,q7=pair_phase_gates(dm,pm,cfg,channel); cand=bool(gm['geometry_ok'] and q1 and q2 and q3 and q4 and q5 and q6 and q7)
                row={**base,**gm,'channel':channel,'mode_i':i,'mode_j':j,'mode_file':str(modefile.relative_to(work)),'mode_i_energy_fraction':float(ev[i]),'mode_j_energy_fraction':float(ev[j]),'even_probe_ratio':even_ratio,'SCIIB_Q1_discovery_pair':q1,'SCIIB_Q2_directed_multiphase_rotation':q2,'SCIIB_Q3_frequency_coherence':q3,'SCIIB_Q4_phase_radius_stability':q4,'SCIIB_Q5_out_of_sample_prediction':q5,'SCIIB_Q6_basis_gauge_invariance':q6,'SCIIB_Q7_natural_channel':q7,'sciib_provisional_candidate':cand,**{f'discovery_{k}':v for k,v in dm.items()},**{f'phase_{k}':v for k,v in pm.items()}}
                rows.append(row)
                if cand:
                    carrier_candidates+=1; candidates.append({'pair_id':pid,'carrier_id':rp['carrier_id'],'topology_group_id':rp.get('topology_group_id',''),'provenance_group_id':rp.get('provenance_group_id',''),'n_components':int(rp.get('n_components',1)),'channel':channel,'mode_i':i,'mode_j':j,'mode_file':str(modefile.relative_to(work)),'trend_t0':dm['trend_t0'],'trend_a':dm['trend_a'],'trend_b':dm['trend_b'],'orientation':dm['orientation'],'combined_energy_fraction':dm['combined_energy_fraction'],'pair_circularity':dm['pair_circularity'],'period':pm.get('period'),'frequency':pm.get('frequency'),'omega':pm.get('omega'),'phase_wraps':pm.get('phase_wraps'),'phase_linearity_r2':pm.get('phase_linearity_r2'),'period_cv':pm.get('period_cv'),'phase_diffusion_rms_rad':pm.get('phase_diffusion_rms_rad'),'phase_prediction_rms_rad':pm.get('phase_prediction_rms_rad'),'rotation_sign_fraction':pm.get('rotation_sign_fraction'),'certification_priority':priority})
        carriers.append({**base,**gm,'status':'VALID','even_probe_ratio':even_ratio,'n_sciib_candidates':carrier_candidates})
    _savecsv(out/'blind_sciib_pair_modal_results.csv',rows); _savecsv(out/'blind_sciib_carrier_summary.csv',carriers)
    (out/'sciib_candidates_provisional.json').write_text(json.dumps(clean_json({'format':'SST-SCIIB-PAIR-CANDIDATES-PROVISIONAL-1.0','candidates':candidates}),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (out/'sciib_candidates.json').write_text(json.dumps({'format':'SST-SCIIB-PAIR-CANDIDATES-CERTIFIED-1.0','candidates':[]},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    total=len(carriers); valid=sum(int(r.get('geometry_ok',False)) for r in carriers); ptotal=sum(int(r.get('certification_priority',False)) for r in carriers); pvalid=sum(int(r.get('certification_priority',False) and r.get('geometry_ok',False)) for r in carriers); cov=_coverage_gate(total,valid,ptotal,pvalid,cfg)
    if candidates: gate='PASS_SCIIB_PROVISIONAL_FROZEN_MODAL_PAIR_PHASE_CLOCK__REQUIRES_MESH_GAUGE_CERTIFICATION'
    elif cov['coverage_ok_for_global_fail']: gate='FAIL_SCIIB_NO_FROZEN_MODAL_PAIR_PHASE_CLOCK'
    else: gate='INDETERMINATE_SCIIB_INSUFFICIENT_VALID_COVERAGE'
    summary={'format':'SST-SCIIB-FROZEN-MODAL-PAIR-STAGE-A-BLIND-1.0','definition':'directed predictive phase rotation in a discovery-frozen 2D modal subspace; full-shape recurrence not required','n_carriers':total,'n_geometry_valid_carriers':valid,'n_mode_pairs_tested':len(rows),'n_sciib_provisional_candidates':len(candidates),'carriers_with_sciib_provisional_candidates':len(set(c['carrier_id'] for c in candidates)),'carrier_identity_read':False,'primary_channel':'natural','odd_channel_role':'diagnostic/null only','pair_selection_window':'discovery only','discovery_time_absolute':disc_t,**cov,'primary_gate':gate}
    (out/'blind_sciib_stage_a_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def _gauge_metrics(work,cfg,c,branch,rr):
    rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); fps=[_stage_a_file(work,r,branch) for r in (rp,rm,r0)]
    if not all(p.exists() for p in fps): return {'geometry_ok':False,'reason':'MISSING_GAUGE_TRAJECTORY'}
    zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
    if not gm['geometry_ok']: return gm
    mf=np.load(Path(work)/c['mode_file'],allow_pickle=False); modes=np.asarray(mf['modes'],float); center=np.asarray(mf['center'],float); n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nd=int(np.searchsorted(t,float(cfg.get('sciib_discovery_time',cfg.get('discovery_time',1.2))),side='right')); nd=max(24,min(n-40,nd)); resp,_=natural_response(_cut(z0,n)); a=project(resp,modes[[int(c['mode_i']),int(c['mode_j'])]],center)
    pm=pair_phase_metrics(t[nd:],a[nd:,0],a[nd:,1],c['trend_t0'],c['trend_a'],c['trend_b'],c['orientation'],cfg)
    # Discovery eligibility is frozen from baseline; gauge replay only tests the same subspace clock.
    fake={'valid':True,'combined_energy_fraction':c.get('combined_energy_fraction',1),'energy_balance_ratio':1,'pair_circularity':c.get('pair_circularity',1),'discovery_frequency_split':0,'discovery_quadrature_plv':1,'discovery_quadrature_error_rad':0,'discovery_rotation_sign_fraction':1}
    _,q2,q3,q4,q5,q6,q7=pair_phase_gates(fake,pm,cfg,'natural')
    return {**gm,**pm,'sciib_phase_ok':bool(q2 and q3 and q4 and q5 and q6 and q7)}


def analyze_sciib_gauge(work,cfg):
    work=Path(work); out=work/'analysis'; provisional=_manifest(work,'sciib_candidates_provisional.json'); pairs=_pairs(work); rows=[]; cert=[]
    for c in provisional:
        rr=pairs.get(c['pair_id'],[]); lo=_gauge_metrics(work,cfg,c,'stage_a_gauge_low',rr); hi=_gauge_metrics(work,cfg,c,'stage_a_gauge_high',rr)
        pspread=_rel_spread([c.get('period'),lo.get('period'),hi.get('period')]); wspread=_rel_spread([c.get('omega'),lo.get('omega'),hi.get('omega')]); dspread=_rel_spread([c.get('phase_diffusion_rms_rad'),lo.get('phase_diffusion_rms_rad'),hi.get('phase_diffusion_rms_rad')])
        ok=bool(lo.get('geometry_ok') and hi.get('geometry_ok') and lo.get('sciib_phase_ok') and hi.get('sciib_phase_ok') and pspread<=float(cfg.get('sciib_gate_max_mesh_gauge_period_spread',0.15)) and wspread<=float(cfg.get('sciib_gate_max_mesh_gauge_omega_spread',0.15)) and dspread<=float(cfg.get('sciib_gate_max_mesh_gauge_phase_diffusion_spread',0.50)))
        row={**c,'gauge_low_geometry_ok':lo.get('geometry_ok',False),'gauge_high_geometry_ok':hi.get('geometry_ok',False),'mesh_gauge_period_spread':pspread,'mesh_gauge_omega_spread':wspread,'mesh_gauge_phase_diffusion_spread':dspread,'mesh_gauge_invariant':ok}; rows.append(row)
        if ok: cert.append(row)
    _savecsv(out/'blind_sciib_gauge_results.csv',rows); (out/'sciib_candidates.json').write_text(json.dumps(clean_json({'format':'SST-SCIIB-PAIR-CANDIDATES-CERTIFIED-1.0','candidates':cert}),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    basep=out/'blind_sciib_stage_a_summary.json'; base=json.loads(basep.read_text(encoding='utf-8')) if basep.exists() else {}
    if cert: gate='PASS_SCIIB_FROZEN_MODAL_PAIR_PHASE_CLOCK_MESH_GAUGE_CERTIFIED'
    elif provisional: gate='FAIL_OR_INDETERMINATE_SCIIB_PROVISIONAL_PAIR_PHASE_NOT_MESH_GAUGE_INVARIANT'
    else: gate=base.get('primary_gate','INDETERMINATE_SCIIB_NO_STAGE_A_RESULT')
    summary={'format':'SST-SCIIB-MESH-GAUGE-BLIND-1.0','n_provisional_candidates':len(provisional),'n_mesh_gauge_certified_candidates':len(cert),'carriers_with_mesh_gauge_certified_candidates':len(set(c['carrier_id'] for c in cert)),'carrier_identity_read':False,'primary_gate':gate}; (out/'blind_sciib_gauge_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def analyze_sciib_provenance(work,cfg):
    work=Path(work); out=work/'analysis'; catalog=load_catalog(work); cert=_manifest(work,'sciib_candidates.json'); carrier_meta={}
    for r in catalog: carrier_meta.setdefault(r['carrier_id'],{'topology_group_id':r.get('topology_group_id',''),'provenance_group_id':r.get('provenance_group_id','')})
    by_top={}
    for cid,m in carrier_meta.items(): by_top.setdefault(m['topology_group_id'],{}).setdefault(m['provenance_group_id'],[]).append(cid)
    cert_by={}
    for c in cert: cert_by.setdefault(c['carrier_id'],[]).append(c)
    rows=[]; robust=0
    for top,fams in sorted(by_top.items()):
        fam_pass=[]; periods=[]
        for fam,cids in fams.items():
            cc=[x for cid in cids for x in cert_by.get(cid,[])]; fam_pass.append(bool(cc))
            if cc: periods.append(float(np.median([float(x['period']) for x in cc if x.get('period') is not None])))
        navail=len(fams); npass=sum(fam_pass); frac=float(npass/max(navail,1)); pspread=_rel_spread(periods)
        ok=bool(npass>=int(cfg.get('sciib_gate_min_provenance_source_families_for_robustness',2)) and frac>=float(cfg.get('sciib_gate_min_provenance_candidate_fraction',2/3)) and pspread<=float(cfg.get('sciib_gate_max_provenance_period_spread',0.30)))
        robust+=int(ok); rows.append({'topology_group_id':top,'n_source_families_available':navail,'n_source_families_with_sciib_clock':npass,'source_family_candidate_fraction':frac,'period_spread':pspread,'provenance_robust_sciib_clock':ok})
    _savecsv(out/'blind_sciib_provenance_results.csv',rows)
    stagep=out/'blind_sciib_stage_a_summary.json'; stage=json.loads(stagep.read_text(encoding='utf-8')) if stagep.exists() else {}
    if robust: gate='PASS_SCIIB_PROVENANCE_ROBUST_PAIR_PHASE_CLOCK'; status=gate
    elif cert: gate='PASS_SCIIB_SEED_SPECIFIC_PAIR_PHASE_CLOCK__PROVENANCE_NOT_ROBUST'; status='SCIIB_CERTIFIED_CLOCK_NOT_PROVENANCE_ROBUST'
    else: gate=stage.get('primary_gate','INDETERMINATE_SCIIB_NO_STAGE_A_RESULT'); status='NOT_REACHED_NO_CERTIFIED_SCIIB_CANDIDATE'
    summary={'format':'SST-SCIIB-PROVENANCE-BLIND-1.0','n_topology_groups':len(rows),'n_groups_with_provenance_robust_sciib_clock':robust,'n_certified_sciib_candidates':len(cert),'carrier_identity_read':False,'overall_primary_gate':gate,'provenance_status':status,'primary_gate':gate}; (out/'blind_sciib_provenance_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary


def _phase_series(t,a,b,c):
    x=np.asarray(a,float)-_apply_affine(t,c['trend_t0'],c['trend_a']); y=int(c['orientation'])*(np.asarray(b,float)-_apply_affine(t,c['trend_t0'],c['trend_b']))
    ph=np.unwrap(np.arctan2(y,x)); return x,y,ph-ph[0]


def delayed_pair_phase_modulation_test(t,x,y,stretch,period,cfg):
    t=np.asarray(t,float); ph=np.unwrap(np.arctan2(y,x)); omega=np.gradient(ph,t,edge_order=2); target=omega-np.median(omega); s=np.asarray(stretch,float)
    if len(target)>=9:
        ker=np.ones(5)/5; target=np.convolve(target,ker,mode='same'); s=np.convolve(s,ker,mode='same')
    disc=float(cfg.get('stage_b_discovery_time',0.8)); nd=int(np.searchsorted(t,disc,side='right')); nd=max(8,min(len(t)-8,nd)); dt=float(np.median(np.diff(t))); maxlag=max(2,min(nd//3,int(round(.75*period/dt)))) if np.isfinite(period) else max(2,nd//4)
    best=(0,0.)
    for lag in range(1,maxlag+1):
        if nd-lag<6: break
        cc=_corr(s[:nd-lag],target[lag:nd])
        if abs(cc)>abs(best[1]): best=(lag,cc)
    lag,cd=best; hs=s[nd:len(t)-lag] if len(t)-lag>nd else np.asarray([]); ht=target[nd+lag:] if len(t)>nd+lag else np.asarray([]); ch=_corr(hs,ht) if len(hs)>=6 else 0.; zc=_corr(s[nd:],target[nd:]) if len(t)-nd>=6 else 0.
    null=[]; nnull=int(cfg.get('n_phase_nulls',31)); m=len(hs)
    if m>=8:
        base=s[nd:].copy()
        for j in range(1,nnull+1):
            sh=max(1,int(round(j*len(base)/(nnull+1)))); null.append(abs(_corr(np.roll(base,sh)[:m],ht)))
    obs=abs(ch); p=(1+sum(v>=obs for v in null))/(1+len(null)) if null else 1.
    return {'lag_samples':int(lag),'delay':float(lag*dt),'discovery_corr':float(cd),'holdout_corr':float(ch),'zero_lag_holdout_corr':float(zc),'delay_advantage_abs_corr':float(abs(ch)-abs(zc)),'phase_null_p':float(p)}


def analyze_sciib_stage_b(work,cfg):
    work=Path(work); out=work/'analysis'; cert=_manifest(work,'sciib_candidates.json'); pairs=_pairs(work); rows=[]
    for c in cert:
        rr=pairs.get(c['pair_id'],[]); rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0)
        if not rp or not rm or not r0: continue
        mf=np.load(work/c['mode_file'],allow_pickle=False); modes=np.asarray(mf['modes'],float); center=np.asarray(mf['center'],float); ref=np.asarray(mf['reference'],float); offs=np.asarray(mf['component_offsets'],dtype=np.int64) if 'component_offsets' in mf.files else np.asarray([0,len(ref)],dtype=np.int64); i,j=int(c['mode_i']),int(c['mode_j']); w1=mode_strain_weights(modes[i],ref,offs); w2=mode_strain_weights(modes[j],ref,offs); met={}; missing=False
        for branch in ('material','fixed'):
            fps=[_stage_b_file(work,branch,r) for r in (rp,rm,r0)]
            if not all(p.exists() for p in fps): missing=True; break
            zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nat,_=natural_response(_cut(z0,n)); aa=project(nat,modes[[i,j]],center); x,y,ph=_phase_series(t,aa[:,0],aa[:,1],c); s1=np.asarray(z0['sigma'][:n])@w1; s2=np.asarray(z0['sigma'][:n])@w2; s2=int(c['orientation'])*s2; stan=-np.sin(ph)*s1+np.cos(ph)*s2; actual=float(t[-1]); period=float(c.get('period') or np.nan); minobs=float(cfg.get('sciib_stage_b_min_periods_observed',1.25))*period if np.isfinite(period) else np.inf; geom=bool(actual>=float(cfg.get('stage_b_discovery_time',0.8))+minobs and float(np.max(z0['ds_cv']))<=float(cfg.get('stage_b_hard_ds_cv',0.45))); d=delayed_pair_phase_modulation_test(t,x,y,stan,period,cfg) if geom else {}; met[branch]={'geometry_ok':geom,'actual_t_final':actual,'max_ds_cv':float(np.max(z0['ds_cv'])),**d}
        if missing: continue
        md,fd=met['material'],met['fixed']; b1=bool(md.get('geometry_ok') and abs(md.get('holdout_corr',0))>=float(cfg.get('sciib_gate_min_stretch_phase_corr',0.30)) and md.get('phase_null_p',1)<=float(cfg.get('gate_max_phase_null_p',0.10))); b2=bool(b1 and md.get('delay_advantage_abs_corr',-99)>=float(cfg.get('gate_min_delay_advantage',0.05))); ms=abs(md.get('holdout_corr',0)); fs=abs(fd.get('holdout_corr',0)) if fd.get('geometry_ok') else 0.; b3=bool(b2 and (not fd.get('geometry_ok') or ms-fs>=float(cfg.get('gate_min_material_over_fixed_corr',0.08))))
        rows.append({**c,**{f'material_{k}':v for k,v in md.items()},**{f'fixed_{k}':v for k,v in fd.items()},'SCIIB_B1_tangent_stretch_phase_modulation':b1,'SCIIB_B2_measured_delay_advantage':b2,'SCIIB_B3_material_core_specificity':b3,'sciib_mechanism_candidate':b3})
    _savecsv(out/'blind_sciib_stage_b_results.csv',rows); mech=[r for r in rows if r.get('sciib_mechanism_candidate')]
    stagep=out/'blind_sciib_stage_a_summary.json'; stage=json.loads(stagep.read_text(encoding='utf-8')) if stagep.exists() else {}; gaugep=out/'blind_sciib_gauge_summary.json'; gauge=json.loads(gaugep.read_text(encoding='utf-8')) if gaugep.exists() else {}; provp=out/'blind_sciib_provenance_summary.json'; prov=json.loads(provp.read_text(encoding='utf-8')) if provp.exists() else {}; provisional=_manifest(work,'sciib_candidates_provisional.json')
    if mech: gate='PASS_SCIIB_CANDIDATE_PAIR_PHASE_CLOCK_MECHANISM'; sbstatus=gate
    elif cert: gate='PASS_SCIIB_PAIR_PHASE_CLOCK__FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'; sbstatus='FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'
    else: gate=stage.get('primary_gate') or gauge.get('primary_gate') or prov.get('primary_gate') or 'INDETERMINATE_SCIIB_NO_STAGE_A_RESULT'; sbstatus='NOT_REACHED_NO_CERTIFIED_SCIIB_CANDIDATE'
    summary={'format':'SST-SCIIB-FROZEN-MODAL-PAIR-PHASE-CLOCK-BLIND-1.0','n_sciib_certified_candidates':len(cert),'n_stage_b_results':len(rows),'n_sciib_mechanism_candidates':len(mech),'stage_a_gate':stage.get('primary_gate'),'mesh_gauge_gate':gauge.get('primary_gate'),'provenance_gate':prov.get('primary_gate'),'stage_a_candidate_status':'SCIIB_PROVISIONAL_PAIR_PHASE_CLOCK_FOUND' if provisional else 'NO_SCIIB_PROVISIONAL_PAIR_PHASE_CLOCK','mesh_gauge_status':'SCIIB_MESH_GAUGE_CERTIFIED_CANDIDATE_EXISTS' if cert else ('NO_SCIIB_MESH_GAUGE_CERTIFIED_CANDIDATE' if provisional else 'NOT_REACHED_NO_PROVISIONAL_SCIIB_CANDIDATE'),'provenance_status':prov.get('provenance_status') or ('NOT_REACHED_NO_CERTIFIED_SCIIB_CANDIDATE' if not cert else prov.get('primary_gate')),'stage_b_status':sbstatus,'carrier_identity_read':False,'full_shape_recurrence_required':False,'pair_basis_rotation_invariance_required':True,'overall_primary_gate':gate,'primary_gate':gate}
    (out/'blind_sciib_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary

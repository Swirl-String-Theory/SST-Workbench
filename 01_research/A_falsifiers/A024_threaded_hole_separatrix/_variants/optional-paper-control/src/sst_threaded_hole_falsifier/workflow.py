from __future__ import annotations
from pathlib import Path
import csv,json,hashlib,math
import numpy as np
from .model import CurveSet
from .dynamics import analyze
from .native import backend_name
from .seal import seal
from .pressure import fit_free_power_exponent

PRIMARY=['initial_relative_equilibrium_residual','shape_auc','rpo_residual','max_real_growth_positive']
HOLE_PRIMARY=['hole_robustness_cost','hole_geometry_collapse_cost','hole_class_instability_cost','hole_lagrangian_incoherence_cost']

def load_config(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def load_candidate(catalog,rel):
    z=np.load(Path(catalog)/rel);return CurveSet(z['points'],z['offsets']),np.asarray(z['gammas'],float),int(z['n_carrier_components'])

def logratio(a,b,key,floor=1e-12,cap=1e12):
    xa=float(a[key]);xb=float(b[key]);xa=cap if not np.isfinite(xa) else min(max(xa,0.),cap);xb=cap if not np.isfinite(xb) else min(max(xb,0.),cap);return float(np.log((xa+floor)/(xb+floor)))

def _survival_decision(a,b,cfg):
    """Hierarchical contact gate. Truncated trajectories never use AUC/RPO/Floquet."""
    sa=a.get('dynamic_status');sb=b.get('dynamic_status');pa=(sa=='PASS_FULL_HORIZON');pb=(sb=='PASS_FULL_HORIZON')
    if pa and not pb:return {'winner_anonymous':'A','decision_basis':'CONTACT_GATE','median_log_ratio_A_over_B':float('-inf'),'metric_log_ratios_A_over_B':{},'n_metrics_A_better':0,'n_metrics_B_better':0}
    if pb and not pa:return {'winner_anonymous':'B','decision_basis':'CONTACT_GATE','median_log_ratio_A_over_B':float('inf'),'metric_log_ratios_A_over_B':{},'n_metrics_A_better':0,'n_metrics_B_better':0}
    if not pa and not pb:
        ta=float(a.get('actual_tau_end',0.));tb=float(b.get('actual_tau_end',0.));tol=float(cfg.get('contact_survival_tie_fraction',.03))*float(cfg.get('tau_end',1.0))
        win='A' if ta>tb+tol else 'B' if tb>ta+tol else 'TIE'
        return {'winner_anonymous':win,'decision_basis':'CONTACT_SURVIVAL_ONLY','median_log_ratio_A_over_B':None,'metric_log_ratios_A_over_B':{},'n_metrics_A_better':0,'n_metrics_B_better':0}
    return None

def decision(a,b,cfg):
    mode=str(cfg.get('decision_mode','self_confinement')).lower()
    if mode=='none':
        return {'winner_anonymous':'UNSCORED','decision_basis':'NO_BLIND_PAIR_SCORE','median_log_ratio_A_over_B':None,'metric_log_ratios_A_over_B':{},'n_metrics_A_better':0,'n_metrics_B_better':0}
    h=_survival_decision(a,b,cfg)
    if h is not None:return h
    if mode in ('hole_robustness','threaded_hole','kelvin_hole'):
        metrics=cfg.get('hole_primary_cost_metrics',HOLE_PRIMARY)
        basis='HOLE_ROBUSTNESS_COSTS'
    else:
        metrics=cfg.get('primary_metrics',PRIMARY)
        basis='FULL_HORIZON_PRIMARY_METRICS'
    vals={m:logratio(a,b,m,float(cfg.get('metric_floor',1e-12))) for m in metrics}
    med=float(np.median(list(vals.values())))
    margin=float(cfg.get('pair_tie_log_margin',math.log(1.03)))
    winner='A' if med<-margin else ('B' if med>margin else 'TIE')
    return {'winner_anonymous':winner,'decision_basis':basis,'median_log_ratio_A_over_B':med,'metric_log_ratios_A_over_B':vals,'n_metrics_A_better':sum(v<0 for v in vals.values()),'n_metrics_B_better':sum(v>0 for v in vals.values())}


def anonymous_delta_pressure_fit(a,b,cfg):
    """Blind active/null-invariant induced pressure diagnostics.

    Exponent and absolute monopole strength are identity invariant.  The signed
    monopole is stored as A-B and corrected only after reveal.
    """
    rr=np.asarray(a.get('radial_r',[]),float);pa=np.asarray(a.get('radial_p',[]),float);rb=np.asarray(b.get('radial_r',[]),float);pb=np.asarray(b.get('radial_p',[]),float);fitcfg=cfg.get('pressure_fit',{})
    if len(rr)<4 or len(rr)!=len(pa) or len(rr)!=len(rb) or len(rr)!=len(pb) or not np.allclose(rr,rb,rtol=1e-8,atol=1e-10):base={'nu_best':float('nan'),'r2_best':float('nan'),'coeff':float('nan'),'boundary_hit':True}
    else:base=fit_free_power_exponent(rr,pa-pb,float(fitcfg.get('nu_min',.10)),float(fitcfg.get('nu_max',4.0)),int(fitcfg.get('nu_steps',157)))
    qa=float(a.get('source_monopole',float('nan')));qb=float(b.get('source_monopole',float('nan')));aa=float(a.get('source_abs_integral',float('nan')));ab=float(b.get('source_abs_integral',float('nan')));dq=qa-qb;scale=.5*(aa+ab) if np.isfinite(aa) and np.isfinite(ab) else float('nan')
    al=a.get('pressure_convergence',{}).get('levels',[]) if isinstance(a.get('pressure_convergence',{}),dict) else [];bl=b.get('pressure_convergence',{}).get('levels',[]) if isinstance(b.get('pressure_convergence',{}),dict) else []
    vals=[];qvals=[];levels=[]
    for x,y in zip(al,bl):
        rx=np.asarray(x.get('radial_r',[]),float);px=np.asarray(x.get('radial_p',[]),float);ry=np.asarray(y.get('radial_r',[]),float);py=np.asarray(y.get('radial_p',[]),float)
        if len(rx)>=4 and len(rx)==len(px)==len(ry)==len(py) and np.allclose(rx,ry,rtol=1e-8,atol=1e-10):f=fit_free_power_exponent(rx,px-py,float(fitcfg.get('nu_min',.10)),float(fitcfg.get('nu_max',4.0)),int(fitcfg.get('nu_steps',157)))
        else:f={'nu_best':float('nan'),'r2_best':float('nan'),'coeff':float('nan'),'boundary_hit':True}
        qd=float(x.get('source_monopole',np.nan))-float(y.get('source_monopole',np.nan));levels.append({'grid_n':x.get('grid_n'),'box_half':x.get('box_half'),'source_monopole_A_minus_B':qd,**f})
        if np.isfinite(f['nu_best']) and not f['boundary_hit']:vals.append(float(f['nu_best']))
        if np.isfinite(qd):qvals.append(abs(qd))
    qspan=float(np.ptp(qvals)/max(np.median(qvals),1e-30)) if len(qvals)>1 else 0.0 if len(qvals)==1 else float('nan')
    return {'delta_far_profile_nu_blind':float(base['nu_best']),'delta_far_profile_r2_blind':float(base['r2_best']),'delta_far_profile_coeff_A_minus_B_blind':float(base['coeff']),'delta_far_profile_boundary_hit_blind':bool(base['boundary_hit']),'delta_source_monopole_A_minus_B_blind':float(dq),'delta_source_monopole_fraction_abs_blind':float(abs(dq)/max(scale,1e-30)) if np.isfinite(scale) else float('nan'),'delta_pressure_ladder_n_blind':len(levels),'delta_pressure_ladder_nu_span_blind':float(np.ptp(vals)) if len(vals)>1 else 0.0 if len(vals)==1 else float('nan'),'delta_pressure_ladder_monopole_rel_span_blind':qspan,'delta_pressure_ladder_levels_blind':levels}

def run_blind(project_root,catalog,outdir,config_path,limit=None):
    project_root=Path(project_root);catalog=Path(catalog);out=Path(outdir);out.mkdir(parents=True,exist_ok=True);cases=out/'cases';cases.mkdir(exist_ok=True);cfg=load_config(config_path)
    if cfg.get('require_native',False) and backend_name()!='cpp-pybind11':raise RuntimeError('Native C++/pybind11 backend required')
    rows=list(csv.DictReader(open(catalog/'pairs_public.csv',encoding='utf-8')));rows=rows[:limit] if limit else rows;cache={};pairs=[]
    for row in rows:
        rr={}
        for side in ('a','b'):
            cid=row[f'candidate_{side}'];rel=row[f'geometry_{side}']
            if cid not in cache:
                try:
                    cs,g,nc=load_candidate(catalog,rel);r=analyze(cs,g,nc,cfg);r.update({'status':'OK','backend':backend_name()})
                except Exception as e:r={'status':'ERROR','error':repr(e),'backend':backend_name()}
                cache[cid]=r;(cases/f'{cid}.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
            rr[side.upper()]=cache[cid]
        if rr['A'].get('status')=='OK' and rr['B'].get('status')=='OK':
            d=decision(rr['A'],rr['B'],cfg);valid=True;pf=anonymous_delta_pressure_fit(rr['A'],rr['B'],cfg)
        else:
            d={'winner_anonymous':'INDETERMINATE','decision_basis':'CASE_ERROR','median_log_ratio_A_over_B':None,'metric_log_ratios_A_over_B':{}};valid=False;pf={}
        rec={'pair_id':row['pair_id'],'candidate_a':row['candidate_a'],'candidate_b':row['candidate_b'],'valid':valid,**d,**pf};pairs.append(rec);(cases/f"{row['pair_id']}_pair.json").write_text(json.dumps(rec,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    fields=['pair_id','candidate_a','candidate_b','valid','winner_anonymous','decision_basis','median_log_ratio_A_over_B','n_metrics_A_better','n_metrics_B_better','delta_far_profile_nu_blind','delta_far_profile_r2_blind','delta_far_profile_coeff_A_minus_B_blind','delta_far_profile_boundary_hit_blind','delta_source_monopole_A_minus_B_blind','delta_source_monopole_fraction_abs_blind','delta_pressure_ladder_n_blind','delta_pressure_ladder_nu_span_blind','delta_pressure_ladder_monopole_rel_span_blind']
    with open(out/'blind_pair_results.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in pairs])
    summary={'campaign_format':'SST-THREADED-HOLE-BLIND-3.0','backend':backend_name(),'n_pairs':len(pairs),'n_valid_pairs':sum(bool(x['valid']) for x in pairs),'anonymous_wins':{x:sum(r.get('winner_anonymous')==x for r in pairs) for x in ('A','B','TIE','UNSCORED','INDETERMINATE')},'decision_bases':{x:sum(r.get('decision_basis')==x for r in pairs) for x in sorted(set(r.get('decision_basis','') for r in pairs))},'carrier_identity_read':False,'condition_identity_read':False,'gravity_target_used':False,'sst_target_values_used':False,'config_sha256':hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),'note':'v0.3.0: adds identity-blind Kelvin/McFarlane central-hole Lagrangian transport, finite-evolution persistence, and perturbation gates; v0.2.1 pressure/contact safeguards remain.'}
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8');sealed=seal(project_root,out,catalog,config_path);summary['sealed_result_tree_sha256']=sealed['result_tree_sha256'];return summary

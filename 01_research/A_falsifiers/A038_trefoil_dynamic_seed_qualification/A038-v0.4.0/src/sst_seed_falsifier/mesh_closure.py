"""S37B mesh-gauge closure diagnostics.

This module is intentionally diagnostic-only.  It does not relax or replace S37A,
and no S37B classification can promote a candidate into S40.

The central question is whether changing a *purely tangential* mesh controller changes
only the point labels / arclength parametrisation, or changes the embedded centreline.
"""
from __future__ import annotations

import math
from pathlib import Path
import numpy as np

from .dynamics import simulate, plan
from .geometry import align_cyclic, normalize_length, resample_closed, tangents
from .metrics import rolling_metrics, shape_distance


def _rms(v):
    v=np.asarray(v,float)
    return float(np.sqrt(np.mean(np.sum(v*v,axis=1)))) if len(v) else 0.0


def _state_at(traj,t):
    times=np.asarray(traj['t'],float)
    states=np.asarray(traj['x'],float)
    if len(times)==0: raise ValueError('EMPTY_TRAJECTORY')
    if t<=times[0]: return states[0].copy()
    if t>=times[-1]: return states[-1].copy()
    j=int(np.searchsorted(times,t,side='right'))
    j=max(1,min(j,len(times)-1))
    w=(float(t)-times[j-1])/max(times[j]-times[j-1],1e-30)
    return (1.0-w)*states[j-1]+w*states[j]


def displacement_decomposition(reference,comparison,coarse_stride=4):
    """Rigid/cyclic aligned raw-label displacement, split along the reference tangent.

    `shape_rms` is separately arclength-resampled and therefore approximately
    parameterisation invariant.  `raw_*` quantities intentionally retain the common
    material labels and expose the tangential point drift induced by a gauge controller.
    """
    ref=np.asarray(reference,float)
    cmp=np.asarray(comparison,float)
    if len(cmp)!=len(ref): cmp=resample_closed(cmp,len(ref))
    aligned,raw_rms,shift,R,translation=align_cyclic(cmp,ref,int(coarse_stride))
    delta=aligned-ref
    tt=tangents(ref)
    scalar=np.sum(delta*tt,axis=1)
    dpar=scalar[:,None]*tt
    dperp=delta-dpar
    tangential=_rms(dpar); normal=_rms(dperp)
    total=max(float(raw_rms),1e-30)
    return {
        'raw_label_rms':float(raw_rms),
        'tangential_rms':tangential,
        'normal_rms':normal,
        'normal_fraction':float(normal/total),
        'tangential_fraction':float(tangential/total),
        'shape_rms':float(shape_distance(cmp,ref,int(coarse_stride))),
        'cyclic_shift':int(shift),
    }


def trajectory_pair_metrics(reference,comparison,coarse_stride=4,samples=24):
    ta=np.asarray(reference['t'],float); tb=np.asarray(comparison['t'],float)
    if len(ta)<1 or len(tb)<1: return {'samples':0,'common_t_final':0.0}
    end=float(min(ta[-1],tb[-1])); start=float(max(ta[0],tb[0]))
    if end<start: return {'samples':0,'common_t_final':end}
    count=max(2,min(int(samples),max(2,len(ta)),max(2,len(tb))))
    times=np.linspace(start,end,count)
    rows=[]
    for t in times:
        rows.append(displacement_decomposition(_state_at(reference,t),_state_at(comparison,t),coarse_stride))
    keys=['raw_label_rms','tangential_rms','normal_rms','shape_rms','normal_fraction','tangential_fraction']
    out={'samples':int(count),'common_t_final':end,'final':rows[-1]}
    for k in keys:
        a=np.asarray([r[k] for r in rows],float)
        out[f'{k}_mean']=float(np.mean(a)); out[f'{k}_max']=float(np.max(a))
    return out


def convergence_order(ns,errors,floor=1e-12):
    """Fit e ~ N^-p.  Returns p; positive p means convergence with resolution."""
    n=np.asarray(ns,float); e=np.asarray(errors,float)
    mask=np.isfinite(n)&np.isfinite(e)&(n>0)&(e>float(floor))
    if np.count_nonzero(mask)<2: return None
    slope=float(np.polyfit(np.log(n[mask]),np.log(e[mask]),1)[0])
    return float(-slope)


def _arm_id(method,rate):
    if method=='none': return 'mesh_off'
    return f'{method}_r{float(rate):g}'.replace('.','p')


def _method_rates(cfg,method):
    table=cfg.get('mesh_closure_method_rates',{}) or {}
    vals=table.get(method,cfg.get('mesh_closure_rates',[2.4,4.0,5.6]))
    return [float(v) for v in vals]

def build_arms(cfg):
    methods=[str(v) for v in cfg.get('mesh_closure_methods',['segment_feedback','target_projection'])]
    arms=[{'arm_id':'mesh_off','method':'none','rate':0.0}]
    for method in methods:
        for rate in _method_rates(cfg,method): arms.append({'arm_id':_arm_id(method,rate),'method':method,'rate':rate})
    return arms


def run_resolution(x,cfg,n,T):
    x=normalize_length(resample_closed(np.asarray(x,float),int(n)),2*np.pi)
    steps,dt=plan(x,cfg,T)
    samples=int(cfg.get('mesh_closure_samples',96))
    guard_stride=max(1,int(math.ceil(steps/max(samples,1))))
    hard=float(cfg.get('mesh_closure_hard_ds_cv',0.60))
    cap=float(cfg.get('mesh_closure_mesh_max_relative_rms',cfg.get('mesh_max_relative_rms',1.0)))
    runs={}; summaries={}
    for arm in build_arms(cfg):
        tr=simulate(
            x,cfg,T,'global_volume',True,
            integration_plan=(steps,dt),guard_stride_override=guard_stride,
            max_ds_cv_override=hard,mesh_rate_override=arm['rate'],
            mesh_method_override=arm['method'],mesh_cap_override=cap,
            store_samples=samples,
        )
        m=rolling_metrics(tr,x,cfg)
        runs[arm['arm_id']]=tr
        summaries[arm['arm_id']]={
            'method':arm['method'],'rate':float(arm['rate']),'dt':float(tr['dt']),
            'integration_steps':int(tr['integration_steps']),'guard_stride':int(tr['guard_stride']),
            'completed':bool(tr['completed']),'stop_reason':str(tr['stop_reason']),
            'actual_t_final':float(tr['actual_t_final']),'score':float(m['score']),
            'shape_auc':float(m['shape_auc']),'shape_final_vs_initial':float(m['shape_final']),
            'max_ds_cv':float(m['max_ds_cv']),'min_gap_over_ds':float(m['min_gap_over_ds']),
            'max_mesh_ratio':float(m['max_mesh_ratio']),
        }
    off=runs['mesh_off']
    versus_off={}
    for arm_id,tr in runs.items():
        if arm_id=='mesh_off': continue
        versus_off[arm_id]=trajectory_pair_metrics(off,tr,int(cfg.get('cyclic_stride',4)),int(cfg.get('mesh_closure_compare_samples',24)))
    # Rate sensitivity inside one controller and controller sensitivity at matched rates.
    rate_pairs={}; controller_pairs={}
    methods=[str(v) for v in cfg.get('mesh_closure_methods',['segment_feedback','target_projection'])]
    method_rates={method:_method_rates(cfg,method) for method in methods}
    for method in methods:
        ids=[_arm_id(method,r) for r in method_rates[method]]
        vals=[]
        for i in range(len(ids)):
            for j in range(i+1,len(ids)):
                key=f'{ids[i]}__vs__{ids[j]}'
                pm=trajectory_pair_metrics(runs[ids[i]],runs[ids[j]],int(cfg.get('cyclic_stride',4)),int(cfg.get('mesh_closure_compare_samples',24)))
                rate_pairs[key]=pm; vals.append(pm.get('final',{}).get('shape_rms',float('nan')))
    if len(methods)>=2:
        common=sorted(set(method_rates[methods[0]]).intersection(method_rates[methods[1]]))
        for r in common:
            a=_arm_id(methods[0],r); b=_arm_id(methods[1],r); key=f'{a}__vs__{b}'
            controller_pairs[key]=trajectory_pair_metrics(runs[a],runs[b],int(cfg.get('cyclic_stride',4)),int(cfg.get('mesh_closure_compare_samples',24)))
    def max_final(mapping,key='shape_rms'):
        vals=[v.get('final',{}).get(key,float('nan')) for v in mapping.values()]
        vals=[float(v) for v in vals if np.isfinite(v)]
        return max(vals) if vals else float('nan')
    completed_all=all(v['completed'] for v in summaries.values())
    return {
        'resolution':int(n),'target_t_final':float(T),'frozen_plan':{'steps':int(steps),'dt':float(dt),'guard_stride':int(guard_stride)},
        'arms':summaries,'versus_mesh_off':versus_off,'within_controller_rate_pairs':rate_pairs,
        'matched_rate_controller_pairs':controller_pairs,'all_arms_completed':bool(completed_all),
        'max_shape_vs_off':max_final(versus_off,'shape_rms'),
        'max_normal_vs_off':max_final(versus_off,'normal_rms'),
        'max_tangential_vs_off':max_final(versus_off,'tangential_rms'),
        'max_rate_sensitivity_shape':max_final(rate_pairs,'shape_rms'),
        'max_controller_sensitivity_shape':max_final(controller_pairs,'shape_rms'),
    }


def classify_resolution_ladder(resolutions,cfg):
    rows=sorted(resolutions,key=lambda r:r['resolution']); fine=rows[-1]
    tol=float(cfg.get('mesh_closure_shape_tol',cfg.get('mesh_gauge_max_final_shape_distance',.035)))
    min_order=float(cfg.get('mesh_closure_min_convergence_order',0.5))
    min_levels=int(cfg.get('mesh_closure_min_resolution_levels_for_support',3))
    floor=float(cfg.get('mesh_closure_error_floor',1e-8))
    arm_ids=sorted({aid for r in rows for aid in r['versus_mesh_off']})
    orders={}
    for aid in arm_ids:
        ns=[]; es=[]
        for r in rows:
            pm=r['versus_mesh_off'].get(aid)
            if pm:
                ns.append(r['resolution']); es.append(pm.get('final',{}).get('shape_rms',float('nan')))
        orders[aid]=convergence_order(ns,es,floor)
    finite_orders=[v for v in orders.values() if v is not None and np.isfinite(v)]
    order_min=min(finite_orders) if finite_orders else None
    all_fine=bool(fine['all_arms_completed'])
    fine_shape=float(fine['max_shape_vs_off'])
    fine_controller=float(fine['max_controller_sensitivity_shape'])
    if not all_fine:
        status='NUMERICALLY_UNRESOLVED_AT_FINEST_RESOLUTION'
    elif np.isfinite(fine_shape) and (fine_shape>tol or (np.isfinite(fine_controller) and fine_controller>tol)):
        status='GEOMETRIC_CENTERLINE_COUPLED_TO_MESH_GAUGE'
    elif len(rows)<min_levels:
        status='INDETERMINATE_INSUFFICIENT_RESOLUTION_LEVELS'
    elif order_min is not None and order_min>=min_order:
        status='GAUGE_CLOSURE_SUPPORTED_DIAGNOSTIC_ONLY'
    else:
        status='INDETERMINATE_MESH_GAUGE_CLOSURE'
    return {
        'status':status,'diagnostic_only':True,'promotion_to_s40_allowed':False,
        'fine_resolution':int(fine['resolution']),'frozen_shape_tolerance':tol,
        'fine_max_shape_vs_off':fine_shape,'fine_max_normal_vs_off':float(fine['max_normal_vs_off']),
        'fine_max_tangential_vs_off':float(fine['max_tangential_vs_off']),
        'fine_max_rate_sensitivity_shape':float(fine['max_rate_sensitivity_shape']),
        'fine_max_controller_sensitivity_shape':fine_controller,
        'shape_vs_off_convergence_orders':orders,'minimum_finite_convergence_order':order_min,
        'required_minimum_convergence_order':min_order,'required_resolution_levels_for_support':min_levels,
    }

from __future__ import annotations
import numpy as np
from .geometry import normalize_length,resample_closed_periodic_cubic
from .dynamics import plan
from .operator_split import simulate_operator_split
from .metrics import rolling_metrics,shape_distance
from .shape_ratio import trefoil_shape_ratio_series


def _rel_span(a):
    a=np.asarray(a,float); return float((np.max(a)-np.min(a))/max(abs(np.median(a)),1e-12)) if len(a) else float('inf')


def run_resolution(base,cfg,n,T):
    x=normalize_length(resample_closed_periodic_cubic(base,int(n),oversample_factor=int(cfg.get('operator_split_remap_oversample_factor',16)),min_oversample=int(cfg.get('operator_split_remap_min_oversample',1024))),2*np.pi)
    frozen=plan(x,cfg,T); hard=float(cfg.get('operator_split_hard_ds_cv',.60))
    intervals=[float(v) for v in cfg.get('operator_split_remap_intervals',[.5,.25,.125])]
    arms=[]
    # physical-only is a diagnostic reference, not a required admission arm.
    for label,interval in [('physical_only',float('inf'))]+[(f'remap_{v:g}',v) for v in intervals]:
        tr=simulate_operator_split(x,cfg,T,remap_interval_override=interval,store_samples=int(cfg.get('operator_split_samples',96)),max_ds_cv_override=hard,integration_plan=frozen)
        m=rolling_metrics(tr,x,cfg); chi=trefoil_shape_ratio_series(tr,x,int(cfg.get('cyclic_stride',4)))
        arms.append({'label':label,'remap_interval':None if not np.isfinite(interval) else float(interval),'completed':bool(tr['completed']),
                     'stop_reason':tr['stop_reason'],'final_geometry':tr['x'][-1], 'metrics':m,'chi':chi,
                     'remap_event_count':int(tr['remap_event_count']),
                     'max_remap_shape_distance':float(np.max(tr['remap_shape_distance'])) if len(tr['remap_shape_distance']) else 0.0,
                     'max_ds_cv':float(np.max(tr['ds_cv']))})
    remap=[a for a in arms if a['label']!='physical_only']
    pair=[]
    for i in range(len(remap)):
        for j in range(i+1,len(remap)):
            pair.append(shape_distance(remap[i]['final_geometry'],remap[j]['final_geometry'],int(cfg.get('cyclic_stride',4))))
    sc=[a['metrics']['score'] for a in remap]; auc=[a['metrics']['shape_auc'] for a in remap]
    maxpair=float(max(pair) if pair else 0.0)
    row={'n':int(n),'integration_plan':{'steps':int(frozen[0]),'dt':float(frozen[1]),'target_t_final':float(T)},
         'all_remap_arms_completed':bool(all(a['completed'] for a in remap)),'max_pairwise_remap_shape_distance':maxpair,
         'score_rel_span':_rel_span(sc),'auc_rel_span':_rel_span(auc),
         'physical_only_completed':bool(arms[0]['completed']),'physical_only_stop_reason':arms[0]['stop_reason'],
         'max_event_shape_distance':float(max(a['max_remap_shape_distance'] for a in remap) if remap else 0.0),
         'arms':[{k:v for k,v in a.items() if k!='final_geometry'} for a in arms]}
    return row


def classify_resolution_ladder(rows,cfg):
    if not rows: return {'status':'INDETERMINATE_NO_DATA','qualified':False}
    rows=sorted(rows,key=lambda r:r['n']); finest=rows[-1]
    err=np.asarray([max(float(r['max_pairwise_remap_shape_distance']),float(cfg.get('operator_split_error_floor',1e-8))) for r in rows],float)
    ns=np.asarray([r['n'] for r in rows],float); floor=float(cfg.get('operator_split_error_floor',1e-8))
    if np.all(err<=floor*1.0001): order=float('inf'); conv='FLOOR_LIMITED'
    elif len(rows)>=3 and np.all(np.isfinite(err)) and np.all(err>0):
        order=float(-np.polyfit(np.log(ns),np.log(err),1)[0]); conv='ORDER_CONFIRMED' if order>=float(cfg.get('operator_split_min_convergence_order',.5)) else 'ORDER_NOT_CONFIRMED'
    else: order=None; conv='INSUFFICIENT_RESOLUTION_LEVELS'
    enough=len(rows)>=int(cfg.get('operator_split_min_resolution_levels_for_support',3))
    finest_ok=(finest['all_remap_arms_completed'] and
               finest['max_pairwise_remap_shape_distance']<=float(cfg.get('operator_split_max_final_shape_distance',cfg.get('mesh_gauge_max_final_shape_distance',.035))) and
               finest['score_rel_span']<=float(cfg.get('operator_split_max_score_rel_span',cfg.get('mesh_gauge_max_score_rel_span',.12))) and
               finest['auc_rel_span']<=float(cfg.get('operator_split_max_auc_rel_span',cfg.get('mesh_gauge_max_auc_rel_span',.20))))
    convergence_ok=conv in ('FLOOR_LIMITED','ORDER_CONFIRMED')
    qualified=bool(enough and finest_ok and convergence_ok)
    if qualified: status='OPERATOR_SPLIT_REMAP_CERTIFIED'
    elif not enough: status='INDETERMINATE_INSUFFICIENT_RESOLUTION_LEVELS'
    elif not finest['all_remap_arms_completed']: status='INDETERMINATE_REMAP_ARM_NUMERICS'
    elif not finest_ok: status='GEOMETRIC_CENTERLINE_REMAP_CADENCE_COUPLED'
    else: status='NUMERICALLY_UNRESOLVED_OPERATOR_SPLIT'
    return {'status':status,'qualified':qualified,'promotion_to_s40_allowed':qualified,'empirical_convergence_order':order,
            'convergence_status':conv,'finest_resolution':int(finest['n']),'finest_max_pairwise_remap_shape_distance':float(finest['max_pairwise_remap_shape_distance']),
            'physical_only_is_diagnostic_reference':True,'target_ratio_used':False}

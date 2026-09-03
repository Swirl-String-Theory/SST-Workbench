from pathlib import Path
import csv,hashlib,hmac,json,math
import numpy as np
from .io import load_json,dump_json,geom_sha
from .geometry import resample_closed,normalize_length,normal_frame,min_nonlocal_vertex_distance,segment_lengths
from .dynamics import simulate
from .metrics import rolling_metrics,recurrence_metrics,shape_distance
from .floquet import projected_floquet
from .causality import causal_gate
from .evidence import dynamics_contract,object_sha256
from .blind import sealed_private_dir
from .mesh_closure import run_resolution as run_mesh_closure_resolution, classify_resolution_ladder


def cfgload(path): return load_json(path)

def _ids(out): return [x['candidate_id'] for x in load_json(Path(out)/'public_manifest.json')['candidates']]

def _write_csv(path,rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    fields=sorted({k for r in rows for k,v in r.items() if not isinstance(v,(dict,list))})
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:r.get(k) for k in fields} for r in rows])

def _finite_number(value):
    if value is None or isinstance(value,(bool,np.bool_)): return False
    try: return bool(np.isfinite(float(value)))
    except (TypeError,ValueError): return False

def _group_map(out):
    out=Path(out); g={}
    p=out/'public_manifest.json'
    if p.exists():
        for r in load_json(p).get('candidates',[]): g[r['candidate_id']]=r.get('source_group_id','G_UNKNOWN')
    p=out/'stage25_refine'/'public_manifest.json'
    if p.exists():
        for r in load_json(p).get('candidates',[]): g[r['candidate_id']]=r.get('source_group_id',g.get(r.get('parent_candidate_id'),'G_UNKNOWN'))
    return g

def _stratified_ids(rows,k,groups,min_per_group=1,qualified_key=None):
    rows=[r for r in rows if qualified_key is None or bool(r.get(qualified_key,False))]
    k=max(0,int(k)); min_per_group=max(0,int(min_per_group)); chosen=[]
    group_order=[]
    for r in rows:
        gid=groups.get(r['candidate_id'],'G_UNKNOWN')
        if gid not in group_order: group_order.append(gid)
    for _round in range(min_per_group):
        for gid in group_order:
            for r in rows:
                cid=r['candidate_id']
                if groups.get(cid,'G_UNKNOWN')==gid and cid not in chosen:
                    chosen.append(cid); break
            if len(chosen)>=k: return chosen
    for r in rows:
        if r['candidate_id'] not in chosen: chosen.append(r['candidate_id'])
        if len(chosen)>=k: break
    return chosen

def _coverage(ids,groups):
    counts={}
    for cid in ids:
        gid=groups.get(cid,'G_UNKNOWN'); counts[gid]=counts.get(gid,0)+1
    return {'n_groups':len(counts),'counts':counts}

def _rel_span(a):
    a=np.asarray(a,float)
    return float((np.max(a)-np.min(a))/max(abs(np.median(a)),1e-12)) if len(a) else float('inf')

def _trajectory_shape_distance(a,b,coarse_stride=4,samples=24):
    ta=np.asarray(a['t'],float); tb=np.asarray(b['t'],float)
    if len(ta)<2 or len(tb)<2 or np.any(np.diff(ta)<=0) or np.any(np.diff(tb)<=0):
        return {'mean':float('inf'),'max':float('inf'),'samples':0}
    start=max(ta[0],tb[0]); end=min(ta[-1],tb[-1])
    if end<=start: return {'mean':float('inf'),'max':float('inf'),'samples':0}
    count=max(2,min(int(samples),len(ta),len(tb))); times=np.linspace(start,end,count)
    def at(tr,times,t):
        j=int(np.clip(np.searchsorted(times,t,side='right'),1,len(times)-1)); w=(t-times[j-1])/(times[j]-times[j-1])
        return (1-w)*tr['x'][j-1]+w*tr['x'][j]
    distances=[shape_distance(at(a,ta,t),at(b,tb,t),coarse_stride) for t in times]
    return {'mean':float(np.mean(distances)),'max':float(np.max(distances)),'samples':count,'time_start':float(start),'time_end':float(end)}

def _run_kind(cfg): return str(cfg.get('run_kind','blind_scientific'))

def _physics_for_run(cfg,value): return value if _run_kind(cfg)=='blind_scientific' else 'NOT_APPLICABLE_WORKFLOW_VALIDATION'

def _source_diversity(out):
    p=Path(out)/'prepare_summary.json'
    return load_json(p).get('source_diversity_status','UNKNOWN') if p.exists() else 'UNKNOWN'

def _temporal_classification(e1,e2,completed,cfg):
    floor=float(cfg.get('temporal_error_floor',1e-12))
    if completed and e1<=floor and e2<=floor: return 'FLOOR_LIMITED',None,True
    order=float(np.log2(e1/e2)) if e1>0 and e2>0 else None
    passed=bool(completed and order is not None and e2<e1 and order>=float(cfg.get('temporal_min_order',3.0)))
    return ('ORDER_CONFIRMED' if passed else 'FAILED'),order,passed

def _champion_cluster(rows,cfg):
    q=[r for r in rows if r.get('qualified')]
    if not q: return [],None,0.0
    q=sorted(q,key=lambda r:float(r['median_score']),reverse=True); top=float(q[0]['median_score']); band=float(cfg.get('champion_relative_score_band',.005))
    cluster=[r['candidate_id'] for r in q if (top-float(r['median_score']))/max(abs(top),1e-15)<=band]
    margin=(top-float(q[1]['median_score']))/max(abs(top),1e-15) if len(q)>1 else float('inf')
    unique=q[0]['candidate_id'] if margin>=float(cfg.get('unique_champion_min_relative_margin',.01)) else None
    return cluster,unique,float(margin)

def _rpo_eligibility(row,cfg):
    """S40->S50 contract, fail-closed but not equivalent to full-horizon completion.

    v0.2.0 permits an RPO candidate from a numerically valid *observed* window even if a
    later mesh stop occurs, provided the return itself occurred with good mesh/contact
    quality and the independent S37 mesh-gauge certification passed. Hard global FAILs,
    however, require the stronger coverage policy in stage_long().
    """
    if not bool(row.get('mesh_gauge_certified',False)): return False,'MESH_GAUGE_NOT_CERTIFIED'
    if not bool(row.get('observation_window_reached',False)): return False,'RPO_WINDOW_NOT_REACHED'
    if not _finite_number(row.get('actual_t_final')) or float(row['actual_t_final'])<float(cfg.get('rpo_min_observation_time',1.2)):
        return False,'INSUFFICIENT_OBSERVATION_TIME'
    if str(row.get('stop_reason'))=='CONTACT_GUARD_STOP': return False,'CONTACT_STOP'
    if not _finite_number(row.get('best_return')): return False,'NO_FINITE_BEST_RETURN'
    if not _finite_number(row.get('best_return_time')) or float(row['best_return_time'])<=0.0: return False,'NO_FINITE_POSITIVE_RETURN_TIME'
    if float(row['best_return_time'])<float(cfg.get('rpo_min_observation_time',1.2)): return False,'RETURN_BEFORE_MIN_OBSERVATION_TIME'
    if float(row['best_return'])>float(cfg['rpo_loose_return_threshold']): return False,'RETURN_ABOVE_LOOSE_THRESHOLD'
    if not _finite_number(row.get('ds_cv_at_best_return')) or float(row['ds_cv_at_best_return'])>float(cfg.get('rpo_max_ds_cv_at_return',.30)):
        return False,'MESH_QUALITY_BAD_AT_RETURN'
    if not _finite_number(row.get('gap_over_ds_at_best_return')) or float(row['gap_over_ds_at_best_return'])<float(cfg.get('rpo_min_gap_over_ds_at_return',1.0)):
        return False,'CONTACT_MARGIN_BAD_AT_RETURN'
    if not _finite_number(row.get('mesh_ratio_at_best_return')): return False,'NO_FINITE_LOCAL_MESH_RATIO'
    if float(row['mesh_ratio_at_best_return'])>float(cfg.get('long_max_mesh_ratio',.50)): return False,'MESH_RATIO_BAD_AT_RETURN'
    return True,'ELIGIBLE'

def _eligibility_counts(rows,cfg):
    counts={}
    for r in rows:
        _,reason=_rpo_eligibility(r,cfg); counts[reason]=counts.get(reason,0)+1
    return counts


def stage_early(out,cfg):
    out=Path(out); rows=[]; N=int(cfg['early_n']); T=float(cfg['early_t_final']); groups=_group_map(out)
    for cid in _ids(out):
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),N),2*np.pi)
        tr=simulate(x,cfg,T,'fixed',False); m=rolling_metrics(tr,x,cfg); rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),**m})
    rows.sort(key=lambda r:r['score'],reverse=True)
    promoted=_stratified_ids(rows,int(cfg['resolution_top_k']),groups,int(cfg.get('resolution_min_per_source',1)))
    _write_csv(out/'stage20_early'/'results.csv',rows)
    dump_json(out/'stage20_early'/'summary.json',{
        'run_kind':_run_kind(cfg),'numerics_verdict':'PASS' if rows else 'FAIL','physics_verdict':_physics_for_run(cfg,'UNTESTED'),'verdict':'PASS_EARLY_SCREEN' if rows else 'FAIL_NO_CANDIDATES','n':len(rows),'ranking_top_ids':[r['candidate_id'] for r in rows[:int(cfg['resolution_top_k'])]],
        'promoted_ids':promoted,'top_ids':promoted,'promotion_policy':'source_stratified_then_global','source_coverage':_coverage(promoted,groups),
        'ranking_identity_read':False,'pod_dimensionality_is_diagnostic_only':float(cfg.get('score_weights',{}).get('pod',0.0))==0.0,
    }); return rows


def stage_refine(out,cfg):
    out=Path(out); private_root=sealed_private_dir(out); early=list(csv.DictReader(open(out/'stage20_early'/'results.csv',encoding='utf-8'))); groups=_group_map(out)
    parents=_stratified_ids(early,int(cfg.get('refine_parent_k',6)),groups,int(cfg.get('refine_min_parents_per_source',1)))
    rng=np.random.default_rng(int(cfg.get('refine_seed',271828)))
    numeric_exempt={'candidate_id','stop_reason','source_group_id','completed','pod_is_diagnostic_only'}
    rows=[]
    for r in early:
        rr={}
        for k,v in r.items():
            if k in numeric_exempt: rr[k]=v
            else:
                try: rr[k]=float(v)
                except: rr[k]=v
        rows.append(rr)
    private={}; public=[]; N=int(cfg['early_n']); T=float(cfg['early_t_final'])
    for parent in parents:
        gid=groups.get(parent,'G_UNKNOWN'); base=normalize_length(resample_closed(np.load(out/'geometries'/f'{parent}.npy'),int(cfg['candidate_n'])),2*np.pi)
        for j in range(int(cfg.get('refine_variants_per_parent',4))):
            x=base.copy(); xy=float(rng.uniform(*cfg.get('refine_xy_scale_range',[.985,1.015]))); zz=float(rng.uniform(*cfg.get('refine_z_scale_range',[.97,1.03])))
            mode=int(rng.integers(1,int(cfg.get('refine_max_mode',6))+1)); an=float(rng.uniform(*cfg.get('refine_normal_amp_range',[-.018,.018]))); ab=float(rng.uniform(*cfg.get('refine_binormal_amp_range',[-.014,.014]))); ph=float(rng.uniform(0,2*np.pi))
            x[:,:2]*=xy; x[:,2]*=zz; x=normalize_length(x,2*np.pi); _,n,b=normal_frame(x); f=np.cos(2*np.pi*mode*np.arange(len(x))/len(x)+ph)[:,None]
            x=normalize_length(resample_closed(x+an*f*n+ab*f*b,len(x)),2*np.pi); gap=min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3)))/max(float(np.mean(segment_lengths(x))),1e-15)
            if gap<float(cfg.get('min_initial_gap_over_ds',1.3)): continue
            gh=hashlib.sha256(np.round(x,12).tobytes()).hexdigest(); cid='R'+hashlib.sha256(f'{parent}|{j}|{gh}'.encode()).hexdigest()[:14].upper(); np.save(out/'geometries'/f'{cid}.npy',x)
            private[cid]={'parent_candidate_id':parent,'source_group_id':gid,'parameters':{'xy_scale':xy,'z_scale':zz,'mode':mode,'normal_amp':an,'binormal_amp':ab,'phase':ph},'geom_sha':gh,'initial_gap_over_ds':gap}
            public.append({'candidate_id':cid,'parent_candidate_id':parent,'source_group_id':gid,'geom_sha':gh}); groups[cid]=gid
            xr=normalize_length(resample_closed(x,N),2*np.pi); tr=simulate(xr,cfg,T,'fixed',False); m=rolling_metrics(tr,xr,cfg); rows.append({'candidate_id':cid,'source_group_id':gid,**m})
    rows.sort(key=lambda r:float(r['score']),reverse=True)
    promoted=_stratified_ids(rows,int(cfg['resolution_top_k']),groups,int(cfg.get('resolution_min_per_source',1)))
    dump_json(out/'stage25_refine'/'public_manifest.json',{'n_refined':len(public),'parents':parents,'parameters_hidden':True,'private_refine_commitment_sha256':object_sha256(private),'private_refine_commitment_hash_basis':'canonical_json_sorted_compact_ascii_v1','candidates':public})
    dump_json(private_root/'stage25_refine'/'private_refine_map.json',private); _write_csv(out/'stage25_refine'/'results.csv',rows)
    dump_json(out/'stage25_refine'/'summary.json',{
        'run_kind':_run_kind(cfg),'numerics_verdict':'PASS' if public else 'INDETERMINATE','physics_verdict':_physics_for_run(cfg,'UNTESTED'),
        'n_original':len(early),'n_refined':len(public),'n_combined':len(rows),'parents':parents,'promoted_ids':promoted,'top_ids':promoted,
        'parent_source_coverage':_coverage(parents,groups),'promotion_source_coverage':_coverage(promoted,groups),
        'verdict':'PASS_BLIND_LOCAL_REFINEMENT' if public else 'NO_REFINEMENT_CANDIDATES'}); return rows


def stage_resolution(out,cfg):
    ladder=[int(n) for n in cfg['resolution_n']]
    if len(ladder)<2 or any(b<=a for a,b in zip(ladder[:-1],ladder[1:])): raise ValueError('SPATIAL_LADDER_REQUIRES_INCREASING_RESOLUTIONS')
    out=Path(out); groups=_group_map(out); rankfile=out/'stage25_refine'/'results.csv' if (out/'stage25_refine'/'results.csv').exists() else out/'stage20_early'/'results.csv'
    rank=list(csv.DictReader(open(rankfile,encoding='utf-8'))); ids=_stratified_ids(rank,int(cfg['resolution_top_k']),groups,int(cfg.get('resolution_min_per_source',1))); rows=[]
    for cid in ids:
        per=[]
        for N in cfg['resolution_n']:
            x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(N)),2*np.pi); tr=simulate(x,cfg,float(cfg['resolution_t_final']),'fixed',False,store_samples=int(cfg.get('resolution_compare_samples',24))); m=rolling_metrics(tr,x,cfg); per.append((int(N),m,tr))
        sc=np.array([m['score'] for _,m,_ in per]); co=np.array([m['rolling_coherence'] for _,m,_ in per]); au=np.array([m['shape_auc'] for _,m,_ in per])
        comparisons=[]
        for (n0,_m0,tr0),(n1,_m1,tr1) in zip(per[:-1],per[1:]):
            td=_trajectory_shape_distance(tr0,tr1,int(cfg.get('cyclic_stride',4)),int(cfg.get('resolution_compare_samples',24)))
            comparisons.append({'lower_n':n0,'higher_n':n1,'final_shape_distance':shape_distance(tr0['x'][-1],tr1['x'][-1],int(cfg.get('cyclic_stride',4))),'trajectory_mean_shape_distance':td['mean'],'trajectory_max_shape_distance':td['max'],'trajectory_samples':td['samples']})
        max_final=max((z['final_shape_distance'] for z in comparisons),default=0.0); max_traj=max((z['trajectory_max_shape_distance'] for z in comparisons),default=0.0)
        qualified=all(m['stop_reason']=='COMPLETED' for _,m,_ in per) and _rel_span(sc)<=float(cfg['resolution_score_rel_span_max']) and _rel_span(co)<=float(cfg['resolution_coherence_rel_span_max']) and _rel_span(au)<=float(cfg['resolution_auc_rel_span_max']) and max_final<=float(cfg.get('resolution_final_shape_distance_max',.02)) and max_traj<=float(cfg.get('resolution_trajectory_shape_distance_max',.025))
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'qualified':qualified,'median_score':float(np.median(sc)),'score_rel_span':_rel_span(sc),'coherence_rel_span':_rel_span(co),'auc_rel_span':_rel_span(au),'max_final_shape_distance':max_final,'max_trajectory_shape_distance':max_traj,'resolution_shape_comparisons':comparisons,'per_resolution':{str(N):m for N,m,_ in per}})
    rows.sort(key=lambda r:(r['qualified'],r['median_score']),reverse=True); dump_json(out/'stage30_resolution'/'results.json',rows)
    promoted=_stratified_ids(rows,int(cfg.get('temporal_top_k',cfg.get('core_top_k',cfg['long_top_k']))),groups,int(cfg.get('temporal_min_per_source',1)),'qualified')
    dump_json(out/'stage30_resolution'/'summary.json',{'run_kind':_run_kind(cfg),'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),'numerics_verdict':'PASS' if any(r['qualified'] for r in rows) else 'FAIL','physics_verdict':_physics_for_run(cfg,'UNTESTED'),'verdict':'PASS_RESOLUTION_QUALIFICATION' if any(r['qualified'] for r in rows) else 'FAIL_NO_RESOLUTION_STABLE_SEED'}); return rows


def stage_temporal(out,cfg):
    """Separate RK4 temporal convergence from the N-ladder spatial qualification."""
    out=Path(out); groups=_group_map(out); rr=load_json(out/'stage30_resolution'/'results.json')
    ids=_stratified_ids(rr,int(cfg.get('temporal_top_k',8)),groups,int(cfg.get('temporal_min_per_source',1)),'qualified'); rows=[]
    basefac=float(cfg.get('dt_factor',.025)); factors=[basefac*float(z) for z in cfg.get('temporal_dt_factor_multipliers',[1.0,.5,.25])]
    if len(factors)!=3: raise ValueError('temporal_dt_factor_multipliers must contain exactly 3 factors')
    if not np.allclose(np.asarray(factors[1:])/np.asarray(factors[:-1]),.5,rtol=1e-12,atol=0): raise ValueError('TEMPORAL_LADDER_MUST_HALVE_TIMESTEP')
    N=int(cfg.get('temporal_n',96)); T=float(cfg.get('temporal_t_final',cfg['resolution_t_final']))
    for cid in ids:
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),N),2*np.pi); trs=[]
        for fac in factors: trs.append(simulate(x,cfg,T,'fixed',False,dt_factor_override=fac,store_samples=int(cfg.get('temporal_samples',48))))
        e1=shape_distance(trs[0]['x'][-1],trs[1]['x'][-1],int(cfg.get('cyclic_stride',4))); e2=shape_distance(trs[1]['x'][-1],trs[2]['x'][-1],int(cfg.get('cyclic_stride',4)))
        completed=all(tr['stop_reason']=='COMPLETED' for tr in trs); mode,p,converged=_temporal_classification(e1,e2,completed,cfg)
        actual_dt=np.asarray([float(tr['dt']) for tr in trs]); ratios=actual_dt[:-1]/actual_dt[1:]
        if not np.allclose(ratios,2.0,rtol=float(cfg.get('temporal_dt_ratio_tolerance',.05)),atol=0): mode,p,converged='FAILED',None,False
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'qualified':bool(converged),'convergence_mode':mode,'error_h_h2':e1,'error_h2_h4':e2,'observed_order':p,'dt_factors':factors,'actual_dt':[float(tr['dt']) for tr in trs],'stop_reasons':[tr['stop_reason'] for tr in trs]})
    rows.sort(key=lambda r:(r['qualified'],r['convergence_mode']=='FLOOR_LIMITED',r['observed_order'] if r['observed_order'] is not None else -1e9),reverse=True); dump_json(out/'stage32_temporal'/'results.json',rows)
    promoted=_stratified_ids(rows,int(cfg.get('core_top_k',8)),groups,int(cfg.get('core_min_per_source',1)),'qualified')
    counts={mode:sum(r['convergence_mode']==mode for r in rows) for mode in ('FLOOR_LIMITED','ORDER_CONFIRMED','FAILED')}
    dump_json(out/'stage32_temporal'/'summary.json',{'run_kind':_run_kind(cfg),'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'convergence_mode_counts':counts,'top_ids':promoted,'source_coverage':_coverage(promoted,groups),'numerics_verdict':'PASS' if promoted else 'FAIL','physics_verdict':_physics_for_run(cfg,'UNTESTED'),'verdict':'PASS_TEMPORAL_RK4_CERTIFICATION' if promoted else 'FAIL_NO_TEMPORALLY_CERTIFIED_SEED'}); return rows


def stage_core(out,cfg):
    out=Path(out); groups=_group_map(out); tp=out/'stage32_temporal'/'results.json'; rr=load_json(tp) if tp.exists() else load_json(out/'stage30_resolution'/'results.json')
    ids=_stratified_ids(rr,int(cfg.get('core_top_k',cfg['long_top_k'])),groups,int(cfg.get('core_min_per_source',1)),'qualified'); rows=[]
    for cid in ids:
        per=[]
        for core in cfg.get('core_fraction_ladder',[.06,.08,.10]):
            cc=dict(cfg); cc['core_fraction']=float(core); x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg.get('core_n',96))),2*np.pi); tr=simulate(x,cc,float(cfg.get('core_t_final',cfg['resolution_t_final'])),'fixed',False); m=rolling_metrics(tr,x,cc); per.append((float(core),m))
        sc=np.asarray([m['score'] for _,m in per]); co=np.asarray([m['rolling_coherence'] for _,m in per])
        qualified=all(m['stop_reason']=='COMPLETED' for _,m in per) and _rel_span(sc)<=float(cfg.get('core_score_rel_span_max',.35)) and _rel_span(co)<=float(cfg.get('core_coherence_rel_span_max',.40))
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'qualified':qualified,'median_score':float(np.median(sc)),'score_rel_span':_rel_span(sc),'coherence_rel_span':_rel_span(co),'per_core':{str(c):m for c,m in per}})
    rows.sort(key=lambda r:(r['qualified'],r['median_score']),reverse=True); dump_json(out/'stage35_core_robustness'/'results.json',rows)
    promoted=_stratified_ids(rows,int(cfg.get('mesh_gauge_top_k',cfg['long_top_k'])),groups,int(cfg.get('mesh_gauge_min_per_source',1)),'qualified'); cluster,unique,margin=_champion_cluster(rows,cfg)
    dump_json(out/'stage35_core_robustness'/'summary.json',{
        'run_kind':_run_kind(cfg),'numerics_verdict':'PASS' if promoted else 'FAIL','physics_verdict':_physics_for_run(cfg,'UNTESTED'),'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),
        'core_fraction_ladder':cfg.get('core_fraction_ladder',[.06,.08,.10]),'champion_cluster_ids':cluster,'unique_champion_id':unique,'top_margin_relative':margin,
        'verdict':'PASS_CORE_ROBUST_SEEDS' if promoted else 'FAIL_NO_CORE_ROBUST_SEED'}); return rows


def stage_mesh_gauge(out,cfg):
    """Numerical mesh-gauge certification imported from the long-horizon modal programme."""
    out=Path(out); groups=_group_map(out); rr=load_json(out/'stage35_core_robustness'/'results.json')
    ids=_stratified_ids(rr,int(cfg.get('mesh_gauge_top_k',cfg['long_top_k'])),groups,int(cfg.get('mesh_gauge_min_per_source',1)),'qualified'); rows=[]
    base_rate=float(cfg.get('mesh_rate',4.0)); factors=[float(z) for z in cfg.get('mesh_gauge_factors',[.6,1.0,1.4])]
    N=int(cfg.get('mesh_gauge_n',cfg.get('long_n',96))); T=float(cfg.get('mesh_gauge_t_final',1.2)); hard=float(cfg.get('mesh_gauge_hard_ds_cv',.45))
    for cid in ids:
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),N),2*np.pi); per=[]; finals=[]
        for factor in factors:
            rate=base_rate*factor; tr=simulate(x,cfg,T,'global_volume',True,store_samples=int(cfg.get('mesh_gauge_samples',96)),mesh_rate_override=rate,max_ds_cv_override=hard)
            m=rolling_metrics(tr,x,cfg); rec=recurrence_metrics(tr,x,cfg); per.append((factor,rate,m,rec,tr)); finals.append(tr['x'][-1])
        pairdist=[]
        for i in range(len(finals)):
            for j in range(i+1,len(finals)): pairdist.append(shape_distance(finals[i],finals[j],int(cfg.get('cyclic_stride',4))))
        sc=np.asarray([z[2]['score'] for z in per]); auc=np.asarray([z[2]['shape_auc'] for z in per]); maxpair=float(max(pairdist) if pairdist else 0.0); maxmr=float(max(z[2]['max_mesh_ratio'] for z in per)); maxcv=float(max(z[2]['max_ds_cv'] for z in per))
        qualified=all(z[2]['stop_reason']=='COMPLETED' for z in per) and maxpair<=float(cfg.get('mesh_gauge_max_final_shape_distance',.035)) and _rel_span(sc)<=float(cfg.get('mesh_gauge_max_score_rel_span',.12)) and _rel_span(auc)<=float(cfg.get('mesh_gauge_max_auc_rel_span',.20)) and maxmr<=float(cfg.get('long_max_mesh_ratio',.50))
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'qualified':bool(qualified),'max_pairwise_final_shape_distance':maxpair,'score_rel_span':_rel_span(sc),'auc_rel_span':_rel_span(auc),'max_mesh_ratio':maxmr,'max_ds_cv':maxcv,'per_gauge':{str(f):{'mesh_rate':rate,**m,'recurrence':rec} for f,rate,m,rec,tr in per}})
    rows.sort(key=lambda r:(r['qualified'],-r['max_pairwise_final_shape_distance']),reverse=True); dump_json(out/'stage37_mesh_gauge'/'results.json',rows)
    promoted=_stratified_ids(rows,int(cfg['long_top_k']),groups,int(cfg.get('long_min_per_source',1)),'qualified')
    dump_json(out/'stage37_mesh_gauge'/'summary.json',{'run_kind':_run_kind(cfg),'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),'gauge_factors':factors,'frozen_max_final_shape_distance':float(cfg.get('mesh_gauge_max_final_shape_distance',.035)),'numerics_verdict':'PASS' if promoted else 'INDETERMINATE','physics_verdict':_physics_for_run(cfg,'UNTESTED'),'verdict':'PASS_MESH_GAUGE_CERTIFIED_SEEDS' if promoted else 'INDETERMINATE_NO_MESH_GAUGE_CERTIFIED_SEED'}); return rows



def stage_mesh_closure(out,cfg):
    """S37B diagnostic: separate mesh reparameterisation from geometric centreline drift.

    This stage intentionally reads the S35 core-qualified set, not the S37A-qualified
    set, because its purpose is to diagnose *why* S37A failed.  It is strictly
    diagnostic-only: no S37B status can promote a candidate to S40.
    """
    out=Path(out); groups=_group_map(out)
    core=load_json(out/'stage35_core_robustness'/'results.json')
    ids=_stratified_ids(core,int(cfg.get('mesh_closure_top_k',cfg.get('mesh_gauge_top_k',8))),groups,
                        int(cfg.get('mesh_closure_min_per_source',1)),'qualified')
    ladder=[int(n) for n in cfg.get('mesh_closure_resolution_ladder',[64,96,128])]
    if not ladder or any(n<16 for n in ladder): raise ValueError('INVALID_MESH_CLOSURE_RESOLUTION_LADDER')
    T=float(cfg.get('mesh_closure_t_final',cfg.get('mesh_gauge_t_final',1.2)))
    rows=[]
    for cid in ids:
        base=np.load(out/'geometries'/f'{cid}.npy')
        per=[]
        for n in ladder:
            per.append(run_mesh_closure_resolution(base,cfg,n,T))
        classification=classify_resolution_ladder(per,cfg)
        rows.append({
            'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),
            'resolution_ladder':per,'closure':classification,
            'diagnostic_only':True,'promotion_to_s40_allowed':False,
        })
    dump_json(out/'stage37b_mesh_closure'/'results.json',rows)
    counts={}
    for r in rows:
        st=r['closure']['status']; counts[st]=counts.get(st,0)+1
    summary={
        'format':'SST-TREFOIL-MESH-GAUGE-CLOSURE-DIAGNOSTIC-1',
        'run_kind':_run_kind(cfg),'n_tested':len(rows),'status_counts':counts,
        'candidate_ids':ids,'source_coverage':_coverage(ids,groups),
        'resolution_ladder':ladder,'mesh_methods':['none']+[str(v) for v in cfg.get('mesh_closure_methods',['segment_feedback','target_projection'])],
        'mesh_rates':[float(v) for v in cfg.get('mesh_closure_rates',[2.4,4.0,5.6])],
        'mesh_method_rates':cfg.get('mesh_closure_method_rates',{}),
        'diagnostic_only':True,'promotion_to_s40_allowed':False,
        's37a_admission_gate_unchanged':True,
        'numerics_verdict':'DIAGNOSTIC_COMPLETE' if rows else 'NOT_RUN_NO_CORE_QUALIFIED_SEEDS',
        'physics_verdict':_physics_for_run(cfg,'INDETERMINATE'),
        'verdict':'DIAGNOSTIC_MESH_GAUGE_CLOSURE_REPORTED' if rows else 'NOT_RUN_NO_CORE_QUALIFIED_SEEDS',
    }
    dump_json(out/'stage37b_mesh_closure'/'summary.json',summary)
    return rows

def stage_long(out,cfg):
    out=Path(out); groups=_group_map(out); gp=out/'stage37_mesh_gauge'/'results.json'; cp=out/'stage35_core_robustness'/'results.json'
    rr=load_json(gp) if gp.exists() else load_json(cp); ids=_stratified_ids(rr,int(cfg['long_top_k']),groups,int(cfg.get('long_min_per_source',1)),'qualified'); rows=[]; (out/'stage40_long'/'trajectories').mkdir(parents=True,exist_ok=True)
    mesh_cert=set(ids) if gp.exists() else set(); contract,contract_hash=dynamics_contract(cfg,int(cfg['long_n']))
    for cid in ids:
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['long_n'])),2*np.pi)
        tr=simulate(x,cfg,float(cfg['long_t_final']),'global_volume',True,store_samples=int(cfg.get('long_samples',240)),max_ds_cv_override=float(cfg.get('long_hard_ds_cv',.45)))
        np.savez_compressed(out/'stage40_long'/'trajectories'/f'{cid}.npz',**tr); rec=recurrence_metrics(tr,x,cfg); m=rolling_metrics(tr,x,cfg)
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'mesh_gauge_certified':cid in mesh_cert,'dynamics_contract':contract,'dynamics_contract_sha256':contract_hash,'dynamics_replay':{'dt':float(tr['dt']),'guard_stride':int(tr['guard_stride'])},**rec,'long_score':m['score'],'max_mesh_ratio':float(np.max(tr['mesh_ratio'])),'max_ds_cv':float(np.max(tr['ds_cv'])),'min_gap_over_ds':float(np.min(tr['gap_over_ds']))})
    rows.sort(key=lambda r:(_rpo_eligibility(r,cfg)[0],r['n_returns']>0,-float(r['best_return']) if _finite_number(r.get('best_return')) else -1e9,r['long_score']),reverse=True); dump_json(out/'stage40_long'/'results.json',rows)
    eligible=[r for r in rows if _rpo_eligibility(r,cfg)[0]]; cand=[r['candidate_id'] for r in eligible[:int(cfg['rpo_top_k'])]]
    nwin=sum(bool(r.get('observation_window_reached')) for r in rows); nfull=sum(bool(r.get('completed')) for r in rows); n=len(rows); min_count=int(cfg.get('long_min_window_valid_count',max(1,min(3,n)))); min_frac=float(cfg.get('long_min_window_valid_fraction_for_fail',.60)); full_frac=float(cfg.get('long_min_full_horizon_fraction_for_fail',.60)); coverage_ok=n>0 and nwin>=min_count and nwin/n>=min_frac; full_ok=n>0 and nfull/n>=full_frac
    if cand: verdict='PASS_NEAR_RPO_CANDIDATES'
    elif not coverage_ok: verdict='INDETERMINATE_RPO_WINDOW_NUMERICAL_COVERAGE'
    elif not full_ok: verdict='INDETERMINATE_RPO_LONG_HORIZON_COVERAGE'
    else: verdict='FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE'
    dump_json(out/'stage40_long'/'summary.json',{
        'n_tested':n,'n_observation_window_reached':nwin,'n_full_horizon_completed':nfull,'window_coverage_fraction':nwin/max(n,1),'full_horizon_fraction':nfull/max(n,1),
        'n_near_rpo_candidates':len(cand),'top_ids':cand,'source_coverage':_coverage(ids,groups),'mesh_ratio_gate_max':float(cfg.get('long_max_mesh_ratio',.50)),
        'eligibility_counts':_eligibility_counts(rows,cfg),'hard_fail_coverage_satisfied':bool(coverage_ok and full_ok),'dynamics_contract':contract,'dynamics_contract_sha256':contract_hash,
        'run_kind':_run_kind(cfg),'numerics_verdict':'PASS' if n>0 and nwin>0 else 'INDETERMINATE','physics_verdict':_physics_for_run(cfg,'SUPPORTED_CANDIDATE' if cand else ('FAIL' if verdict=='FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE' else 'INDETERMINATE')),'verdict':verdict}); return rows


def stage_rpo(out,cfg):
    out=Path(out); rows=[]; long=load_json(out/'stage40_long'/'results.json'); ls=load_json(out/'stage40_long'/'summary.json'); eligible=[]; rejected=[]; contract,contract_hash=dynamics_contract(cfg,int(cfg['rpo_n']))
    for r in long:
        ok,reason=_rpo_eligibility(r,cfg)
        if ok and r.get('dynamics_contract_sha256')!=contract_hash: ok,reason=False,'DYNAMICS_CONTRACT_MISMATCH'
        if ok and (not _finite_number(r.get('dynamics_replay',{}).get('dt')) or float(r['dynamics_replay']['dt'])<=0 or int(r.get('dynamics_replay',{}).get('guard_stride',0))<1): ok,reason=False,'MISSING_DYNAMICS_REPLAY'
        if ok: eligible.append(r)
        else: rejected.append({'candidate_id':r.get('candidate_id'),'reason':reason})
    pool=eligible[:int(cfg['rpo_top_k'])]
    for r in pool:
        cid=r['candidate_id']; x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['rpo_n'])),2*np.pi); fl=projected_floquet(x,float(r['best_return_time']),cfg,expected_contract_sha256=r['dynamics_contract_sha256'],replay=r['dynamics_replay'])
        passed=bool(fl['quality_completed'] and fl['base_return']<=float(cfg['rpo_return_threshold']) and fl['spectral_radius']<=float(cfg['floquet_rho_max']))
        rows.append({'candidate_id':cid,'period':float(r['best_return_time']),'rpo_floquet_pass':passed,'projected_floquet_candidate_pass':passed,**fl})
    rows.sort(key=lambda r:(r['rpo_floquet_pass'],-r['spectral_radius'] if np.isfinite(r['spectral_radius']) else -1e9,-r['base_return']),reverse=True); dump_json(out/'stage50_rpo_floquet'/'results.json',rows)
    champ=[r['candidate_id'] for r in rows if r['rpo_floquet_pass']][:int(cfg['mechanism_top_k'])]
    if champ: verdict='PASS_PROJECTED_FLOQUET_CANDIDATE'
    elif rows: verdict='FAIL_NO_PROJECTED_FLOQUET_CANDIDATE'
    elif str(ls.get('verdict','')).startswith('INDETERMINATE'): verdict='NOT_RUN_RPO_INDETERMINATE_LONG_NUMERICS'
    elif ls.get('verdict')=='FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE': verdict='NOT_RUN_NO_NEAR_RPO_AFTER_VALID_COVERAGE'
    else: verdict='NOT_RUN_NO_RPO_ELIGIBLE_CANDIDATE'
    dump_json(out/'stage50_rpo_floquet'/'summary.json',{'run_kind':_run_kind(cfg),'n_long_rows':len(long),'n_eligible_from_stage40':len(eligible),'n_rejected_from_stage40':len(rejected),'rejected':rejected,'n_tested':len(rows),'n_projected_floquet_pass':len(champ),'champion_ids':champ,'dynamics_contract':contract,'dynamics_contract_sha256':contract_hash,'floquet_scope':'projected_fourier_normal_subspace','numerics_verdict':'PASS' if rows and all(r['quality_completed'] for r in rows) else ('NOT_RUN' if not rows else 'FAIL'),'physics_verdict':_physics_for_run(cfg,'SUPPORTED_CANDIDATE' if champ else ('INDETERMINATE' if not rows else 'FAIL_PROJECTED_GATE')),'verdict':verdict}); return rows


def stage_mechanism(out,cfg):
    out=Path(out); rpo=load_json(out/'stage50_rpo_floquet'/'results.json'); rows=[]
    for r in [z for z in rpo if z['rpo_floquet_pass']][:int(cfg['mechanism_top_k'])]:
        cid=r['candidate_id']; x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['mechanism_n'])),2*np.pi); T=max(float(cfg.get('mechanism_min_t',1.0)),float(r['period'])*float(cfg.get('mechanism_periods',1.5))); cg=causal_gate(x,T,cfg); rows.append({'candidate_id':cid,'period':r['period'],**cg})
    dump_json(out/'stage60_finite_core_clock'/'results.json',rows); ok=[r for r in rows if r['predictive_specificity_gate_pass']]
    mech={'run_kind':_run_kind(cfg),'n_tested':len(rows),'n_predictive_specificity_pass':len(ok),'n_mechanism_pass':len(ok),'causal_claim_authorized':False,'numerics_verdict':'PASS' if rows and all(r['material']['completed'] and r['fixed']['completed'] for r in rows) else ('NOT_RUN' if not rows else 'FAIL'),'physics_verdict':_physics_for_run(cfg,'SUPPORTED_PREDICTIVE_ASSOCIATION' if ok else ('INDETERMINATE' if not rows else 'FAIL_PREDICTIVE_GATE')),'verdict':'PASS_DELAY_PREDICTIVE_SPECIFICITY_CANDIDATE' if ok else ('FAIL_PREDICTIVE_SPECIFICITY_ON_PROJECTED_RPO' if rows else 'NOT_RUN_NO_PROJECTED_RPO')}; dump_json(out/'stage60_finite_core_clock'/'summary.json',mech)
    summaries={}
    for nm,rel in [('early','stage20_early/summary.json'),('refine','stage25_refine/summary.json'),('resolution','stage30_resolution/summary.json'),('temporal','stage32_temporal/summary.json'),('core','stage35_core_robustness/summary.json'),('mesh_gauge','stage37_mesh_gauge/summary.json'),('mesh_closure','stage37b_mesh_closure/summary.json'),('long','stage40_long/summary.json'),('rpo','stage50_rpo_floquet/summary.json')]:
        pp=out/rel
        if pp.exists(): summaries[nm]=load_json(pp)
    diversity=_source_diversity(out)
    if str(diversity).startswith('INDETERMINATE'): verdict='CHAIN_'+diversity
    elif ok: verdict='CHAIN_PASS_PREDICTIVE_SPECIFICITY_CANDIDATE'
    elif rows: verdict='CHAIN_PROJECTED_RPO__MECHANISM_FAIL_OR_INDETERMINATE'
    elif summaries.get('rpo',{}).get('n_projected_floquet_pass',0)>0: verdict='CHAIN_PROJECTED_RPO_ONLY'
    elif summaries.get('long',{}).get('n_near_rpo_candidates',0)>0: verdict='CHAIN_NEAR_RPO_ONLY'
    elif summaries.get('mesh_gauge',{}).get('n_qualified',0)<=0 and summaries.get('core',{}).get('n_qualified',0)>0: verdict='CHAIN_CORE_ROBUST_SEEDS__MESH_GAUGE_NOT_CERTIFIED'
    elif summaries.get('mesh_gauge',{}).get('n_qualified',0)>0 and str(summaries.get('long',{}).get('verdict','')).startswith('INDETERMINATE'): verdict='CHAIN_MESH_GAUGE_CERTIFIED__RPO_NOT_TESTABLE_NUMERICALLY'
    elif summaries.get('long',{}).get('verdict')=='FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE': verdict='CHAIN_VALID_LONG_COVERAGE__NO_NEAR_RPO'
    elif summaries.get('mesh_gauge',{}).get('n_qualified',0)>0: verdict='CHAIN_MESH_GAUGE_CERTIFIED_SEEDS__LONG_NOT_DECISIVE'
    elif summaries.get('core',{}).get('n_qualified',0)>0: verdict='CHAIN_CORE_ROBUST_SEEDS__MESH_GAUGE_NOT_CERTIFIED'
    elif summaries.get('temporal',{}).get('n_qualified',0)>0: verdict='CHAIN_TEMPORALLY_CERTIFIED_SEEDS__NO_CORE_ROBUSTNESS'
    elif summaries.get('resolution',{}).get('n_qualified',0)>0: verdict='CHAIN_RESOLUTION_STABLE_SEEDS__NO_TEMPORAL_CERTIFICATION'
    elif summaries.get('early',{}).get('n',0)>0: verdict='CHAIN_EARLY_SCREEN_ONLY'
    else: verdict='CHAIN_FAIL_NO_SEEDS'
    run_kind=_run_kind(cfg)
    if run_kind!='blind_scientific': physics='NOT_APPLICABLE_WORKFLOW_VALIDATION'
    elif verdict=='CHAIN_VALID_LONG_COVERAGE__NO_NEAR_RPO': physics='FAIL'
    elif ok: physics='SUPPORTED_PREDICTIVE_ASSOCIATION_CANDIDATE'
    else: physics='INDETERMINATE'
    numerics='PASS_PARTIAL' if any(summaries.get(k,{}).get('n_qualified',0)>0 for k in ('resolution','temporal','core','mesh_gauge')) else 'INDETERMINATE'
    dump_json(out/'BLIND_CHAIN_SUMMARY.json',{'format':'SST-TREFOIL-DYNAMIC-SEED-CHAIN-3','run_kind':run_kind,'source_diversity_status':diversity,'numerics_verdict':numerics,'physics_verdict':physics,'verdict':verdict,'identity_read':False,**summaries,'mechanism':mech}); return rows


def reveal(out):
    out=Path(out); private=sealed_private_dir(out); identity=load_json(private/'identity_map.json'); manifest=load_json(out/'public_manifest.json'); key=(private/'blind_key.bin').read_bytes()
    if hashlib.sha256(key).hexdigest()!=manifest.get('private_key_commitment_sha256'):
        raise ValueError('BLIND_KEY_COMMITMENT_MISMATCH')
    if object_sha256(identity)!=manifest.get('identity_map_commitment_sha256'):
        raise ValueError('IDENTITY_MAP_COMMITMENT_MISMATCH')
    if set(identity)!={r['candidate_id'] for r in manifest['candidates']}:
        raise ValueError('PUBLIC_IDENTITY_COVERAGE_MISMATCH')
    for i,r in enumerate(manifest['candidates']):
        cid=r['candidate_id']; record=identity[cid]
        expected='C'+hmac.new(key,f"{i}|{record['geom_sha']}".encode(),hashlib.sha256).hexdigest()[:14].upper()
        if cid!=expected or record['geom_sha']!=r['geom_sha'] or geom_sha(np.load(out/'geometries'/f'{cid}.npy'))!=r['geom_sha']:
            raise ValueError('CANDIDATE_GEOMETRY_OR_IDENTITY_MISMATCH')
    result={'identity_commitment_verified':True,'sealed_private_bundle_name':private.name,'revealed_candidates':identity}
    rp=private/'stage25_refine'/'private_refine_map.json'
    if rp.exists():
        refined=load_json(rp); public_refined=load_json(out/'stage25_refine'/'public_manifest.json')
        if object_sha256(refined)!=public_refined.get('private_refine_commitment_sha256'):
            raise ValueError('REFINEMENT_COMMITMENT_MISMATCH')
        if set(refined)!={r['candidate_id'] for r in public_refined['candidates']}:
            raise ValueError('REFINEMENT_IDENTITY_COVERAGE_MISMATCH')
        for r in public_refined['candidates']:
            cid=r['candidate_id']
            if refined[cid]['geom_sha']!=r['geom_sha'] or geom_sha(np.load(out/'geometries'/f'{cid}.npy'))!=r['geom_sha']:
                raise ValueError('REFINEMENT_GEOMETRY_MISMATCH')
        result['revealed_refinements']=refined
    sg=private/'source_generation_audit.json'
    audit=load_json(sg)
    if object_sha256(audit)!=manifest.get('source_audit_commitment_sha256'):
        raise ValueError('SOURCE_AUDIT_COMMITMENT_MISMATCH')
    result['revealed_source_generation_audit']=audit
    evidence=load_json(private/'EVIDENCE_MANIFEST_PRIVATE.json'); public_evidence=load_json(out/'EVIDENCE_MANIFEST.json')
    if object_sha256(evidence)!=public_evidence.get('private_evidence_sha256'):
        raise ValueError('EVIDENCE_COMMITMENT_MISMATCH')
    result['revealed_evidence_manifest']=evidence
    b=out/'BLIND_CHAIN_SUMMARY.json'
    if b.exists(): result['blind_chain']=load_json(b)
    for stage,path in [('early','stage20_early/summary.json'),('refine','stage25_refine/summary.json'),('resolution','stage30_resolution/summary.json'),('temporal','stage32_temporal/summary.json'),('core','stage35_core_robustness/summary.json'),('mesh_gauge','stage37_mesh_gauge/summary.json'),('mesh_closure','stage37b_mesh_closure/summary.json'),('long','stage40_long/summary.json'),('rpo','stage50_rpo_floquet/summary.json'),('mechanism','stage60_finite_core_clock/summary.json')]:
        p=out/path
        if p.exists(): result[stage]=load_json(p)
    dump_json(out/'REVEAL_SUMMARY.json',result); return result

from pathlib import Path
import csv,hashlib,json,math
import numpy as np
from .io import load_json,dump_json
from .geometry import resample_closed,normalize_length,normal_frame,min_nonlocal_vertex_distance,segment_lengths
from .dynamics import simulate
from .metrics import rolling_metrics,recurrence_metrics,shape_distance
from .floquet import projected_floquet
from .causality import causal_gate


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
    if float(row['best_return'])>float(cfg['rpo_loose_return_threshold']): return False,'RETURN_ABOVE_LOOSE_THRESHOLD'
    if not _finite_number(row.get('ds_cv_at_best_return')) or float(row['ds_cv_at_best_return'])>float(cfg.get('rpo_max_ds_cv_at_return',.30)):
        return False,'MESH_QUALITY_BAD_AT_RETURN'
    if not _finite_number(row.get('gap_over_ds_at_best_return')) or float(row['gap_over_ds_at_best_return'])<float(cfg.get('rpo_min_gap_over_ds_at_return',1.0)):
        return False,'CONTACT_MARGIN_BAD_AT_RETURN'
    if not _finite_number(row.get('max_mesh_ratio')): return False,'NO_FINITE_MESH_RATIO'
    if float(row['max_mesh_ratio'])>float(cfg.get('long_max_mesh_ratio',.50)): return False,'MESH_RATIO_GATE_FAIL'
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
        'verdict':'PASS_EARLY_SCREEN' if rows else 'FAIL_NO_CANDIDATES','n':len(rows),'ranking_top_ids':[r['candidate_id'] for r in rows[:int(cfg['resolution_top_k'])]],
        'promoted_ids':promoted,'top_ids':promoted,'promotion_policy':'source_stratified_then_global','source_coverage':_coverage(promoted,groups),
        'ranking_identity_read':False,'pod_dimensionality_is_diagnostic_only':float(cfg.get('score_weights',{}).get('pod',0.0))==0.0,
    }); return rows


def stage_refine(out,cfg):
    out=Path(out); early=list(csv.DictReader(open(out/'stage20_early'/'results.csv',encoding='utf-8'))); groups=_group_map(out)
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
    dump_json(out/'stage25_refine'/'public_manifest.json',{'n_refined':len(public),'parents':parents,'parameters_hidden':True,'candidates':public})
    dump_json(out/'stage25_refine'/'private_refine_map.json',private); _write_csv(out/'stage25_refine'/'results.csv',rows)
    dump_json(out/'stage25_refine'/'summary.json',{
        'n_original':len(early),'n_refined':len(public),'n_combined':len(rows),'parents':parents,'promoted_ids':promoted,'top_ids':promoted,
        'parent_source_coverage':_coverage(parents,groups),'promotion_source_coverage':_coverage(promoted,groups),
        'verdict':'PASS_BLIND_LOCAL_REFINEMENT' if public else 'NO_REFINEMENT_CANDIDATES'}); return rows


def stage_resolution(out,cfg):
    out=Path(out); groups=_group_map(out); rankfile=out/'stage25_refine'/'results.csv' if (out/'stage25_refine'/'results.csv').exists() else out/'stage20_early'/'results.csv'
    rank=list(csv.DictReader(open(rankfile,encoding='utf-8'))); ids=_stratified_ids(rank,int(cfg['resolution_top_k']),groups,int(cfg.get('resolution_min_per_source',1))); rows=[]
    for cid in ids:
        per=[]
        for N in cfg['resolution_n']:
            x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(N)),2*np.pi); tr=simulate(x,cfg,float(cfg['resolution_t_final']),'fixed',False); m=rolling_metrics(tr,x,cfg); per.append((int(N),m))
        sc=np.array([m['score'] for _,m in per]); co=np.array([m['rolling_coherence'] for _,m in per]); au=np.array([m['shape_auc'] for _,m in per])
        qualified=all(m['stop_reason']=='COMPLETED' for _,m in per) and _rel_span(sc)<=float(cfg['resolution_score_rel_span_max']) and _rel_span(co)<=float(cfg['resolution_coherence_rel_span_max']) and _rel_span(au)<=float(cfg['resolution_auc_rel_span_max'])
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'qualified':qualified,'median_score':float(np.median(sc)),'score_rel_span':_rel_span(sc),'coherence_rel_span':_rel_span(co),'auc_rel_span':_rel_span(au),'per_resolution':{str(N):m for N,m in per}})
    rows.sort(key=lambda r:(r['qualified'],r['median_score']),reverse=True); dump_json(out/'stage30_resolution'/'results.json',rows)
    promoted=_stratified_ids(rows,int(cfg.get('temporal_top_k',cfg.get('core_top_k',cfg['long_top_k']))),groups,int(cfg.get('temporal_min_per_source',1)),'qualified')
    dump_json(out/'stage30_resolution'/'summary.json',{'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),'verdict':'PASS_RESOLUTION_QUALIFICATION' if any(r['qualified'] for r in rows) else 'FAIL_NO_RESOLUTION_STABLE_SEED'}); return rows


def stage_temporal(out,cfg):
    """Separate RK4 temporal convergence from the N-ladder spatial qualification."""
    out=Path(out); groups=_group_map(out); rr=load_json(out/'stage30_resolution'/'results.json')
    ids=_stratified_ids(rr,int(cfg.get('temporal_top_k',8)),groups,int(cfg.get('temporal_min_per_source',1)),'qualified'); rows=[]
    basefac=float(cfg.get('dt_factor',.025)); factors=[basefac*float(z) for z in cfg.get('temporal_dt_factor_multipliers',[1.0,.5,.25])]
    if len(factors)!=3: raise ValueError('temporal_dt_factor_multipliers must contain exactly 3 factors')
    N=int(cfg.get('temporal_n',96)); T=float(cfg.get('temporal_t_final',cfg['resolution_t_final']))
    for cid in ids:
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),N),2*np.pi); trs=[]
        for fac in factors: trs.append(simulate(x,cfg,T,'fixed',False,dt_factor_override=fac,store_samples=int(cfg.get('temporal_samples',48))))
        e1=shape_distance(trs[0]['x'][-1],trs[1]['x'][-1],int(cfg.get('cyclic_stride',4))); e2=shape_distance(trs[1]['x'][-1],trs[2]['x'][-1],int(cfg.get('cyclic_stride',4)))
        floor=float(cfg.get('temporal_error_floor',1e-12)); p=float(np.log2(max(e1,floor)/max(e2,floor))) if e1>0 and e2>0 else float('inf')
        abs_tol=float(cfg.get('temporal_abs_shape_tol',5e-4)); converged=all(tr['stop_reason']=='COMPLETED' for tr in trs) and ((e1<=abs_tol and e2<=abs_tol) or (e2<e1 and p>=float(cfg.get('temporal_min_order',3.0))))
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'qualified':bool(converged),'error_h_h2':e1,'error_h2_h4':e2,'observed_order':p,'dt_factors':factors,'actual_dt':[float(tr['dt']) for tr in trs],'stop_reasons':[tr['stop_reason'] for tr in trs]})
    rows.sort(key=lambda r:(r['qualified'],r['observed_order']),reverse=True); dump_json(out/'stage32_temporal'/'results.json',rows)
    promoted=_stratified_ids(rows,int(cfg.get('core_top_k',8)),groups,int(cfg.get('core_min_per_source',1)),'qualified')
    dump_json(out/'stage32_temporal'/'summary.json',{'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),'verdict':'PASS_TEMPORAL_RK4_CERTIFICATION' if promoted else 'FAIL_NO_TEMPORALLY_CERTIFIED_SEED'}); return rows


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
        'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),
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
    dump_json(out/'stage37_mesh_gauge'/'summary.json',{'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':promoted,'source_coverage':_coverage(promoted,groups),'gauge_factors':factors,'verdict':'PASS_MESH_GAUGE_CERTIFIED_SEEDS' if promoted else 'INDETERMINATE_NO_MESH_GAUGE_CERTIFIED_SEED'}); return rows


def stage_long(out,cfg):
    out=Path(out); groups=_group_map(out); gp=out/'stage37_mesh_gauge'/'results.json'; cp=out/'stage35_core_robustness'/'results.json'
    rr=load_json(gp) if gp.exists() else load_json(cp); ids=_stratified_ids(rr,int(cfg['long_top_k']),groups,int(cfg.get('long_min_per_source',1)),'qualified'); rows=[]; (out/'stage40_long'/'trajectories').mkdir(parents=True,exist_ok=True)
    mesh_cert=set(ids) if gp.exists() else set()
    for cid in ids:
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['long_n'])),2*np.pi)
        tr=simulate(x,cfg,float(cfg['long_t_final']),'global_volume',True,store_samples=int(cfg.get('long_samples',240)),max_ds_cv_override=float(cfg.get('long_hard_ds_cv',.45)))
        np.savez_compressed(out/'stage40_long'/'trajectories'/f'{cid}.npz',**tr); rec=recurrence_metrics(tr,x,cfg); m=rolling_metrics(tr,x,cfg)
        rows.append({'candidate_id':cid,'source_group_id':groups.get(cid,'G_UNKNOWN'),'mesh_gauge_certified':cid in mesh_cert,**rec,'long_score':m['score'],'max_mesh_ratio':float(np.max(tr['mesh_ratio'])),'max_ds_cv':float(np.max(tr['ds_cv'])),'min_gap_over_ds':float(np.min(tr['gap_over_ds']))})
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
        'eligibility_counts':_eligibility_counts(rows,cfg),'hard_fail_coverage_satisfied':bool(coverage_ok and full_ok),'verdict':verdict}); return rows


def stage_rpo(out,cfg):
    out=Path(out); rows=[]; long=load_json(out/'stage40_long'/'results.json'); ls=load_json(out/'stage40_long'/'summary.json'); eligible=[]; rejected=[]
    for r in long:
        ok,reason=_rpo_eligibility(r,cfg)
        if ok: eligible.append(r)
        else: rejected.append({'candidate_id':r.get('candidate_id'),'reason':reason})
    pool=eligible[:int(cfg['rpo_top_k'])]
    for r in pool:
        cid=r['candidate_id']; x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['rpo_n'])),2*np.pi); fl=projected_floquet(x,float(r['best_return_time']),cfg)
        passed=bool(fl['quality_completed'] and fl['base_return']<=float(cfg['rpo_return_threshold']) and fl['spectral_radius']<=float(cfg['floquet_rho_max']))
        rows.append({'candidate_id':cid,'period':float(r['best_return_time']),'rpo_floquet_pass':passed,**fl})
    rows.sort(key=lambda r:(r['rpo_floquet_pass'],-r['spectral_radius'] if np.isfinite(r['spectral_radius']) else -1e9,-r['base_return']),reverse=True); dump_json(out/'stage50_rpo_floquet'/'results.json',rows)
    champ=[r['candidate_id'] for r in rows if r['rpo_floquet_pass']][:int(cfg['mechanism_top_k'])]
    if champ: verdict='PASS_PROJECTED_FLOQUET_CANDIDATE'
    elif rows: verdict='FAIL_NO_PROJECTED_STABLE_RPO'
    elif str(ls.get('verdict','')).startswith('INDETERMINATE'): verdict='NOT_RUN_RPO_INDETERMINATE_LONG_NUMERICS'
    elif ls.get('verdict')=='FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE': verdict='NOT_RUN_NO_NEAR_RPO_AFTER_VALID_COVERAGE'
    else: verdict='NOT_RUN_NO_RPO_ELIGIBLE_CANDIDATE'
    dump_json(out/'stage50_rpo_floquet'/'summary.json',{'n_long_rows':len(long),'n_eligible_from_stage40':len(eligible),'n_rejected_from_stage40':len(rejected),'rejected':rejected,'n_tested':len(rows),'n_projected_floquet_pass':len(champ),'champion_ids':champ,'verdict':verdict}); return rows


def stage_mechanism(out,cfg):
    out=Path(out); rpo=load_json(out/'stage50_rpo_floquet'/'results.json'); rows=[]
    for r in [z for z in rpo if z['rpo_floquet_pass']][:int(cfg['mechanism_top_k'])]:
        cid=r['candidate_id']; x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['mechanism_n'])),2*np.pi); T=max(float(cfg.get('mechanism_min_t',1.0)),float(r['period'])*float(cfg.get('mechanism_periods',1.5))); cg=causal_gate(x,T,cfg); rows.append({'candidate_id':cid,'period':r['period'],**cg})
    dump_json(out/'stage60_finite_core_clock'/'results.json',rows); ok=[r for r in rows if r['mechanism_gate_pass']]
    mech={'n_tested':len(rows),'n_mechanism_pass':len(ok),'verdict':'PASS_CANDIDATE_FINITE_CORE_SWIRL_CLOCK_MECHANISM' if ok else ('FAIL_MECHANISM_ON_PROJECTED_RPO' if rows else 'NOT_RUN_NO_PROJECTED_RPO')}; dump_json(out/'stage60_finite_core_clock'/'summary.json',mech)
    summaries={}
    for nm,rel in [('early','stage20_early/summary.json'),('refine','stage25_refine/summary.json'),('resolution','stage30_resolution/summary.json'),('temporal','stage32_temporal/summary.json'),('core','stage35_core_robustness/summary.json'),('mesh_gauge','stage37_mesh_gauge/summary.json'),('long','stage40_long/summary.json'),('rpo','stage50_rpo_floquet/summary.json')]:
        pp=out/rel
        if pp.exists(): summaries[nm]=load_json(pp)
    if ok: verdict='CHAIN_PASS_CANDIDATE_MECHANISM'
    elif rows: verdict='CHAIN_PROJECTED_RPO__MECHANISM_FAIL_OR_INDETERMINATE'
    elif summaries.get('rpo',{}).get('n_projected_floquet_pass',0)>0: verdict='CHAIN_PROJECTED_RPO_ONLY'
    elif summaries.get('long',{}).get('n_near_rpo_candidates',0)>0: verdict='CHAIN_NEAR_RPO_ONLY'
    elif str(summaries.get('long',{}).get('verdict','')).startswith('INDETERMINATE'): verdict='CHAIN_CORE_ROBUST_MESH_CERTIFIED__RPO_NOT_TESTABLE_NUMERICALLY'
    elif summaries.get('long',{}).get('verdict')=='FAIL_NO_NEAR_RPO_WITH_VALID_COVERAGE': verdict='CHAIN_VALID_LONG_COVERAGE__NO_NEAR_RPO'
    elif summaries.get('mesh_gauge',{}).get('n_qualified',0)>0: verdict='CHAIN_MESH_GAUGE_CERTIFIED_SEEDS__LONG_NOT_DECISIVE'
    elif summaries.get('core',{}).get('n_qualified',0)>0: verdict='CHAIN_CORE_ROBUST_SEEDS__MESH_GAUGE_NOT_CERTIFIED'
    elif summaries.get('temporal',{}).get('n_qualified',0)>0: verdict='CHAIN_TEMPORALLY_CERTIFIED_SEEDS__NO_CORE_ROBUSTNESS'
    elif summaries.get('resolution',{}).get('n_qualified',0)>0: verdict='CHAIN_RESOLUTION_STABLE_SEEDS__NO_TEMPORAL_CERTIFICATION'
    elif summaries.get('early',{}).get('n',0)>0: verdict='CHAIN_EARLY_SCREEN_ONLY'
    else: verdict='CHAIN_FAIL_NO_SEEDS'
    dump_json(out/'BLIND_CHAIN_SUMMARY.json',{'format':'SST-TREFOIL-DYNAMIC-SEED-CHAIN-2','verdict':verdict,'identity_read':False,**summaries,'mechanism':mech}); return rows


def reveal(out):
    out=Path(out); identity=load_json(out/'private'/'identity_map.json'); result={'identity_commitment_verified':True,'revealed_candidates':identity}
    rp=out/'stage25_refine'/'private_refine_map.json'
    if rp.exists(): result['revealed_refinements']=load_json(rp)
    sg=out/'private'/'source_generation_audit.json'
    if sg.exists(): result['revealed_source_generation_audit']=load_json(sg)
    b=out/'BLIND_CHAIN_SUMMARY.json'
    if b.exists(): result['blind_chain']=load_json(b)
    for stage,path in [('early','stage20_early/summary.json'),('refine','stage25_refine/summary.json'),('resolution','stage30_resolution/summary.json'),('temporal','stage32_temporal/summary.json'),('core','stage35_core_robustness/summary.json'),('mesh_gauge','stage37_mesh_gauge/summary.json'),('long','stage40_long/summary.json'),('rpo','stage50_rpo_floquet/summary.json'),('mechanism','stage60_finite_core_clock/summary.json')]:
        p=out/path
        if p.exists(): result[stage]=load_json(p)
    dump_json(out/'REVEAL_SUMMARY.json',result); return result

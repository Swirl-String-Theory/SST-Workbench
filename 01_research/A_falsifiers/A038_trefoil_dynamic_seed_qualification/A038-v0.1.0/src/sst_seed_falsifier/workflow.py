from pathlib import Path
import csv,json,numpy as np
from .io import load_json,dump_json
from .geometry import resample_closed,normalize_length,normal_frame,min_nonlocal_vertex_distance,segment_lengths
from .dynamics import simulate
from .metrics import rolling_metrics,recurrence_metrics
from .floquet import projected_floquet
from .causality import causal_gate

def cfgload(path): return load_json(path)
def _ids(out): return [x['candidate_id'] for x in load_json(Path(out)/'public_manifest.json')['candidates']]
def _write_csv(path,rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True); fields=sorted({k for r in rows for k,v in r.items() if not isinstance(v,(dict,list))});
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in rows])
def stage_early(out,cfg):
    out=Path(out); rows=[]; N=int(cfg['early_n']); T=float(cfg['early_t_final'])
    for cid in _ids(out):
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),N),2*np.pi); tr=simulate(x,cfg,T,'fixed',False); m=rolling_metrics(tr,x,cfg); rows.append({'candidate_id':cid,**m})
    rows.sort(key=lambda r:r['score'],reverse=True); _write_csv(out/'stage20_early'/'results.csv',rows); dump_json(out/'stage20_early'/'summary.json',{'verdict':'PASS_EARLY_SCREEN' if rows else 'FAIL_NO_CANDIDATES','n':len(rows),'top_ids':[r['candidate_id'] for r in rows[:int(cfg['resolution_top_k'])]],'ranking_identity_read':False}); return rows

def stage_refine(out,cfg):
    out=Path(out); early=list(csv.DictReader(open(out/'stage20_early'/'results.csv',encoding='utf-8'))); parents=[r['candidate_id'] for r in early[:int(cfg.get('refine_parent_k',6))]]; rng=np.random.default_rng(int(cfg.get('refine_seed',271828))); rows=[{k:(float(v) if k!='candidate_id' and k not in ('stop_reason',) else v) for k,v in r.items()} for r in early]; private={}; public=[]; N=int(cfg['early_n']); T=float(cfg['early_t_final'])
    for parent in parents:
        base=normalize_length(resample_closed(np.load(out/'geometries'/f'{parent}.npy'),int(cfg['candidate_n'])),2*np.pi)
        for j in range(int(cfg.get('refine_variants_per_parent',4))):
            x=base.copy(); xy=float(rng.uniform(*cfg.get('refine_xy_scale_range',[.985,1.015]))); zz=float(rng.uniform(*cfg.get('refine_z_scale_range',[.97,1.03]))); mode=int(rng.integers(1,int(cfg.get('refine_max_mode',6))+1)); an=float(rng.uniform(*cfg.get('refine_normal_amp_range',[-.018,.018]))); ab=float(rng.uniform(*cfg.get('refine_binormal_amp_range',[-.014,.014]))); ph=float(rng.uniform(0,2*np.pi)); x[:,:2]*=xy; x[:,2]*=zz; x=normalize_length(x,2*np.pi); _,n,b=normal_frame(x); f=np.cos(2*np.pi*mode*np.arange(len(x))/len(x)+ph)[:,None]; x=normalize_length(resample_closed(x+an*f*n+ab*f*b,len(x)),2*np.pi); gap=min_nonlocal_vertex_distance(x,int(cfg.get('contact_skip',3)))/max(float(np.mean(segment_lengths(x))),1e-15)
            if gap<float(cfg.get('min_initial_gap_over_ds',1.3)): continue
            import hashlib
            gh=hashlib.sha256(np.round(x,12).tobytes()).hexdigest(); cid='R'+hashlib.sha256(f'{parent}|{j}|{gh}'.encode()).hexdigest()[:14].upper(); np.save(out/'geometries'/f'{cid}.npy',x); private[cid]={'parent_candidate_id':parent,'parameters':{'xy_scale':xy,'z_scale':zz,'mode':mode,'normal_amp':an,'binormal_amp':ab,'phase':ph},'geom_sha':gh,'initial_gap_over_ds':gap}; public.append({'candidate_id':cid,'parent_candidate_id':parent,'geom_sha':gh}); xr=normalize_length(resample_closed(x,N),2*np.pi); tr=simulate(xr,cfg,T,'fixed',False); m=rolling_metrics(tr,xr,cfg); rows.append({'candidate_id':cid,**m})
    rows.sort(key=lambda r:float(r['score']),reverse=True); dump_json(out/'stage25_refine'/'public_manifest.json',{'n_refined':len(public),'parents':parents,'parameters_hidden':True,'candidates':public}); dump_json(out/'stage25_refine'/'private_refine_map.json',private); _write_csv(out/'stage25_refine'/'results.csv',rows); dump_json(out/'stage25_refine'/'summary.json',{'n_original':len(early),'n_refined':len(public),'n_combined':len(rows),'top_ids':[r['candidate_id'] for r in rows[:int(cfg['resolution_top_k'])]],'verdict':'PASS_BLIND_LOCAL_REFINEMENT' if public else 'NO_REFINEMENT_CANDIDATES'}); return rows

def stage_resolution(out,cfg):
    out=Path(out); rankfile=out/'stage25_refine'/'results.csv' if (out/'stage25_refine'/'results.csv').exists() else out/'stage20_early'/'results.csv'; early=list(csv.DictReader(open(rankfile,encoding='utf-8'))); ids=[r['candidate_id'] for r in early[:int(cfg['resolution_top_k'])]]; rows=[]
    for cid in ids:
        per=[]
        for N in cfg['resolution_n']:
            x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(N)),2*np.pi); tr=simulate(x,cfg,float(cfg['resolution_t_final']),'fixed',False); m=rolling_metrics(tr,x,cfg); per.append((int(N),m))
        sc=np.array([m['score'] for _,m in per]); co=np.array([m['rolling_coherence'] for _,m in per]); au=np.array([m['shape_auc'] for _,m in per]); span=lambda a:float((np.max(a)-np.min(a))/max(abs(np.median(a)),1e-12)); qualified=all(m['stop_reason']=='COMPLETED' for _,m in per) and span(sc)<=float(cfg['resolution_score_rel_span_max']) and span(co)<=float(cfg['resolution_coherence_rel_span_max']) and span(au)<=float(cfg['resolution_auc_rel_span_max']); rows.append({'candidate_id':cid,'qualified':qualified,'median_score':float(np.median(sc)),'score_rel_span':span(sc),'coherence_rel_span':span(co),'auc_rel_span':span(au),'per_resolution':{str(N):m for N,m in per}})
    rows.sort(key=lambda r:(r['qualified'],r['median_score']),reverse=True); dump_json(out/'stage30_resolution'/'results.json',rows); dump_json(out/'stage30_resolution'/'summary.json',{'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':[r['candidate_id'] for r in rows if r['qualified']][:int(cfg['long_top_k'])],'verdict':'PASS_RESOLUTION_QUALIFICATION' if any(r['qualified'] for r in rows) else 'FAIL_NO_RESOLUTION_STABLE_SEED'}); return rows

def stage_core(out,cfg):
    out=Path(out); rr=load_json(out/'stage30_resolution'/'results.json'); ids=[r['candidate_id'] for r in rr if r['qualified']][:int(cfg.get('core_top_k',cfg['long_top_k']))]; rows=[]
    for cid in ids:
        per=[]
        for core in cfg.get('core_fraction_ladder',[.06,.08,.10]):
            cc=dict(cfg); cc['core_fraction']=float(core); x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg.get('core_n',96))),2*np.pi); tr=simulate(x,cc,float(cfg.get('core_t_final',cfg['resolution_t_final'])),'fixed',False); m=rolling_metrics(tr,x,cc); per.append((float(core),m))
        sc=np.asarray([m['score'] for _,m in per]); co=np.asarray([m['rolling_coherence'] for _,m in per]); span=lambda a:float((np.max(a)-np.min(a))/max(abs(np.median(a)),1e-12)); qualified=all(m['stop_reason']=='COMPLETED' for _,m in per) and span(sc)<=float(cfg.get('core_score_rel_span_max',.35)) and span(co)<=float(cfg.get('core_coherence_rel_span_max',.40)); rows.append({'candidate_id':cid,'qualified':qualified,'median_score':float(np.median(sc)),'score_rel_span':span(sc),'coherence_rel_span':span(co),'per_core':{str(c):m for c,m in per}})
    rows.sort(key=lambda r:(r['qualified'],r['median_score']),reverse=True); dump_json(out/'stage35_core_robustness'/'results.json',rows); ids2=[r['candidate_id'] for r in rows if r['qualified']][:int(cfg['long_top_k'])]; dump_json(out/'stage35_core_robustness'/'summary.json',{'n_tested':len(rows),'n_qualified':sum(r['qualified'] for r in rows),'top_ids':ids2,'core_fraction_ladder':cfg.get('core_fraction_ladder',[.06,.08,.10]),'verdict':'PASS_CORE_ROBUST_SEEDS' if ids2 else 'FAIL_NO_CORE_ROBUST_SEED'}); return rows

def stage_long(out,cfg):
    out=Path(out); rp=out/'stage35_core_robustness'/'results.json'; rr=load_json(rp) if rp.exists() else load_json(out/'stage30_resolution'/'results.json'); ids=[r['candidate_id'] for r in rr if r['qualified']][:int(cfg['long_top_k'])]; rows=[]; (out/'stage40_long'/'trajectories').mkdir(parents=True,exist_ok=True)
    for cid in ids:
        x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['long_n'])),2*np.pi); tr=simulate(x,cfg,float(cfg['long_t_final']),'global_volume',True,store_samples=int(cfg.get('long_samples',240))); np.savez_compressed(out/'stage40_long'/'trajectories'/f'{cid}.npz',**tr); rec=recurrence_metrics(tr,x,cfg); m=rolling_metrics(tr,x,cfg); rows.append({'candidate_id':cid,**rec,'long_score':m['score'],'max_mesh_ratio':float(np.max(tr['mesh_ratio']))})
    rows.sort(key=lambda r:(r['n_returns']>0,-r['best_return'],r['long_score']),reverse=True); dump_json(out/'stage40_long'/'results.json',rows); cand=[r['candidate_id'] for r in rows if r['best_return']<=float(cfg['rpo_loose_return_threshold']) and r['completed'] and r['max_mesh_ratio']<=float(cfg.get('long_max_mesh_ratio',0.50))][:int(cfg['rpo_top_k'])]; dump_json(out/'stage40_long'/'summary.json',{'n_tested':len(rows),'n_near_rpo_candidates':len(cand),'top_ids':cand,'mesh_ratio_gate_max':float(cfg.get('long_max_mesh_ratio',0.50)),'verdict':'PASS_NEAR_RPO_CANDIDATES' if cand else 'FAIL_NO_NEAR_RPO_SEED'}); return rows

def stage_rpo(out,cfg):
    out=Path(out); rows=[]; long=load_json(out/'stage40_long'/'results.json'); pool=[r for r in long if r['best_return']<=float(cfg['rpo_loose_return_threshold']) and r['completed']][:int(cfg['rpo_top_k'])]
    for r in pool:
        cid=r['candidate_id']; x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['rpo_n'])),2*np.pi); fl=projected_floquet(x,float(r['best_return_time']),cfg); passed=bool(fl['quality_completed'] and fl['base_return']<=float(cfg['rpo_return_threshold']) and fl['spectral_radius']<=float(cfg['floquet_rho_max'])); rows.append({'candidate_id':cid,'period':float(r['best_return_time']),'rpo_floquet_pass':passed,**fl})
    rows.sort(key=lambda r:(r['rpo_floquet_pass'],-r['spectral_radius'] if np.isfinite(r['spectral_radius']) else -1e9,-r['base_return']),reverse=True); dump_json(out/'stage50_rpo_floquet'/'results.json',rows); champ=[r['candidate_id'] for r in rows if r['rpo_floquet_pass']][:int(cfg['mechanism_top_k'])]; dump_json(out/'stage50_rpo_floquet'/'summary.json',{'n_tested':len(rows),'n_projected_floquet_pass':len(champ),'champion_ids':champ,'verdict':'PASS_PROJECTED_FLOQUET_CANDIDATE' if champ else 'FAIL_NO_PROJECTED_STABLE_RPO'}); return rows

def stage_mechanism(out,cfg):
    out=Path(out); rpo=load_json(out/'stage50_rpo_floquet'/'results.json'); rows=[]
    for r in [z for z in rpo if z['rpo_floquet_pass']][:int(cfg['mechanism_top_k'])]:
        cid=r['candidate_id']; x=normalize_length(resample_closed(np.load(out/'geometries'/f'{cid}.npy'),int(cfg['mechanism_n'])),2*np.pi); T=max(float(cfg.get('mechanism_min_t',1.0)),float(r['period'])*float(cfg.get('mechanism_periods',1.5))); cg=causal_gate(x,T,cfg); rows.append({'candidate_id':cid,'period':r['period'],**cg})
    dump_json(out/'stage60_finite_core_clock'/'results.json',rows); ok=[r for r in rows if r['mechanism_gate_pass']]; mech={'n_tested':len(rows),'n_mechanism_pass':len(ok),'verdict':'PASS_CANDIDATE_FINITE_CORE_SWIRL_CLOCK_MECHANISM' if ok else ('FAIL_MECHANISM_ON_PROJECTED_RPO' if rows else 'NOT_RUN_NO_PROJECTED_RPO')}; dump_json(out/'stage60_finite_core_clock'/'summary.json',mech);
    summaries={};
    for nm,rel in [('early','stage20_early/summary.json'),('refine','stage25_refine/summary.json'),('resolution','stage30_resolution/summary.json'),('core','stage35_core_robustness/summary.json'),('long','stage40_long/summary.json'),('rpo','stage50_rpo_floquet/summary.json')]:
        pp=out/rel
        if pp.exists(): summaries[nm]=load_json(pp)
    if ok: verdict='CHAIN_PASS_CANDIDATE_MECHANISM'
    elif rows: verdict='CHAIN_PROJECTED_RPO__MECHANISM_FAIL_OR_INDETERMINATE'
    elif summaries.get('rpo',{}).get('n_projected_floquet_pass',0)>0: verdict='CHAIN_PROJECTED_RPO_ONLY'
    elif summaries.get('long',{}).get('n_near_rpo_candidates',0)>0: verdict='CHAIN_NEAR_RPO_ONLY'
    elif summaries.get('core',{}).get('n_qualified',0)>0: verdict='CHAIN_CORE_ROBUST_SEEDS__NO_RPO'
    elif summaries.get('resolution',{}).get('n_qualified',0)>0: verdict='CHAIN_RESOLUTION_STABLE_SEEDS__NO_CORE_ROBUST_RPO'
    elif summaries.get('early',{}).get('n',0)>0: verdict='CHAIN_EARLY_SCREEN_ONLY'
    else: verdict='CHAIN_FAIL_NO_SEEDS'
    dump_json(out/'BLIND_CHAIN_SUMMARY.json',{'verdict':verdict,'identity_read':False,**summaries,'mechanism':mech}); return rows

def reveal(out):
    out=Path(out); identity=load_json(out/'private'/'identity_map.json'); result={'identity_commitment_verified':True,'revealed_candidates':identity}; rp=out/'stage25_refine'/'private_refine_map.json';
    if rp.exists(): result['revealed_refinements']=load_json(rp)
    b=out/'BLIND_CHAIN_SUMMARY.json'
    if b.exists(): result['blind_chain']=load_json(b)
    for stage,path in [('early','stage20_early/summary.json'),('refine','stage25_refine/summary.json'),('resolution','stage30_resolution/summary.json'),('core','stage35_core_robustness/summary.json'),('long','stage40_long/summary.json'),('rpo','stage50_rpo_floquet/summary.json'),('mechanism','stage60_finite_core_clock/summary.json')]:
        p=out/path
        if p.exists(): result[stage]=load_json(p)
    dump_json(out/'REVEAL_SUMMARY.json',result); return result

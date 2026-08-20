from __future__ import annotations
from pathlib import Path
import csv,json,hashlib,math
import numpy as np
from .model import CurveSet
from .geometry import resample_curves,high_mode_fraction,curve_roughness
from .dynamics import integrate_metrics,restoring_modes
from .native import backend_name,min_nonlocal_segment_distance
from .seal import seal

LOWER_BETTER=['contact_survival_deficit','initial_relative_equilibrium_residual','shape_auc','final_shape_distance','peak_high_mode_fraction','rpo_residual','max_real_growth_positive']

def load_config(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def load_geom(base,rel,n):
    z=np.load(Path(base)/rel);return resample_curves(CurveSet(z['points'],z['offsets']),n)

def initial_observables(cs,cfg):
    return {'edge_cv':float(np.std(np.concatenate([np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1) for c in cs.components()]))/max(np.mean(np.concatenate([np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1) for c in cs.components()])),1e-14)),'curvature_roughness':float(np.mean([curve_roughness(c) for c in cs.components()])),'initial_high_mode_geometry':float(np.mean([high_mode_fraction(c,cfg.get('high_mode_cut_fraction',0.35)) for c in cs.components()])),'initial_gap_core':float(min_nonlocal_segment_distance(cs.points,cs.offsets,int(cfg.get('contact_adjacency',3)))/cfg['core'])}

def analyze_candidate(cs,cfg):
    g=np.ones(cs.n_components,float)
    init=initial_observables(cs,cfg);dyn=integrate_metrics(cs,g,cfg);rest=restoring_modes(cs,g,cfg)
    return {**init,**{k:v for k,v in dyn.items() if k!='history'},'history':dyn['history'],'restoring_fraction':rest['restoring_fraction'],'max_real_growth':rest['max_real_growth'],'max_real_growth_positive':max(float(rest['max_real_growth']),0.0),'restoring':rest,'backend':backend_name()}

def _metric_logratio(a,b,key,floor=1e-12,cap=1e12):
    xa=float(a[key]);xb=float(b[key])
    # A failed/too-short recurrence search can yield +inf.  Treat that as a
    # preregistered very-bad finite score so inf/inf becomes a neutral tie
    # instead of NaN and one finite candidate still beats an infinite one.
    xa = cap if not np.isfinite(xa) else min(max(xa,0.0),cap)
    xb = cap if not np.isfinite(xb) else min(max(xb,0.0),cap)
    return float(np.log((xa+floor)/(xb+floor)))

def pair_decision(a,b,cfg):
    metrics=cfg.get('primary_metrics',LOWER_BETTER)
    vals={m:_metric_logratio(a,b,m,float(cfg.get('metric_floor',1e-12))) for m in metrics}
    med=float(np.median(list(vals.values())));margin=float(cfg.get('pair_tie_log_margin',math.log(1.03)))
    winner='A' if med < -margin else ('B' if med > margin else 'TIE')
    return {'winner_anonymous':winner,'median_log_ratio_A_over_B':med,'metric_log_ratios_A_over_B':vals,'n_metrics_A_better':sum(v<0 for v in vals.values()),'n_metrics_B_better':sum(v>0 for v in vals.values()),'primary_metrics':metrics}

def run_blind(project_root,catalog_dir,outdir,config_path,limit=None):
    project_root=Path(project_root);catalog=Path(catalog_dir);out=Path(outdir);out.mkdir(parents=True,exist_ok=True);cases=out/'cases';cases.mkdir(exist_ok=True)
    cfg=load_config(config_path);rows=list(csv.DictReader(open(catalog/'pairs_public.csv',encoding='utf-8')))
    if limit:rows=rows[:limit]
    if cfg.get('require_native',False) and backend_name()!='cpp-pybind11':raise RuntimeError('Native C++/pybind11 backend required by config')
    pair_rows=[];candidate_cache={}
    for ix,row in enumerate(rows,1):
        results={}
        for side in ('a','b'):
            cid=row[f'candidate_{side}'];geom=row[f'geometry_{side}']
            if cid not in candidate_cache:
                try:
                    cs=load_geom(catalog,geom,int(cfg['resample_n']));r=analyze_candidate(cs,cfg);r['status']='OK'
                except Exception as e:r={'status':'ERROR','error':repr(e),'backend':backend_name()}
                candidate_cache[cid]=r
                (cases/f'{cid}.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8')
            results[side.upper()]=candidate_cache[cid]
        if results['A'].get('status')=='OK' and results['B'].get('status')=='OK':
            dec=pair_decision(results['A'],results['B'],cfg);valid=True
        else:dec={'winner_anonymous':'INDETERMINATE','median_log_ratio_A_over_B':None,'metric_log_ratios_A_over_B':{}};valid=False
        prec={'pair_id':row['pair_id'],'candidate_a':row['candidate_a'],'candidate_b':row['candidate_b'],'valid':valid,**dec}
        pair_rows.append(prec);(cases/f"{row['pair_id']}_pair.json").write_text(json.dumps(prec,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    # Public CSV contains only anonymous pair outcomes.
    with open(out/'blind_pair_results.csv','w',newline='',encoding='utf-8') as f:
        fields=['pair_id','candidate_a','candidate_b','valid','winner_anonymous','median_log_ratio_A_over_B','n_metrics_A_better','n_metrics_B_better']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in pair_rows])
    summary={'campaign_format':'SST-FVI-BLIND-1','backend':backend_name(),'n_pairs':len(pair_rows),'n_valid_pairs':sum(bool(r['valid']) for r in pair_rows),'anonymous_wins':{x:sum(r.get('winner_anonymous')==x for r in pair_rows) for x in ('A','B','TIE','INDETERMINATE')},'source_identity_read':False,'topology_identity_read':False,'sst_target_values_used':False,'blind_config_sha256':hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),'public_catalog_sha256':hashlib.sha256((catalog/'pairs_public.csv').read_bytes()).hexdigest(),'note':'No source-family or topology labels were accessible to this runner.'}
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    sealed=seal(project_root,out,catalog,config_path);summary['sealed_result_tree_sha256']=sealed['result_tree_sha256']
    return summary

from __future__ import annotations
from pathlib import Path
import csv,json,hashlib,math
import numpy as np
from .model import CurveSet
from .dynamics import analyze
from .native import backend_name
from .seal import seal
PRIMARY=['contact_survival_deficit','initial_relative_equilibrium_residual','shape_auc','rpo_residual','max_real_growth_positive']
def load_config(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def load_candidate(catalog,rel):
    z=np.load(Path(catalog)/rel);return CurveSet(z['points'],z['offsets']),np.asarray(z['gammas'],float),int(z['n_carrier_components'])
def logratio(a,b,key,floor=1e-12,cap=1e12):
    xa=float(a[key]);xb=float(b[key]);xa=cap if not np.isfinite(xa) else min(max(xa,0.),cap);xb=cap if not np.isfinite(xb) else min(max(xb,0.),cap);return float(np.log((xa+floor)/(xb+floor)))
def decision(a,b,cfg):
    vals={m:logratio(a,b,m,float(cfg.get('metric_floor',1e-12))) for m in cfg.get('primary_metrics',PRIMARY)};med=float(np.median(list(vals.values())));margin=float(cfg.get('pair_tie_log_margin',math.log(1.03)));winner='A' if med<-margin else ('B' if med>margin else 'TIE');return {'winner_anonymous':winner,'median_log_ratio_A_over_B':med,'metric_log_ratios_A_over_B':vals,'n_metrics_A_better':sum(v<0 for v in vals.values()),'n_metrics_B_better':sum(v>0 for v in vals.values())}
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
                cache[cid]=r;(cases/f'{cid}.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=True)+'\n', encoding='utf-8')
            rr[side.upper()]=cache[cid]
        if rr['A'].get('status')=='OK' and rr['B'].get('status')=='OK':d=decision(rr['A'],rr['B'],cfg);valid=True
        else:d={'winner_anonymous':'INDETERMINATE','median_log_ratio_A_over_B':None,'metric_log_ratios_A_over_B':{}};valid=False
        rec={'pair_id':row['pair_id'],'candidate_a':row['candidate_a'],'candidate_b':row['candidate_b'],'valid':valid,**d};pairs.append(rec);(cases/f"{row['pair_id']}_pair.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n', encoding='utf-8')
    fields=['pair_id','candidate_a','candidate_b','valid','winner_anonymous','median_log_ratio_A_over_B','n_metrics_A_better','n_metrics_B_better']
    with open(out/'blind_pair_results.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r.get(k) for k in fields} for r in pairs])
    summary={'campaign_format':'SST-THREADED-HOLE-BLIND-1','backend':backend_name(),'n_pairs':len(pairs),'n_valid_pairs':sum(bool(x['valid']) for x in pairs),'anonymous_wins':{x:sum(r.get('winner_anonymous')==x for r in pairs) for x in ('A','B','TIE','INDETERMINATE')},'carrier_identity_read':False,'condition_identity_read':False,'gravity_target_used':False,'sst_target_values_used':False,'config_sha256':hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),'note':'Pressure and dynamics are computed anonymously; no carrier family, active/null label, Newton 1/r target, SST constants or mechanical gear ratio is available to scoring.'}
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n', encoding='utf-8');sealed=seal(project_root,out,catalog,config_path);summary['sealed_result_tree_sha256']=sealed['result_tree_sha256'];return summary

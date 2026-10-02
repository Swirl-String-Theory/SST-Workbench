from __future__ import annotations
from pathlib import Path
import csv,json,hashlib,shutil
import numpy as np
from .model import load_candidate
from .analyze import analyze
from .native import backend_name
from .seal import seal

def _decision(a,b,cfg):
    if not a.get('eigenmode_gate_valid') and not b.get('eigenmode_gate_valid'):return {'winner_anonymous':'INDETERMINATE','basis':'MODE_GATE'}
    if a.get('eigenmode_gate_valid') and not b.get('eigenmode_gate_valid'):return {'winner_anonymous':'A','basis':'MODE_GATE'}
    if b.get('eigenmode_gate_valid') and not a.get('eigenmode_gate_valid'):return {'winner_anonymous':'B','basis':'MODE_GATE'}
    ga=float(a['growth_metric']);gb=float(b['growth_metric']);margin=float(cfg.get('growth_tie_fraction',.05));scale=max(.5*(ga+gb),1e-5)
    if ga<gb-margin*scale:return {'winner_anonymous':'A','basis':'CONVERGED_GROWTH','growth_A_over_B':ga/max(gb,1e-12)}
    if gb<ga-margin*scale:return {'winner_anonymous':'B','basis':'CONVERGED_GROWTH','growth_A_over_B':ga/max(gb,1e-12)}
    return {'winner_anonymous':'TIE','basis':'CONVERGED_GROWTH','growth_A_over_B':ga/max(gb,1e-12)}

def run_blind(root,catalog,outdir,config_path,limit=None):
    root=Path(root);catalog=Path(catalog);out=Path(outdir)
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True);cases=out/'cases';cases.mkdir(exist_ok=True);cfg=json.loads(Path(config_path).read_text(encoding='utf-8'))
    if cfg.get('require_native',True) and backend_name()!='cpp-pybind11':raise RuntimeError('native cpp-pybind11 backend required')
    rows=list(csv.DictReader(open(catalog/'pairs_public.csv',encoding='utf-8')));rows=rows[:limit] if limit else rows;cache={};pairs=[]
    for row in rows:
        rr={}
        for side in ('a','b'):
            cid=row[f'candidate_{side}']; rel=row[f'geometry_{side}']
            if cid not in cache:
                try:r=analyze(load_candidate(catalog/rel),cfg);r['backend']=backend_name()
                except Exception as e:r={'status':'ERROR','error':repr(e),'backend':backend_name(),'eigenmode_gate_valid':False}
                cache[cid]=r;(cases/f'{cid}.json').write_text(json.dumps(r,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
            rr[side.upper()]=cache[cid]
        d=_decision(rr['A'],rr['B'],cfg) if rr['A'].get('status')=='OK' and rr['B'].get('status')=='OK' else {'winner_anonymous':'INDETERMINATE','basis':'CASE_ERROR'}
        rec={'pair_id':row['pair_id'],'candidate_a':row['candidate_a'],'candidate_b':row['candidate_b'],**d};pairs.append(rec)
    fields=sorted(set().union(*(x.keys() for x in pairs)))
    with open(out/'blind_pair_results.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(pairs)
    summary={'format':'SST-FINITE-CORE-BLIND-1','backend':backend_name(),'n_pairs':len(pairs),'anonymous_wins':{z:sum(x.get('winner_anonymous')==z for x in pairs) for z in ('A','B','TIE','INDETERMINATE')},'carrier_identity_read':False,'condition_identity_read':False,'target_phase_used':False,'explicit_delay_parameter_used':False,'config_sha256':hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),'note':'Delay is measured from the finite-core dispersion/wavepacket return; no tau_delay or target phase appears in dynamics or scoring.'}
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8'); s=seal(root,out,catalog,config_path);summary['sealed_result_tree_sha256']=s['result_tree_sha256'];return summary

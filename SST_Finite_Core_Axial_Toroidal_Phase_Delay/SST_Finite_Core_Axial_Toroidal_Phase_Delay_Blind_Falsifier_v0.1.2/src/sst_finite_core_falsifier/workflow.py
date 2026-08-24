from __future__ import annotations
from pathlib import Path
import csv,json,hashlib,shutil
import numpy as np
from .model import load_candidate
from .analyze import analyze
from .native import backend_name
from .seal import seal


def _decision(a,b,cfg):
    va=bool(a.get('eigenmode_gate_valid')); vb=bool(b.get('eigenmode_gate_valid'))
    if not va and not vb:return {'winner_anonymous':'INDETERMINATE','basis':'MODE_GATE'}
    if va and not vb:return {'winner_anonymous':'A','basis':'MODE_GATE'}
    if vb and not va:return {'winner_anonymous':'B','basis':'MODE_GATE'}
    ga=float(a['growth_metric']);gb=float(b['growth_metric']);eps=float(cfg.get('neutral_growth_epsilon',1e-8))
    if max(ga,gb)<=eps:return {'winner_anonymous':'TIE','basis':'NEUTRAL_NEUTRAL','growth_A_over_B':1.0}
    margin=float(cfg.get('growth_tie_fraction',.05));scale=max(.5*(ga+gb),eps)
    ratio=(ga+eps)/(gb+eps)
    if ga<gb-margin*scale:return {'winner_anonymous':'A','basis':'CONVERGED_GROWTH','growth_A_over_B':ratio}
    if gb<ga-margin*scale:return {'winner_anonymous':'B','basis':'CONVERGED_GROWTH','growth_A_over_B':ratio}
    return {'winner_anonymous':'TIE','basis':'CONVERGED_GROWTH','growth_A_over_B':ratio}


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
    fields=sorted(set().union(*(x.keys() for x in pairs))) if pairs else ['pair_id']
    with open(out/'blind_pair_results.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(pairs)
    summary={'format':'SST-FINITE-CORE-BLIND-1.2','backend':backend_name(),'n_pairs':len(pairs),'anonymous_wins':{z:sum(x.get('winner_anonymous')==z for x in pairs) for z in ('A','B','TIE','INDETERMINATE')},'carrier_identity_read':False,'condition_identity_read':False,'target_phase_used_in_dynamics':False,'explicit_delay_parameter_used':False,'symmetric_control':True,'config_sha256':hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),'note':'Delay is measured from finite-core dispersion/wavepacket return. v0.1.2 refines return time continuously and phase validity is gated by measured uncertainty; control growth remains the symmetric k0-dk/k0+dk mean.'}
    (out/'blind_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8'); s=seal(root,out,catalog,config_path);summary['sealed_result_tree_sha256']=s['result_tree_sha256'];return summary

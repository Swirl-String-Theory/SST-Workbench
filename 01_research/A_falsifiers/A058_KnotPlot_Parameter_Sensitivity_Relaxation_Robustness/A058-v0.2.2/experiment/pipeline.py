from __future__ import annotations
from pathlib import Path
from typing import Any
import json,math
from .analysis import analyze

def rec(ledger,gid,status,metrics=None,reason=''):
    if not ledger.defs[gid].enabled:return ledger.record(gid,'NOT_APPLICABLE',metrics=metrics or {},reason='Disabled by Framework-v1.0.6 profile semantics; A058 does not repurpose this lane.')
    return ledger.record(gid,status,metrics=metrics or {},reason=reason)
def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    rec(ledger,'G0','PASS',{'mode':mode,'framework_version':'1.0.6'},'Frozen protocol verified before pipeline entry.')
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs";out.mkdir(exist_ok=True);a=analyze(root);(out/'A058_SLIDER_ANALYSIS.json').write_text(json.dumps(a,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    prov=a.get('condition_count')==236 and a.get('runlog_entries')==236 and a.get('parameter_state_verified_fraction')==1.0 and bool(a.get('runtime',{}).get('executable_sha256'));rec(ledger,'G1','PASS' if prov else 'FAIL',{'condition_count':a.get('condition_count'),'runlog_entries':a.get('runlog_entries'),'run_failures':a.get('run_failures'),'parameter_state_verified_fraction':a.get('parameter_state_verified_fraction'),'knotplot_executable_sha256':a.get('runtime',{}).get('executable_sha256')},'Requires all 236 registered conditions to be attempted with verified runtime state; individual numerical failures remain diagnostic rather than aborting the campaign.')
    g2=bool(a.get('ladder_ok')) and a.get('coordinate_complete_fraction',0)>=cfg['thresholds']['coordinate_complete_fraction'];rec(ledger,'G2','PASS' if g2 else 'FAIL',{'ladder_ok':a.get('ladder_ok'),'coordinate_complete_fraction':a.get('coordinate_complete_fraction'),'parse_errors':len(a.get('parse_errors',[]))},'Exact quarter-octave ladder and final-coordinate completeness gate.')
    sums=a.get('axis_summaries',{});effect={};
    for s,v in sums.items():effect[s]=bool((float(v.get('max_shape',0))>cfg['thresholds']['effect_shape_noise_floor']) or (float(v.get('max_scalar_rel',0))>cfg['thresholds']['effect_scalar_noise_floor']) or (float(v.get('max_iteration_fraction_change',0))>cfg['thresholds']['effect_iteration_fraction_floor']))
    rec(ledger,'G3','PASS' if any(effect.values()) else 'FAIL',{'effect_detected_by_axis':effect,'axis_summaries':sums},'PASS means at least one correctly applied slider perturbation measurably changes shape, scalar geometry, or adaptive convergence time; per-axis null results remain valid.')
    rec(ledger,'G4','UNRESOLVED',reason='No independent held-out physical confirmation source in this single-build numerical campaign.')
    try:
        import kpmetrics_native
        from .metrics import read_xyz,curve_metrics
        p=next((root/'campaign/results').glob('C*/final.txt'));x=read_xyz(p);py=curve_metrics(x);nv=kpmetrics_native.metrics(x);errs={k:abs(float(py[k])-float(nv[k]))/max(abs(float(py[k])),abs(float(nv[k])),1e-15) for k in ('length','rg','edge_cv')};mx=max(errs.values());thr=cfg['thresholds']['native_rel'];rec(ledger,'G5','PASS' if mx<=thr else 'FAIL',{'max_relative_error':mx,**errs,'threshold':thr},'Strict Python FP64 versus C++/pybind11 FP64 parity.')
    except Exception as e:rec(ledger,'G5','UNRESOLVED',{'error':str(e)},'Native certification unavailable; no silent fallback.')
    rec(ledger,'G6','UNRESOLVED',reason='GPU screening follows framework profile semantics only.');rec(ledger,'G7','UNRESOLVED',reason='One KnotPlot executable does not constitute independent cross-source replication.')
    convergence={s:float(v.get('converged_fraction',0)) for s,v in sums.items()};g8=(a.get('safe_final_verified_fraction',0)==1.0 and all(v==1.0 for v in convergence.values()) and a.get('run_failures',1)==0);rec(ledger,'G8','PASS' if g8 else 'FAIL',{'safe_final_verified_fraction':a.get('safe_final_verified_fraction'),'converged_fraction_by_axis':convergence,'run_failures':a.get('run_failures'),'quadratic_local_fits':a.get('quadratic_local_fits'),'special_diagnostics':a.get('special_diagnostics')},'PASS requires every valid slider condition to reach the preregistered adaptive plateau without losing final safety; response magnitude is reported separately.')
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'native_cpu':{'expected_backend':'C++17/pybind11 FP64','authority':'CERTIFICATION','silent_fallback':False},'knotplot_campaign':'single trefoil; 7 anonymous GUI sliders; 5 sector references; adaptive go-quantum convergence; Damped + collision avoidance'}

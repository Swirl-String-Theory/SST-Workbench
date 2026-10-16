\
from __future__ import annotations
from pathlib import Path
from typing import Any
import json,math
from .analysis import analyze

def rec(ledger,gid,status,metrics=None,reason=''):
    if not ledger.defs[gid].enabled: return ledger.record(gid,'NOT_APPLICABLE',metrics=metrics or {},reason='Disabled by Framework-v1.0.6 profile semantics; A058 does not repurpose this lane.')
    return ledger.record(gid,status,metrics=metrics or {},reason=reason)
def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    rec(ledger,'G0','PASS',{'mode':mode,'framework_version':'1.0.6'},'Frozen protocol verified before pipeline entry.')
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"; out.mkdir(exist_ok=True)
    a=analyze(root); (out/'A058_STRENGTH_ANALYSIS.json').write_text(json.dumps(a,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    src=(root/'private/historical/build_knot_3.1.kpc').is_file(); prov=a.get('condition_count')==101 and a.get('runlog_entries')==101 and a.get('runlog_nonzero_exits')==0 and bool(a.get('runtime',{}).get('executable_sha256'))
    rec(ledger,'G1','PASS' if src and prov else 'UNRESOLVED',{'historical_trefoil_script':src,'condition_count':a.get('condition_count'),'runlog_entries':a.get('runlog_entries'),'runlog_nonzero_exits':a.get('runlog_nonzero_exits'),'knotplot_executable_sha256':a.get('runtime',{}).get('executable_sha256')},'Requires one identified trefoil source, exact 101-condition campaign, 101 zero-exit runs and pinned executable hash.')
    cfrac=a.get('coordinate_complete_fraction',0.0); g2=bool(a.get('ladder_ok')) and cfrac>=1.0 and not a.get('parse_errors')
    rec(ledger,'G2','PASS' if g2 else 'FAIL',{'ladder_ok':a.get('ladder_ok'),'coordinate_complete_fraction':cfrac,'parseable':a.get('parseable_coordinate_files'),'expected':a.get('expected_coordinate_files')},'Quarter-octave ladder and every coordinate checkpoint must be complete.')
    live=a.get('liveness_extreme_shape',{}); live_vals=[float(v) for v in live.values() if v is not None and math.isfinite(float(v))]; live_ok=bool(live_vals) and max(live_vals)>0.00001
    rec(ledger,'G3','PASS' if live_ok else 'FAIL',{'extreme_shape_by_axis':live,'liveness_threshold':1e-5},'At least one extreme default-relative strength perturbation must produce a measurable shape response.')
    rec(ledger,'G4','UNRESOLVED',reason='No independent held-out physical confirmation source in this single-build numerical campaign.')
    try:
        import kpmetrics_native
        from .metrics import read_xyz,curve_metrics
        p=next((root/'campaign/results').glob('C*/i015000.txt')); x=read_xyz(p); py=curve_metrics(x); nv=kpmetrics_native.metrics(x); errs={k:abs(float(py[k])-float(nv[k]))/max(abs(float(py[k])),abs(float(nv[k])),1e-15) for k in ('length','rg','edge_cv')}; mx=max(errs.values()); rec(ledger,'G5','PASS' if mx<=1e-12 else 'FAIL',{'max_relative_error':mx,**errs,'threshold':1e-12},'Strict Python FP64 versus C++/pybind11 FP64 parity.')
    except Exception as e: rec(ledger,'G5','UNRESOLVED',{'error':str(e)},'Native certification unavailable; no silent fallback.')
    rec(ledger,'G6','UNRESOLVED',reason='GPU screening follows framework profile semantics only.')
    rec(ledger,'G7','UNRESOLVED',reason='One KnotPlot executable does not constitute independent cross-source replication.')
    z=a.get('conditional_zero_equivalence',{}); z_ok=math.isfinite(float(z.get('shape_distance',math.nan))) and float(z['shape_distance'])<=1e-8 and float(z.get('scalar_rel_max',math.inf))<=1e-10
    local=a.get('local',{}); active=['S0','S1']; locvals=[float(local.get(s,{}).get('max_shape',math.inf)) for s in active]; local_ok=all(math.isfinite(v) and v<=0.005 for v in locvals)
    rec(ledger,'G8','PASS' if z_ok and local_ok else 'FAIL',{'conditional_zero_shape':z.get('shape_distance'),'conditional_zero_scalar_rel':z.get('scalar_rel_max'),'zero_shape_threshold':1e-8,'zero_scalar_threshold':1e-10,'active_axis_local_max_shape':{s:local.get(s,{}).get('max_shape') for s in active},'local_shape_threshold':0.005,'quadratic_local_fits':a.get('quadratic_local_fits'),'reciprocal_asymmetry':a.get('reciprocal_asymmetry')},'PASS requires the conditional zero endpoint to equal reset-all baseline and both always-active axes to remain locally robust for one quarter-octave steps; quadratic fits are diagnostic only.')
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'native_cpu':{'expected_backend':'C++17/pybind11 FP64','authority':'CERTIFICATION','silent_fallback':False},'knotplot_campaign':'single trefoil, 101 default-relative strength conditions'}

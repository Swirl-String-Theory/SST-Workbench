from __future__ import annotations
from pathlib import Path
from typing import Any
import json, math, sys
from .analysis import analyze

def _audit(root:Path):
    sys.path.insert(0,str(root))
    from tools.audit_original_scripts import audit
    return audit(root)

def _rec(ledger,gid,status,metrics=None,reason=''):
    d=ledger.defs[gid]
    if not d.enabled:
        return ledger.record(gid,'NOT_APPLICABLE',metrics=metrics or {},reason='Disabled by Framework-v1.0.6 profile semantics; A058 does not repurpose this lane.')
    return ledger.record(gid,status,metrics=metrics or {},reason=reason)

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    _rec(ledger,'G0','PASS',{'mode':mode,'framework_version':'1.0.6'},'Frozen protocol verified before pipeline entry.')
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    out.mkdir(exist_ok=True)

    audit=_audit(root)
    a=analyze(root)
    (out/'A058_RECOVERY_ANALYSIS.json').write_text(json.dumps(a,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')

    # G1: historical canonical provenance remains a clean FAIL; recovered acquisition identity is still recorded.
    provenance_defect=bool(audit.get('implicit_sformat_dependency') or audit.get('runtime_default_dependency'))
    _rec(ledger,'G1','FAIL' if provenance_defect else 'PASS',
         {'historical_file_count':audit.get('file_count'),'implicit_sformat_dependency':audit.get('implicit_sformat_dependency'),
          'runtime_default_dependency':audit.get('runtime_default_dependency'),
          'recovered_runlog_entries':a.get('runlog_entries',0),'recovered_nonzero_exits':a.get('runlog_nonzero_exits',0),
          'knotplot_executable_sha256':a.get('runtime',{}).get('executable_sha256')},
         'FAIL means the historical export procedure is not canonical; it does not invalidate the recovered v0.1.3 coordinate acquisition.')

    complete=a.get('coordinate_complete_fraction',0.0)
    g2_ok=(a.get('available') and complete>=0.999999 and not a.get('parse_errors') and a.get('runlog_nonzero_exits',1)==0)
    _rec(ledger,'G2','PASS' if g2_ok else 'UNRESOLVED',
         {'coordinate_complete_fraction':complete,'parseable':a.get('parseable_coordinate_files',0),
          'expected':a.get('expected_coordinate_files',0),'metrics_csv_nonempty':a.get('metrics_csv_nonempty',0),
          'metrics_csv_present':a.get('metrics_csv_present',0),'runlog_nonzero_exits':a.get('runlog_nonzero_exits',0)},
         'Coordinate checkpoints are authoritative recovery data. Zero-byte KnotPlot data logs are explicitly recorded as missing, not imputed.')

    ns=a.get('negative_control_max_scalar',math.nan); nd=a.get('negative_control_max_shape',math.nan)
    fs=a.get('force_effect_median_shape',math.nan)
    null_ok=(math.isfinite(ns) and math.isfinite(nd) and ns<=1e-10 and nd<=1e-8 and a.get('negative_control_all_final_byte_identical') is True)
    live=(math.isfinite(fs) and fs>1e-6)
    _rec(ledger,'G3','PASS' if null_ok and live else 'FAIL',
         {'dstep_max_coordinate_scalar_rel':ns,'dstep_max_shape':nd,
          'dstep_all_final_byte_identical':a.get('negative_control_all_final_byte_identical'),
          'force_effect_median_shape':fs},
         'The preregistered dstep null must be inert while force ablations must be measurably live.')

    _rec(ledger,'G4','UNRESOLVED',reason='No independent held-out physical confirmation source is part of this recovery analysis.')

    try:
        import kpmetrics_native
        from .metrics import read_xyz,curve_metrics
        p=next((root/'campaign'/'results').glob('C*/i015000.txt'))
        x=read_xyz(p); py=curve_metrics(x); nv=kpmetrics_native.metrics(x)
        errs={k:abs(float(py[k])-float(nv[k]))/max(abs(float(py[k])),abs(float(nv[k])),1e-15) for k in ('length','rg','edge_cv')}
        mx=max(errs.values())
        _rec(ledger,'G5','PASS' if mx<=1e-12 else 'FAIL',{'max_relative_error':mx,**errs,'threshold':1e-12},
             'Strict Python FP64 versus C++/pybind11 FP64 parity on coordinate-derived metrics.')
    except Exception as e:
        _rec(ledger,'G5','UNRESOLVED',{'error':str(e)},'Native certification unavailable; no silent fallback.')

    _rec(ledger,'G6','UNRESOLVED',reason='GPU lane follows framework profile semantics only.')
    _rec(ledger,'G7','UNRESOLVED',reason='Same-software variants do not constitute independent cross-source replication.')

    pf=a.get('plateau_pass_fraction',math.nan)
    rs=a.get('resolution_effect_median_shape',math.nan)
    gp=a.get('generator_pair',{})
    gs=gp.get('shape_distance',math.nan)
    plateau_ok=math.isfinite(pf) and pf>=0.8
    res_ok=math.isfinite(rs) and rs<=0.01
    gen_ok=gp.get('available') and math.isfinite(gs) and gs<=0.01
    # Historical provenance is independently disqualifying; convergence diagnostics show how replacement settings must change.
    g8='PASS' if (not provenance_defect and plateau_ok and res_ok and gen_ok) else 'FAIL'
    _rec(ledger,'G8',g8,
         {'historical_provenance_ok':not provenance_defect,'plateau_pass_fraction':pf,'required_plateau_fraction':0.8,
          'resolution_effect_median_shape':rs,'resolution_shape_threshold':0.01,
          'generator_pair_shape':gs,'generator_shape_threshold':0.01,
          'numeric_effect_median_shape':a.get('numeric_effect_median_shape'),
          'metrics_csv_nonempty':a.get('metrics_csv_nonempty',0)},
         'Canonical qualification requires explicit historical provenance plus preregistered plateau, resolution and generator shape convergence.')

    return {
      'schema':'SST-BACKEND-MANIFEST-2',
      'python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},
      'native_cpu':{'expected_backend':'C++17/pybind11 FP64','authority':'CERTIFICATION','silent_fallback':False},
      'recovery_source':'A058-v0.1.3 completed KnotPlot pilot coordinates',
      'knotplot_data_log_status':'MISSING_ZERO_BYTE'
    }

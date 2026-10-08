from __future__ import annotations
from pathlib import Path
from typing import Any
import json,math,sys
import numpy as np
from .analysis import analyze


def _audit(root:Path):
    sys.path.insert(0,str(root))
    from tools.audit_original_scripts import audit
    return audit(root)


def _status(ledger,gid,status,metrics=None,reason=''):
    ledger.record(gid,status,metrics=metrics or {},reason=reason)


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode,'framework_version':'1.0.6'},reason='Framework protocol verified before pipeline entry.')
    campaign_cfg=json.loads((root/'configs/default.json').read_text(encoding='utf-8'))
    th=campaign_cfg['thresholds']
    audit=_audit(root)
    g1='PASS' if audit['file_count']==50 and not audit['implicit_sformat_dependency'] and not audit['runtime_default_dependency'] else 'FAIL'
    _status(ledger,'G1',g1,
            {'file_count':audit['file_count'],'explicit_ascii_save_all':audit['explicit_ascii_save_all'],'implicit_sformat_dependency':audit['implicit_sformat_dependency'],'explicit_dynamic_command_counts':audit['explicit_dynamic_command_counts'],'runtime_default_dependency':audit['runtime_default_dependency']},
            'Historical scripts are structurally audited. FAIL denotes an export-provenance defect, not geometric invalidity.')
    outroot=root/'build'; outroot.mkdir(exist_ok=True)
    (outroot/'ORIGINAL_SCRIPT_AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    a=analyze(root)
    (outroot/'CAMPAIGN_ANALYSIS.json').write_text(json.dumps(a,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')

    if not a.get('available'):
        for gid,why in [('G2','No generated campaign manifest/results yet.'),('G3','No campaign results for liveness/null control.'),('G4','No campaign results for parameter sensitivity.'),('G5','No coordinate export available for native parity.'),('G6','No baseline checkpoint series available.'),('G7','No resolution/generator comparison available.')]:
            _status(ledger,gid,'UNRESOLVED',reason=why)
    else:
        complete=a['complete_fraction']
        _status(ledger,'G2','PASS' if complete>=0.999 else 'UNRESOLVED',
                {'complete_fraction':complete,'complete_conditions':a['complete_conditions'],'expected_conditions':a['expected_conditions']},
                'Every condition must contain all preregistered CSV and ASCII-coordinate checkpoints.')

        ns=a['negative_control_max_scalar']; nd=a['negative_control_max_shape']
        fs=a['force_effect_median_scalar']; fd=a['force_effect_median_shape']
        if all(math.isfinite(x) for x in (ns,nd,fs,fd)):
            null_ok=ns<=th['negative_control_scalar_rel'] and nd<=th['negative_control_shape']
            live=max(fs,fd)>1e-6
            _status(ledger,'G3','PASS' if null_ok and live else 'FAIL',
                    {'dstep_max_scalar_rel':ns,'dstep_max_shape':nd,'force_effect_median_scalar':fs,'force_effect_median_shape':fd},
                    'dstep is the preregistered null control; force ablations establish parameter liveness.')
        else:
            _status(ledger,'G3','UNRESOLVED',reason='Insufficient dstep/force-ablation scalar or coordinate outputs.')

        nscalar=a['numeric_effect_median_scalar']; nshape=a['numeric_effect_median_shape']
        if math.isfinite(nscalar) and math.isfinite(nshape):
            ok=nscalar<=th['material_scalar_rel'] and nshape<=th['material_shape']
            _status(ledger,'G4','PASS' if ok else 'FAIL',
                    {'numeric_effect_median_scalar':nscalar,'numeric_effect_median_shape':nshape,
                     'scalar_threshold':th['material_scalar_rel'],'shape_threshold':th['material_shape']},
                    'Accepted numerical controls must be small in both scalar observables and normalized coordinate geometry.')
        else:
            _status(ledger,'G4','UNRESOLVED',reason='Insufficient numeric-factor scalar or coordinate outputs.')

        # Native parity: never silently emulate the C++ certification lane.
        try:
            import kpmetrics_native
            from .metrics import read_xyz,curve_metrics
            coord=next((root/'campaign'/'results').glob('C*/i015000.txt'))
            x=read_xyz(coord); py=curve_metrics(x); nv=kpmetrics_native.metrics(x)
            errs={k:abs(py[k]-float(nv[k]))/max(abs(py[k]),abs(float(nv[k])),1e-15) for k in ('length','rg','edge_cv')}
            mx=max(errs.values())
            _status(ledger,'G5','PASS' if mx<=th['native_rel'] else 'FAIL',
                    {'max_relative_error':mx,**errs,'threshold':th['native_rel']},
                    'Strict Python FP64 vs C++/pybind11 FP64 metric parity.')
        except StopIteration:
            _status(ledger,'G5','UNRESOLVED',reason='No final coordinate export available for native parity.')
        except Exception as e:
            _status(ledger,'G5','UNRESOLVED',metrics={'error':str(e)},reason='Native module unavailable or certification could not execute; no fallback is accepted.')

        pf=a['plateau_pass_fraction']
        if math.isfinite(pf):
            _status(ledger,'G6','PASS' if pf>=th['required_plateau_fraction'] else 'FAIL',
                    {'plateau_pass_fraction':pf,'required_fraction':th['required_plateau_fraction'],'per_topology':a['plateaus']},
                    'Each qualified baseline must satisfy both scalar and coordinate-shape 10k-to-15k plateau limits.')
        else:
            _status(ledger,'G6','UNRESOLVED',reason='Insufficient baseline coordinate/checkpoint series.')

        rs=a['resolution_effect_median_scalar']; rd=a['resolution_effect_median_shape']; gp=a['generator_pair']
        gen_ok=(gp.get('available') and math.isfinite(gp.get('scalar_rel',math.nan)) and math.isfinite(gp.get('shape_distance',math.nan))
                and gp['scalar_rel']<=th['generator_scalar_rel'] and gp['shape_distance']<=th['generator_shape'])
        if math.isfinite(rs) and math.isfinite(rd) and gp.get('available'):
            res_ok=rs<=th['resolution_scalar_rel'] and rd<=th['resolution_shape']
            _status(ledger,'G7','PASS' if res_ok and gen_ok else 'FAIL',
                    {'resolution_effect_median_scalar':rs,'resolution_effect_median_shape':rd,
                     'resolution_scalar_threshold':th['resolution_scalar_rel'],'resolution_shape_threshold':th['resolution_shape'],
                     'generator_pair':gp,'generator_scalar_threshold':th['generator_scalar_rel'],'generator_shape_threshold':th['generator_shape']},
                    'Resolution robustness and the preregistered same-topology dual-generator convergence must both pass.')
        else:
            _status(ledger,'G7','UNRESOLVED',reason='Insufficient resolution or dual-generator outputs.')

    # Provenance alone is sufficient to reject the historical protocol as *canonical*; diagnostics still continue.
    if audit['implicit_sformat_dependency'] or audit['runtime_default_dependency']:
        reasons=[]
        if audit['implicit_sformat_dependency']: reasons.append('IMPLICIT_SFORMAT_DEPENDENCY')
        if audit['runtime_default_dependency']: reasons.append('UNPINNED_RELAXATION_DEFAULTS')
        _status(ledger,'G8','FAIL',
                {'new_canonical_export_generation_required':True,'reason_codes':reasons},
                'The historical protocol depends on implicit export format and/or unrecorded relaxation defaults; it cannot be promoted as a canonical production source. G3-G7 determine the replacement settings.')
    else:
        _status(ledger,'G8','UNRESOLVED',metrics={'new_canonical_export_generation_required':False},
                reason='Provenance is acceptable; final production qualification requires completed robustness gates.')

    return {
        'schema':'SST-BACKEND-MANIFEST-2',
        'python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},
        'native_cpu':{'expected_backend':'C++17/pybind11 FP64','authority':'CERTIFICATION','silent_fallback':False},
        'diagnostic_continuation':True
    }

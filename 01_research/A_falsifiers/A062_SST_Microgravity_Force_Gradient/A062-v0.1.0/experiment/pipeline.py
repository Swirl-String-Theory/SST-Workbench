"""A062 framework-v1.0.7 science adapter: no monkeypatch to framework internals.

This adapter records FRAMEWORK semantic G0--G8 and delegates scientific
computation to the preregistered, explicit standalone engine. The generated
local ledger is strictly labelled NOT the canonical framework gate ledger.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from microgravity.runner import run as run_science


def run_scientific_pipeline(root:Path, cfg:dict[str,Any], ledger, mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'framework':'v1.0.7','mode':mode},
      reason='The canonical framework checked its own frozen bundle before pipeline entry.')
    # Published summaries are public calibration benchmarks, not legitimate held-out targets.
    source=root/'inputs'/'article_public_summary.json'
    ledger.record('G1','PASS' if source.is_file() else 'FAIL',
      metrics={'source':'Zhu2026 public rounded article summary','measured_G_independently':False},
      reason='Public rounded source is present; independent source-blind proof is not claimed.')
    # Deliberately independent scientific gates. A failed mass closure cannot suppress
    # the far-field slope, C++ parity or readiness gates.
    results=run_science(mode if mode in ('BASIC','FULL','CERTIFY') else 'FULL')
    st=results['gate_status']
    # No inference is hidden in the report. Copy the same numeric metrics into the
    # framework-owned report folder before frozen framework report rendering.
    import shutil
    science_out=root/('A062_SST_Microgravity_Force_Gradient_v0.1.0-outputs')
    framework_out=root/(cfg['project']['name']+'_'+cfg['project']['version']+'-outputs')
    metric_target=framework_out/'report'/'LOCAL_METRICS.tex'
    metric_target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(science_out/'LOCAL_METRICS.tex',metric_target)
    ledger.record('G2',st['S2'],metrics={'maximum_relative_refinement_error':max(
      results['sst_candidate']['pressure_force'][a]['max_rel_refinement_change'] for a in ('x','z'))},
      reason='Numerical midpoint quadrature qualification (Python FP64).',
      actual_backend='python-numpy-fp64',authority='REFERENCE')
    ledger.record('G3','FAIL' if ('FAIL' in [st['S3'],st['S4']]) else 'PASS',
      metrics={'mass_closure_ratio':results['sst_candidate']['mass_ratio'],
       'equatorial_far_field_exponent':results['sst_candidate']['pressure_force']['x']['farfield_slope'],
       'axial_far_field_exponent':results['sst_candidate']['pressure_force']['z']['farfield_slope']},
      reason='Restricted Gaussian closure, NOT full SST, fails energy mass and far-field scaling.',
      actual_backend='python-numpy-fp64',authority='REFERENCE')
    # G4/G5/G6/G7 framework enablement follows frozen profile mapping.
    for gid,reason in [
       ('G4','Independent withheld separation sweeps are absent.'),
       ('G5','Strict native C++ FP64 parity against Python integration.'),
       ('G6','Sycl GPU optional screening is not part of this CPU profile.'),
       ('G7','Only one experimental source family is supplied.'),
       ('G8','PKLSA geometries and derived test-body momentum coupling not supplied.')]:
        if gid not in ledger.defs: continue
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by canonical selected profile.')
        elif gid=='G5':
            status=st['S5']
            ledger.record(gid,status,metrics={'actual_native_compiler':results['native']['compiler'],
                'native_cpp_fp64_max_relative_error':results['native'].get('max_relative_error')},
                reason=reason,requested_backend='cpp-fp64',
                actual_backend='cpp-fp64' if results['native']['ran'] else 'unavailable',
                authority='CERTIFICATION' if status=='PASS' else 'NONE')
        else:
            ledger.record(gid,'UNRESOLVED',reason=reason)
    return {'schema':'SST-BACKEND-MANIFEST-2',
            'python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},
            'cpp_fp64':results['native'],
            'sycl_gpu':{'requested':False,'ran':False,'authority':'SCREENING_ONLY'},
            'scientific_claim':'restricted Gaussian Euler pressure source only; not full SST'}

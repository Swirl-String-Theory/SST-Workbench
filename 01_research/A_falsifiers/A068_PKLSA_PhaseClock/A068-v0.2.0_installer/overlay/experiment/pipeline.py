"""A068 v0.2.0 | scientific overlay on SST Falsifier Framework v1.0.8.
Scientific G3+ remain explicitly open. No relabeling of A064 snapshots as a vortex clock.
The official framework supplies run IDs, frozen protocol, ledger, archiving and reports.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any
from .phaseclock import demo, audit_A064, run_npz

EXPECTED = {
    'PREFLIGHT_RESULTS.json':'eb2c099968b5ab2b33abb9ce855b0a4c77f58cd0f0137ccabdaf917146574730',
    'PREFLIGHT_WITH_A064.json':'7f6f865af5e6c459462bcc88780415a1d7257e96558cc47cae9ac6bd723f6902',
    'A064-v0.3.0_results.json':'3c1469cfddeafbc69c368a779072144119769d5ee9276a92064c803fbc6af3c1',
}

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_sources(root: Path) -> dict:
    result={}
    for name, expected in EXPECTED.items():
        path=root/'data'/name
        result[name]={'exists':path.is_file(),'sha256_matches':path.is_file() and _sha(path)==expected,
                      'expected_sha256':expected,'actual_sha256':_sha(path) if path.is_file() else None}
    return {'all_valid':all(r['sha256_matches'] for r in result.values()),'files':result}


def check_method(root: Path) -> dict:
    original=json.loads((root/'data/PREFLIGHT_RESULTS.json').read_text(encoding='utf-8'))
    earlier=json.loads((root/'data/PREFLIGHT_WITH_A064.json').read_text(encoding='utf-8'))
    actual=demo()
    pos=actual['positive_two_shape_signals']
    negrot=actual['negative_rigid_rotation_shape_invariants']
    negbeat=actual['negative_beating']
    checks={
        'original_is_unblinded_method':original.get('test_type')=='UNBLINDED_METHOD_DEVELOPMENT_NOT_PHYSICAL_VALIDATION',
        'original_demo_reproducible':all(original['demo'][k]['G3_phase_reproducibility']==actual[k]['G3_phase_reproducibility']
               for k in ('positive_two_shape_signals','negative_rigid_rotation_shape_invariants','negative_beating')),
        'positive_numeric_clock_recovered':pos['G3_phase_reproducibility']=='PASS_NUMERICAL_ONLY'
              and abs(pos['q1']['frequency']-0.25)<1e-5
              and abs(pos['q2']['frequency']-0.25)<1e-5,
        'rigid_rotating_shape_rejected':negrot['q1']['status']=='NO_CLOCK'
              and negrot['q2']['status']=='NO_CLOCK',
        'beating_rejected':negbeat['G3_phase_reproducibility']=='SCREEN_FAIL',
    }
    audit=audit_A064(root/'data/A064-v0.3.0_results.json')
    source_audit=earlier.get('existing_A064_source_audit',{})
    checks.update({
        'A064_identity_matches':audit['sha256']==source_audit.get('sha256'),
        'A064_no_physical_clock_claim':audit['overall']=='NO_PHYSICAL_CLOCK_INFERENCE_POSSIBLE',
        'A064_periodic_background_not_certified':audit['G1_periodic_relative_equilibrium']=='UNRESOLVED',
    })
    return {'pass_method_control':all(checks.values()),'checks':checks,
            'synthetic_omega':pos['q1']['omega'],
            'synthetic_frequency':pos['q1']['frequency'],
            'a064_audit':audit, 'interpretation':'SYNTHETIC_METHOD_VALIDATION_ONLY'}


def analyze_optional_field(root: Path) -> dict:
    """Development-only field screen, not a route to physical G3 PASS."""
    p=root/'data/PKLSA_DYNAMICS.npz'
    if not p.is_file():
        return {'status':'NOT_PROVIDED','reason':'No time-resolved 3D velocity field supplied; A064 is not that dataset.'}
    try:
        r=run_npz(p)
    except Exception as exc:
        return {'status':'INVALID_INPUT','reason':str(exc)}
    return {'status':'METHOD_DIAGNOSTIC_ONLY','screen':r,
            'reason':'A field screen cannot certify a material vortex, relative periodic orbit, operator holdout, convergence or provider independence.'}


def run_scientific_pipeline(root: Path, cfg: dict[str,Any], ledger, mode: str) -> dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode},
                 reason='Framework verified the pinned v1.0.8 protocol before pipeline entry.')
    source=check_sources(root)
    ledger.record('G1','PASS' if source['all_valid'] else 'FAIL',
                 metrics={'verified_input_files':sum(r['sha256_matches'] for r in source['files'].values()),
                          'required_input_files':len(source['files'])},
                 reason='Input hashes and source types match; NOT a PKLSA dynamics qualification.'
                       if source['all_valid'] else 'Missing or modified immutable audit evidence; fail closed.')
    if ledger.status('G1')=='PASS':
        method=check_method(root)
        ledger.record('G2','PASS' if method['pass_method_control'] else 'FAIL',
                      metrics={'passed_controls':sum(method['checks'].values()),
                               'total_controls':len(method['checks'])},
                      reason='Synthetic preflight reproduced with exact input provenance; no physical claim.'
                            if method['pass_method_control'] else 'Preflight controls not reproduced.')
    else:
        method={'status':'NOT_RUN_PREREQUISITE'}
        ledger.skip_due_prerequisite('G2')
    if ledger.status('G2')=='PASS':
        field=analyze_optional_field(root)
        ledger.record('G3','UNRESOLVED',metrics={'eligible_real_pklsa_clocks':0},
                     reason='No source-native material-bounded time-evolving PKLSA vortex with independent clock and orbit qualification. '
                     'Optional full-field analysis is method screening only.')
    else:
        field={'status':'NOT_RUN_PREREQUISITE'}
        ledger.skip_due_prerequisite('G3')
    for gid in ('G4','G5','G6','G7','G8'):
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Framework profile disabled this gate; not a scientific PASS.')
        else:
            ledger.skip_due_prerequisite(gid,reason='G3 real-PKLSA clock qualification has not passed.')
    # G9 is automatically DEFERRED by the official framework run_mode.
    return {
        'schema':'SST-BACKEND-MANIFEST-2',
        'project':'A068_PKLSA_PhaseClock_v0.2.0',
        'requested_framework':'SST_Falsifier_Framework_v1.0.8',
        'authority':'METHOD_DEVELOPMENT_ONLY',
        'actual_backend':'python-numpy-fp64',
        'precision':'float64',
        'source_hash_status':source,
        'preflight_result':method,
        'optional_3d_field':field,
        'physical_clock_status':'UNRESOLVED',
        'no_native_cpp_or_sycl_claim':True,
        'no_independent_pklsa_provider_claim':True,
    }

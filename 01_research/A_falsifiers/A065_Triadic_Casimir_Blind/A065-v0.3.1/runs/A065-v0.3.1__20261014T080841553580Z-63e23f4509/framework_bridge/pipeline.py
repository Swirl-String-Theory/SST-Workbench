"""Application plug-in for *unchanged* canonical SST framework v1.0.7.

The instance gate DAG is versioned and frozen *before* FREEZE. G5 is a
strict C++ kernel-parity gate that does NOT certify full coupled dynamics.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from triadic.runner import run_d01,run_d02,run_d03
from triadic.security import verify_all
from triadic.provider_manifest import verify as verify_provider
from triadic.native_qualification import evaluate


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode,'framework_contract':'1.0.7'},
                  reason='Frozen protocol verified by canonical framework.')
    seals=verify_all(root)
    provider=verify_provider(root)
    ledger.record('G1','PASS',metrics={'sealed_datasets':3,'upstream_geometry_providers':1+
                  int(provider['status']=='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY'),
                  'provider_status':provider['status'],'provider_manifest_sha256':provider['manifest_sha256'],
                  'seals':seals},reason='Source bytes and single shared provider manifest verified; dynamic independence not implied.')
    results=[run_d01(root),run_d02(root),run_d03(root)]
    gates=[g for r in results for g in r['gates']]
    fails=[g['gate'] for g in gates if g['status']!='PASS']
    dyn=results[0]['filament_dynamics']
    ledger.record('G2','PASS' if not fails else 'FAIL',metrics={
        'reference_gates_pass':len(gates)-len(fails),'reference_gates_total':len(gates),
        'legacy_75_150_relative':dyn['spatial_75_150_relative_displacement'],
        'new_150_300_relative':dyn['spatial_150_300_relative_displacement'],
        'failed_reference_gates':fails,'pklsa_points':300},
        reason='75/150/300 fixed-core validation. Retain historical FAIL; no tolerance changes.')
    # G5 is deliberately independent from scientific G2 so a spatial FAIL does
    # not suppress useful CPU parity evidence. The question is restricted to
    # the executed C++17 velocity kernel, not an unexecuted native RK4 chain.
    if ledger.defs['G5'].enabled:
        native=evaluate(root)
        if native['status']=='PASS':
            ledger.record('G5','PASS',metrics=native,
                          requested_backend='cpp17-fp64',actual_backend='cpp17-serial-fp64',
                          authority='KERNEL_ONLY',reason='Actual C++17 kernel executed. Full scientific/backend certification remains open.')
        else:
            ledger.record('G5','UNRESOLVED',metrics=native,
                          requested_backend='cpp17-fp64',actual_backend=None,authority='KERNEL_ONLY',
                          reason='C++ kernel parity unavailable/failed; never silently substitute Python.')
    else:ledger.record('G5','NOT_APPLICABLE',reason='Native CPU profile disabled')
    if ledger.status('G2')!='PASS':
        ledger.skip_due_prerequisite('G3',reason='Spatial reference gate G2 FAIL; physical discovery not run')
    else:
        ledger.record('G3','UNRESOLVED',metrics={'qualified_time_dependent_euler_providers':0,
            'raw_hash_verified_fremlin':provider['status']=='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY'},
            reason='No independent physical force prediction, complete Euler dynamics or microscopic material response.')
    ledger.skip_due_prerequisite('G4',reason='G3 physical discovery not PASS')
    for gid in ('G6','G7'):
        if gid in ledger.defs:
            if not ledger.defs[gid].enabled:
                ledger.record(gid,'NOT_APPLICABLE',reason='Disabled for CPU-only profile')
            else:
                ledger.skip_due_prerequisite(gid,reason='Not certified for this profile')
    if 'G8' in ledger.defs:
        ledger.skip_due_prerequisite('G8',reason='Physical G3 not PASS; G8 has no dependency on disabled G7')
    return {'schema':'SST-BACKEND-MANIFEST-2',
            'python_reference':{'actual_backend':'python-stdlib-binary64','precision':'float64','authority':'REFERENCE'},
            'native_kernel':native if ledger.defs['G5'].enabled else {'status':'NOT_APPLICABLE'},
            'scope':'Kernel-only native gate; complete coupled physical validation withheld',
            'provider_manifest_sha256':provider['manifest_sha256'],
            'provider_status':provider['status'],
            'pklsa_geometry':results[0]['pklsa']['source']['raw_sha256'],
            'sealed_source_groups':list(seals), 'physical_force_status':'UNRESOLVED'}

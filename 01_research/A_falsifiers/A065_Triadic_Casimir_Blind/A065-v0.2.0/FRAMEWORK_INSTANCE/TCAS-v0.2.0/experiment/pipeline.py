"""Scientific application for the genuine frozen v1.0.7 framework.

Self-contained datasets are copied into the generated framework instance. The
framework owns protocol freeze, gate ledger, reveal policy and output manifests.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from triadic.runner import run_d01,run_d02,run_d03
from triadic.security import verify_all


def run_scientific_pipeline(root: Path, cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode,'framework_contract':'1.0.7'},reason='Frozen preregistration verified by official framework.')
    seals=verify_all(root)
    ledger.record('G1','PASS',metrics={'sealed_datasets':3,'pklsa_upstream_provider_count':1,'seals':seals},
                  reason='Raw datasets and seals intact; source completeness only, not independent physical replication.')
    results=[run_d01(root),run_d02(root),run_d03(root)]
    gates=[g for r in results for g in r['gates']]
    ok=all(g['status']=='PASS' for g in gates)
    ledger.record('G2','PASS' if ok else 'FAIL',metrics={'reference_gates_pass':sum(g['status']=='PASS' for g in gates),'reference_gates_total':len(gates),'pklsa_points':results[0]['pklsa']['stats']['points']},reason='Independent analytic and geometry-based numerical controls only.')
    ledger.record('G3','UNRESOLVED',metrics={'independent_physical_providers':0,'geometry_provider_count':1},
                  reason='No independently derived time-dependent Euler+link physical Casimir prediction; no blind target claim.')
    for gid in ('G4','G5','G6','G7','G8'):
        if gid not in ledger.defs:continue
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Backend/source extension disabled in minimal profile.')
        else:
            ledger.skip_due_prerequisite(gid,reason='Physical discovery G3 is UNRESOLVED.')
    return {'schema':'SST-BACKEND-MANIFEST-2',
            'python_reference':{'actual_backend':'python-stdlib-binary64','precision':'float64','authority':'REFERENCE'},
            'note':'Reference-only geometry pilot. Native C++ backend not executed by this framework profile.',
            'pklsa_geometry':results[0]['pklsa']['source']['raw_sha256'],
            'sealed_source_groups':list(seals), 'physical_force_status':'UNRESOLVED'}

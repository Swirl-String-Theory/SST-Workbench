from __future__ import annotations
from pathlib import Path
import json

def audit_snapshot(snapshot_path):
    d=json.loads(Path(snapshot_path).read_text(encoding='utf-8'))
    s=d['sources']
    blockers=[]
    a048=s.get('A048_euler',{}).get('extract',{})
    if not a048.get('material_phase_run_executed',False): blockers.append('A048_NO_MATERIAL_PHASE_OBSERVABLE')
    if a048.get('cells_per_sigma',0)<4: blockers.append('A048_CORE_UNRESOLVED')
    a050=s.get('A050',{}).get('extract',{})
    if not a050.get('modal_transfer_pass',False): blockers.append('A050_REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED')
    a038=s.get('A038',{}).get('extract',{})
    if 'INDETERMINATE' in str(a038.get('long','')): blockers.append('A038_LONG_RPO_INDETERMINATE')
    a031=s.get('A031',{}).get('extract',{})
    if 'NO_CERTIFIED_RPO' in str(a031): blockers.append('A031_NO_CERTIFIED_RPO')
    return {'schema':'A051_UPSTREAM_READINESS_1.0','physical_ready':len(blockers)==0,'status':'READY' if not blockers else 'INDETERMINATE','blockers':blockers,'note':'Blockers are inherited evidence constraints, not A051 FAIL results.'}

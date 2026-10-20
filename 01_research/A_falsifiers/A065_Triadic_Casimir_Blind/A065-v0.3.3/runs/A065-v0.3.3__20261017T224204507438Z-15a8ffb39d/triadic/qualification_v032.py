"""Write-once preregistered spatial and independent-provider qualifications."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from .security import verify_all,canon
from .provider_manifest import verify as verify_provider
from .spatial_v032 import diagnose
from .independent_fremlin_v032 import verify as fremlin

def run(root):
    root=Path(root)
    seals=verify_all(root)
    manifest=verify_provider(root)
    scan=diagnose(root)
    lane=fremlin(root)
    payload={'schema':'A065-QUALIFICATION-V032-1','release':'v0.3.2',
       'precommit_sha256':hashlib.sha256((root/'preregistration/QUALIFICATION_V032.json').read_bytes()).hexdigest(),
       'original_seals':seals,'source_provider_manifest_sha256':manifest['manifest_sha256'],
       'spatial':scan,'independent_dynamic_simulation':lane,
       'qualification':{
          'historical_fail_retained':scan['status_full_historical'],
          'refined_discretization':scan['status_refined_spatial'],
          'time_discretization':scan['status_temporal'],
          'fremlin_dynamic_lane':lane['status'],
          'physical_euler':'UNRESOLVED', 'physical_casimir':'UNRESOLVED',
          'second_independent_physical_provider':'UNRESOLVED',
       }}
    payload['payload_sha256']=hashlib.sha256(canon(payload)).hexdigest()
    dest=root/'outputs/QUALIFICATION_V032.json'; dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as fh:fh.write(canon(payload))
    return payload

"""Independent upstream-provider checker. Never treats provider names as proof.

E010 A006 Fremlin 3_1 raw source is not bundled; registration is not observation.
On a Workbench checkout, check exact byte hash at source_root relative location.
"""
from __future__ import annotations
import json,hashlib,math,os
from pathlib import Path
from .pklsa import load_geometry

def check(root, raw_override=None):
    root=Path(root)
    reg=json.loads((root/'data'/'D01_EULER'/'pklsa'/'fremlin_provider_contract.json').read_text())
    raw=Path(raw_override) if raw_override else Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))/reg['workbench_relative_path']
    result={'schema':'A065-INDEPENDENT-PROVIDER-1','provider':reg['provider'], 'carrier_id':reg['carrier_id'],
            'source_family':reg['source_family'],'independence_group':reg['independence_group'],
            'expected_raw_sha256':reg['expected_raw_sha256'],'requested_path':str(raw),'status':'UNRESOLVED_SOURCE_MISSING'}
    if not raw.is_file():return result
    blob=raw.read_bytes();hash_=hashlib.sha256(blob).hexdigest();result['observed_raw_sha256']=hash_
    if hash_!=reg['expected_raw_sha256']:
        result['status']='FAIL_RAW_HASH_MISMATCH';return result
    try:
        # E010's short format must be parsed by a native reader, never silently read as xyz
        rows=load_geometry(raw)
        result['point_count']=len(rows)
        result['bounding_box']=[[min(p[d] for p in rows),max(p[d] for p in rows)] for d in range(3)]
    except Exception as exc:
        result['status']='UNRESOLVED_PARSER_REQUIREMENT';result['parser_error']=type(exc).__name__+': '+str(exc)
        return result
    result['status']='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY'
    result['physics_qualification']='UNRESOLVED_NO_TIME_EVOLUTION_OR_MATERIAL_RESPONSE'
    return result

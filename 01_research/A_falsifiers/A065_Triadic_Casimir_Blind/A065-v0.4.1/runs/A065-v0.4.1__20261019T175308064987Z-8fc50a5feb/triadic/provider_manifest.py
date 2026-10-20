"""Single canonical per-run Fremlin provider resolution.

No provider is accepted by label. Absolute source path and raw SHA-256 are
committed once and verified again by portable and official framework runs.
This verifies GEOMETRY ONLY; it does not certify dynamics or Casimir physics.
"""
from __future__ import annotations
import hashlib,json,os,pathlib
from .pklsa import load_geometry
from .security import canon,readjson

NAME='PROVIDER_MANIFEST.json'

def digest(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def location(root,override=None):
    root=pathlib.Path(root)
    r=readjson(root/'data/D01_EULER/pklsa/fremlin_provider_contract.json')
    explicit=override or os.getenv('SST_A065_FREMLIN_PATH','')
    wb=os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench')
    p=pathlib.Path(explicit) if explicit else pathlib.Path(wb)/r['workbench_relative_path']
    return p.absolute(),r

def resolve(root,override=None):
    raw,r=location(root,override)
    v={'schema':'A065-PROVIDER-MANIFEST-1','provider':'fremlin','carrier_id':r['carrier_id'],
       'source_family':r['source_family'],'independence_group':r['independence_group'],
       'expected_raw_sha256':r['expected_raw_sha256'],'resolved_path':str(raw),
       'status':'UNRESOLVED_SOURCE_MISSING','evidence_class':'geometry_only'}
    if raw.is_file():
        actual=digest(raw)
        v['observed_raw_sha256']=actual
        if actual!=r['expected_raw_sha256']:
            v['status']='FAIL_RAW_HASH_MISMATCH'
        else:
            try:
                points=load_geometry(raw)
                v['point_count']=len(points)
                v['status']='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY'
            except Exception as exc:
                v['status']='UNRESOLVED_PARSER_REQUIREMENT'
                v['parser_error']=type(exc).__name__+': '+str(exc)
    v['manifest_sha256']=hashlib.sha256(canon(v)).hexdigest()
    return v

def write_new(root,override=None):
    root=pathlib.Path(root);dst=root/'outputs'/NAME
    dst.parent.mkdir(parents=True,exist_ok=True)
    record=resolve(root,override)
    with dst.open('xb') as f:f.write(canon(record))
    return record

def verify(root):
    path=pathlib.Path(root)/'outputs'/NAME
    if not path.is_file():raise RuntimeError('PROVIDER_MANIFEST_MISSING: use the unique run launcher')
    record=readjson(path)
    expected=record.get('manifest_sha256')
    core={k:v for k,v in record.items() if k!='manifest_sha256'}
    if expected!=hashlib.sha256(canon(core)).hexdigest():raise RuntimeError('PROVIDER_MANIFEST_TAMPERED')
    raw,r=location(root,record['resolved_path'])
    if str(raw)!=record['resolved_path'] or r['expected_raw_sha256']!=record['expected_raw_sha256']:
        raise RuntimeError('PROVIDER_MANIFEST_SOURCE_CONTRACT_CHANGED')
    # TOCTOU guard: source status is never promoted in one component alone.
    current=resolve(root,record['resolved_path'])
    if current['manifest_sha256']!=record['manifest_sha256']:
        raise RuntimeError('PROVIDER_MANIFEST_SOURCE_CHANGED_OR_DISAPPEARED')
    return record

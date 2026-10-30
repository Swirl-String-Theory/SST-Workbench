"""Freeze the new public admission-smoke protocol, without creating reveal material."""
import hashlib
import json
import sys
import zipfile

sys.dont_write_bytecode=True
from preflight import ROOT,read,sha,atomic
from a054_prepare import TARGET,OUT
from phase3_prepare import create_json


def main():
    admission=read(OUT/'SOURCE_ADMISSION.json')
    # Preserve numeric kernels and every registered profile byte-for-byte.
    with zipfile.ZipFile(admission['source_archive']) as z:
        m=next(n for n in z.namelist() if n.endswith('/PACKAGE_MANIFEST.json'))
        prefix=m[:-len('PACKAGE_MANIFEST.json')]
        for name in ['geometry','energy','selector','dynamics','analysis','native','utils','commitment']:
            rel='a054_state/'+name+'.py'
            (TARGET/rel).write_bytes(z.read(prefix+rel))
        for name in ['basic','full','certify']:
            rel='configs/'+name+'.json'
            (TARGET/rel).write_bytes(z.read(prefix+rel))
    sys.path.insert(0,str(TARGET))
    from a054_state.commitment import compute_implementation_bundle
    bundle,rows=compute_implementation_bundle(TARGET)
    science=read(TARGET/'science_contract.json')
    science['implementation_commitment']['bundle_sha256']=bundle
    atomic(TARGET/'science_contract.json',science)
    atomic(TARGET/'data/IMPLEMENTATION_MANIFEST.json',{'schema':'A054-IMPLEMENTATION-MANIFEST-1','bundle_sha256':bundle,'files':rows})
    source={}
    for p in sorted(TARGET.rglob('*')):
        if p.is_file() and p.name not in {'LATEST_RUN.json','PUBLICATIONS.jsonl','SOURCE_MANIFEST_v0.6.0.json'} and not any(x in {'__pycache__','.pytest_cache','preregistration'} or '_outputs' in x for x in p.relative_to(TARGET).parts):
            source[p.relative_to(TARGET).as_posix()]=sha(p)
    digest=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    protocol={'schema':'SST-FALSIFIER-PROTOCOL-2','scope':'PUBLIC_ADMISSION_SMOKE_ONLY_NOT_FULL_PRIVATE_BLIND_FREEZE',
              'version':'v0.6.0','bundle_sha256':digest,'bundle_scheme':'A054_PUBLIC_MIGRATION_SOURCE_HASH_MAP',
              'files':[{'path':p,'sha256':h} for p,h in source.items()],
              'scientific_status_promoted':False,'reveal_authorized':False}
    (TARGET/'preregistration').mkdir(exist_ok=True)
    create_json(TARGET/'preregistration/MIGRATION_PROTOCOL.json',protocol)
    create_json(TARGET/'preregistration/FROZEN_PROTOCOL.json',protocol)
    print(json.dumps({'public_protocol_sha256':digest,'files':len(source),'implementation_bundle_sha256':bundle}))


if __name__=='__main__':main()

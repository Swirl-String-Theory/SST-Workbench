from __future__ import annotations
import hashlib
from pathlib import Path


def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def verify_manifest(root='.', manifest='MANIFEST_SHA256.txt'):
    root=Path(root); mf=root/manifest; rows=[]; ok=True
    if not mf.exists(): return {'pass':False,'error':f'manifest not found: {mf}','files':[]}
    for line in mf.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        expected,rel=line.split('  ',1); p=root/rel
        exists=p.is_file(); actual=sha256_file(p) if exists else None; match=exists and actual.lower()==expected.lower(); ok &= match
        rows.append({'path':rel,'exists':exists,'expected_sha256':expected,'actual_sha256':actual,'match':match})
    return {'pass':bool(ok),'file_count':len(rows),'files':rows}

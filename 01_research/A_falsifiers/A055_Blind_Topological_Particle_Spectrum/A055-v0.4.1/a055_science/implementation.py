from __future__ import annotations
from pathlib import Path
from .util import read_json,sha256_file

def verify_implementation(root:Path)->dict:
    root=Path(root); science=read_json(root/'science_contract.json'); commit=science.get('implementation_commitment') or {}
    rel=commit.get('manifest_path','IMPLEMENTATION_MANIFEST.json'); mp=root/rel
    if not mp.is_file(): raise RuntimeError(f'implementation manifest missing: {mp}')
    expected=commit.get('sha256'); actual=sha256_file(mp)
    if not expected or actual!=expected: raise RuntimeError(f'implementation manifest commitment mismatch: expected={expected}, actual={actual}')
    man=read_json(mp); bad={}
    for row in man.get('files',[]):
        p=root/row['path']
        if not p.is_file(): bad[row['path']]={'expected':row['sha256'],'actual':'MISSING'}
        else:
            got=sha256_file(p)
            if got!=row['sha256'] or p.stat().st_size!=row['size']:
                bad[row['path']]={'expected':row['sha256'],'actual':got,'expected_size':row['size'],'actual_size':p.stat().st_size}
    if bad: raise RuntimeError(f'implementation byte mismatch: {bad}')
    return {'status':'PASS','schema':man.get('schema'),'manifest_path':rel,'manifest_sha256':actual,'file_count':len(man.get('files',[]))}

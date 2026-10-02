from __future__ import annotations
from pathlib import Path
import hashlib,json
EXCLUDE={'outputs','.venv','build','__pycache__','.pytest_cache'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(root):
    root=Path(root);d={}
    for p in sorted(root.rglob('*')):
        if not p.is_file() or any(x in p.parts for x in EXCLUDE) or p.suffix in ('.pyc','.pyd','.so'):continue
        d[p.relative_to(root).as_posix()]=sha(p)
    return d
def seal(project_root,blind,catalog,config):
    project_root=Path(project_root);blind=Path(blind);cat=Path(catalog); rec={'format':'SST-FINITE-CORE-SEAL-1','code_tree':tree(project_root),'config_sha256':sha(config),'public_pairs_sha256':sha(cat/'pairs_public.csv')}
    files={p.relative_to(blind).as_posix():sha(p) for p in sorted(blind.rglob('*')) if p.is_file() and p.name!='SEALED_MANIFEST.json'};rec['result_files']=files;rec['result_tree_sha256']=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest();(blind/'SEALED_MANIFEST.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n',encoding='utf-8');return rec
def verify(project_root,blind,catalog,config):
    rec=json.loads((Path(blind)/'SEALED_MANIFEST.json').read_text(encoding='utf-8'))
    if rec['code_tree']!=tree(project_root):raise RuntimeError('code changed after seal')
    if rec['config_sha256']!=sha(config):raise RuntimeError('config changed after seal')
    if rec['public_pairs_sha256']!=sha(Path(catalog)/'pairs_public.csv'):raise RuntimeError('public pair table changed after seal')
    files={p.relative_to(blind).as_posix():sha(p) for p in sorted(Path(blind).rglob('*')) if p.is_file() and p.name!='SEALED_MANIFEST.json'}
    if files!=rec['result_files']:raise RuntimeError('blind result tree changed after seal')
    return rec

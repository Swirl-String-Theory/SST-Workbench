from __future__ import annotations
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone

CODE_EXT={'.py','.cpp','.h','.hpp','.json','.cmd','.toml','.txt','.md','.tex'}

def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def tree_records(root,exclude_names=()):
    root=Path(root);rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name not in exclude_names:
            rows.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    h=hashlib.sha256()
    for r in rows:h.update(f"{r['sha256']}  {r['path']}\n".encode())
    return h.hexdigest(),rows

def code_digest(project_root):
    root=Path(project_root);rows=[]
    excluded={'outputs','private','blind_catalog','.venv','build','__pycache__','.pytest_cache'}
    for p in sorted(root.rglob('*')):
        if not p.is_file() or any(part in excluded for part in p.parts):continue
        if p.suffix.lower() not in CODE_EXT:continue
        rows.append({'path':p.relative_to(root).as_posix(),'sha256':sha256_file(p)})
    h=hashlib.sha256()
    for r in rows:h.update(f"{r['sha256']}  {r['path']}\n".encode())
    return h.hexdigest(),rows

def seal(project_root,blind_dir,catalog_dir,config_path):
    project_root=Path(project_root);blind=Path(blind_dir);catalog=Path(catalog_dir);cfg=Path(config_path)
    summary=blind/'blind_summary.json'
    if not summary.exists():raise RuntimeError('blind_summary.json missing')
    s=json.loads(summary.read_text(encoding='utf-8'))
    if s.get('source_identity_read') is not False:raise RuntimeError('blind run does not certify source_identity_read=false')
    result_sha,result_files=tree_records(blind,{'SEALED_MANIFEST.json','BLIND_RESULT_SHA256.txt'})
    code_sha,code_files=code_digest(project_root)
    pub=json.loads((catalog/'manifest_public.json').read_text(encoding='utf-8'))
    catalog_sha,catalog_files=tree_records(catalog)
    # Verify the public manifest's own commitment to the anonymous pair table.
    if sha256_file(catalog/'pairs_public.csv') != pub.get('public_pair_sha256'):
        raise RuntimeError('public pair table no longer matches manifest_public.json')
    sealed={'status':'SEALED','sealed_utc':datetime.now(timezone.utc).isoformat(),'result_tree_sha256':result_sha,'code_sha256':code_sha,'public_manifest_sha256':sha256_file(catalog/'manifest_public.json'),'public_catalog_tree_sha256':catalog_sha,'public_catalog_files':catalog_files,'blind_config_sha256':sha256_file(cfg),'private_key_commitment_sha256':pub['private_key_commitment_sha256'],'result_files':result_files,'code_files':code_files,'rule':'Reveal must refuse if result tree, code, config, public catalog, or private-key commitment no longer matches.'}
    (blind/'SEALED_MANIFEST.json').write_text(json.dumps(sealed,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (blind/'BLIND_RESULT_SHA256.txt').write_text(result_sha+'  blind_result_tree\n',encoding='utf-8')
    return sealed

def verify(project_root,blind_dir,catalog_dir,config_path,private_dir):
    project_root=Path(project_root);blind=Path(blind_dir);catalog=Path(catalog_dir);private=Path(private_dir);cfg=Path(config_path)
    sealed=json.loads((blind/'SEALED_MANIFEST.json').read_text(encoding='utf-8'))
    result_sha,_=tree_records(blind,{'SEALED_MANIFEST.json','BLIND_RESULT_SHA256.txt'})
    code_sha,_=code_digest(project_root)
    if result_sha!=sealed['result_tree_sha256']:raise RuntimeError('blind result tree changed after seal')
    if code_sha!=sealed['code_sha256']:raise RuntimeError('code/config files changed after seal')
    if sha256_file(cfg)!=sealed['blind_config_sha256']:raise RuntimeError('blind config changed after seal')
    if sha256_file(catalog/'manifest_public.json')!=sealed['public_manifest_sha256']:raise RuntimeError('public catalog manifest changed after seal')
    pub=json.loads((catalog/'manifest_public.json').read_text(encoding='utf-8'))
    if sha256_file(catalog/'pairs_public.csv')!=pub.get('public_pair_sha256'):raise RuntimeError('public pair table changed after preparation')
    catalog_sha,_=tree_records(catalog)
    if catalog_sha!=sealed['public_catalog_tree_sha256']:raise RuntimeError('anonymous public geometry/catalog changed after seal')
    h=hashlib.sha256()
    for p in sorted([private/'candidate_key.csv',private/'pair_key.csv'],key=lambda x:x.name):h.update(p.name.encode());h.update(b'\0');h.update(p.read_bytes());h.update(b'\0')
    if h.hexdigest()!=sealed['private_key_commitment_sha256']:raise RuntimeError('private identity key does not match pre-run commitment')
    return True

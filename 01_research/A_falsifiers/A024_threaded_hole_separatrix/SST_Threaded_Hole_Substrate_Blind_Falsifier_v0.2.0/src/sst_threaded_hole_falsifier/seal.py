from __future__ import annotations
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
CODE_EXT={'.py','.cpp','.h','.hpp','.json','.cmd','.toml','.txt','.md','.tex','.fseries'}
def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree_records(root,exclude_names=()):
    root=Path(root);rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name not in exclude_names:rows.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    h=hashlib.sha256();[h.update(f"{r['sha256']}  {r['path']}\n".encode()) for r in rows];return h.hexdigest(),rows
def code_digest(root):
    root=Path(root);rows=[];excluded={'outputs','private','blind_catalog','.venv','build','__pycache__','.pytest_cache'}
    for p in sorted(root.rglob('*')):
        if p.is_file() and not any(x in excluded for x in p.parts) and p.suffix.lower() in CODE_EXT:rows.append({'path':p.relative_to(root).as_posix(),'sha256':sha256_file(p)})
    h=hashlib.sha256();[h.update(f"{r['sha256']}  {r['path']}\n".encode()) for r in rows];return h.hexdigest(),rows
def seal(project_root,blind,catalog,config):
    project_root=Path(project_root);blind=Path(blind);catalog=Path(catalog);config=Path(config);s=json.loads((blind/'blind_summary.json').read_text(encoding='utf-8'))
    for k in ('carrier_identity_read','condition_identity_read','gravity_target_used'):
        if s.get(k) is not False:raise RuntimeError(f'blind certification failed: {k}')
    rsha,rfiles=tree_records(blind,{'SEALED_MANIFEST.json','BLIND_RESULT_SHA256.txt'});csha,cfiles=code_digest(project_root);psha,pfiles=tree_records(catalog);pub=json.loads((catalog/'manifest_public.json').read_text(encoding='utf-8'))
    if sha256_file(catalog/'pairs_public.csv')!=pub['public_pair_sha256']:raise RuntimeError('public pair table changed')
    rec={'status':'SEALED','sealed_utc':datetime.now(timezone.utc).isoformat(),'result_tree_sha256':rsha,'code_sha256':csha,'public_catalog_tree_sha256':psha,'blind_config_sha256':sha256_file(config),'private_key_commitment_sha256':pub['private_key_commitment_sha256'],'result_files':rfiles,'code_files':cfiles,'public_files':pfiles}
    (blind/'SEALED_MANIFEST.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n', encoding='utf-8');(blind/'BLIND_RESULT_SHA256.txt').write_text(rsha+'  blind_result_tree\n', encoding='utf-8');return rec
def verify(project_root,blind,catalog,config,private):
    project_root=Path(project_root);blind=Path(blind);catalog=Path(catalog);config=Path(config);private=Path(private);rec=json.loads((blind/'SEALED_MANIFEST.json').read_text(encoding='utf-8'));rsha,_=tree_records(blind,{'SEALED_MANIFEST.json','BLIND_RESULT_SHA256.txt'});csha,_=code_digest(project_root);psha,_=tree_records(catalog)
    if rsha!=rec['result_tree_sha256']:raise RuntimeError('blind result tree changed after seal')
    if csha!=rec['code_sha256']:raise RuntimeError('code changed after seal')
    if psha!=rec['public_catalog_tree_sha256']:raise RuntimeError('public catalog changed after seal')
    if sha256_file(config)!=rec['blind_config_sha256']:raise RuntimeError('config changed after seal')
    h=hashlib.sha256()
    for p in sorted([private/'candidate_key.csv',private/'pair_key.csv',private/'qualification.csv'],key=lambda x:x.name):h.update(p.name.encode());h.update(b'\0');h.update(p.read_bytes());h.update(b'\0')
    if h.hexdigest()!=rec['private_key_commitment_sha256']:raise RuntimeError('private key commitment mismatch')
    return True

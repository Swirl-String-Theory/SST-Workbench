"""Per-dataset SHA-256 manifest verification. Not cryptographic authentication."""
from __future__ import annotations
import hashlib,json,pathlib

def canon(o):return (json.dumps(o,sort_keys=True,ensure_ascii=True,separators=(',',':'))+'\n').encode('ascii')
def sha(data):return hashlib.sha256(data).hexdigest()
def readjson(path):return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
def writejson(path,o):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canon(o))

def create_seal(root,dataset_id):
    root=pathlib.Path(root)
    paths=sorted(p for p in (root/'data'/dataset_id).rglob('*') if p.is_file())
    if not paths:raise RuntimeError('empty dataset')
    files={str(p.relative_to(root)).replace('\\','/'):sha(p.read_bytes()) for p in paths}
    manifest={'schema':'SST_SEAL_v1','dataset_id':dataset_id,'digest_algorithm':'SHA256','files':files,'note':'A065 v0.3.0 tamper-evident locally hashed dataset; not a cryptographic identity signature.'}
    manifest['self_sha256']=sha(canon(manifest))
    writejson(root/'seals'/f'{dataset_id}.seal.json',manifest)
    return manifest

def verify_seal(root,dataset_id):
    root=pathlib.Path(root);fname=root/'seals'/f'{dataset_id}.seal.json';seal=readjson(fname)
    tmp={k:v for k,v in seal.items() if k!='self_sha256'}
    if seal.get('self_sha256') != sha(canon(tmp)):raise RuntimeError(f'{dataset_id}: manifest self hash fails')
    if seal.get('dataset_id')!=dataset_id:raise RuntimeError('incorrect seal domain')
    expected=seal['files']; actual={str(p.relative_to(root)).replace('\\','/'):sha(p.read_bytes()) for p in (root/'data'/dataset_id).rglob('*') if p.is_file()}
    if expected!=actual:raise RuntimeError(f'{dataset_id}: dataset content/filename tampering detected')
    return seal['self_sha256']

def verify_all(root):
    ids=['D01_EULER','D02_CLOCK_LINK','D03_TWO_SURFACE']
    actual={i:verify_seal(root,i) for i in ids}
    commit=readjson(pathlib.Path(root)/'seals'/'GLOBAL_COMMITMENT.json')
    if commit['seals']!=actual:raise RuntimeError('global dataset commitment mismatch')
    target=pathlib.Path(root)/'private_reveal'/'targets.json'
    if target.exists() and commit['private_target_sha256']!=sha(target.read_bytes()):raise RuntimeError('private target commitment mismatch')
    # A public BLIND package MUST work without the escrow target; reveal checks strictly.

    return actual

def create_global_commitment(root):
    root=pathlib.Path(root);ids=['D01_EULER','D02_CLOCK_LINK','D03_TWO_SURFACE']
    commit={'schema':'SST_TRIADIC_CASIMIR_COMMIT_V1','seals':{i:verify_seal(root,i) for i in ids},'private_target_sha256':sha((root/'private_reveal'/'targets.json').read_bytes()),'framework_authority':'EXTERNAL_CANONICAL_FROZEN_v1.0.7_NOT_VENDORED','source_class':'ONE_SOURCED_PKLSA_GEOMETRY_PLUS_SYNTHETIC_CONTROLS'}
    writejson(root/'seals'/'GLOBAL_COMMITMENT.json',commit)
    return commit

from __future__ import annotations
from pathlib import Path
import json, hashlib, os
from .common import sha256_file,dump_json

def code_manifest(root):
    root=Path(root);rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name not in {'CODE_SEAL.json','PACKAGE_MANIFEST.json'} and not any(x in p.parts for x in ['outputs','private_reveal_keys','.venv','build','__pycache__']): rows.append({'path':str(p.relative_to(root)).replace('\\','/'),'sha256':sha256_file(p),'size':p.stat().st_size})
    return rows

def seal(root,out):
    m=code_manifest(root); payload=json.dumps(m,sort_keys=True,separators=(',',':')).encode(); r={'format':'SST-WP-CODE-SEAL-2.2','manifest':m,'commitment_sha256':hashlib.sha256(payload).hexdigest()};dump_json(out,r);return r

def scan_target_leak(obj):
    txt=json.dumps(obj).lower(); bad=[]
    for token in ['6.62607015e-34','1.054571817e-34','"h"','"hbar"','planck_target','target_action','rho_core','f_swirl_max']:
        if token in txt: bad.append(token)
    return bad

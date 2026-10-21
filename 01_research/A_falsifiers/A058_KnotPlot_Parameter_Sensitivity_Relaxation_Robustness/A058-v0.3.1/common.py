from __future__ import annotations
import json, hashlib, os, sys, time, pathlib, math
from datetime import datetime, timezone
from pathlib import Path

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def dump(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): raise FileExistsError(f'Non-overwrite: {p}')
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def unique(root,stem):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    # Generate collision-safe run name. Only created here, never rename old outputs.
    from uuid import uuid4
    d=root/(f'{stem}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}')
    d.mkdir(exist_ok=False)
    return d

def guard(ok,msg):
    if not ok: raise ValueError(msg)

def run_result(status,reason,**extra):
    return {'status':status,'reason':reason,**extra}

def sha_record(path):
    p=Path(path)
    return {'name':p.name,'sha256':digest(p),'size_bytes':p.stat().st_size}

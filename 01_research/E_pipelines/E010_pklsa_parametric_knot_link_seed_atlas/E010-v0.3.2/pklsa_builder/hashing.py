from __future__ import annotations
from pathlib import Path
import hashlib, json, numpy as np

def sha256_file(path, chunk=1024*1024):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while True:
            b=f.read(chunk)
            if not b: break
            h.update(b)
    return h.hexdigest()

def sha256_bytes(data: bytes): return hashlib.sha256(data).hexdigest()

def geometry_sha256(components):
    h=hashlib.sha256()
    h.update(b'PKLSA-GEOMETRY-SHA256-v1\0')
    for c in components:
        a=np.asarray(c,dtype='<f8',order='C')
        h.update(np.asarray(a.shape,dtype='<i8').tobytes())
        h.update(a.tobytes(order='C'))
    return h.hexdigest()

def stable_id(prefix, *parts, n=16):
    payload='\x1f'.join(str(x) for x in parts).encode('utf-8')
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:n]}"

def write_json(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding='utf-8')
    return p

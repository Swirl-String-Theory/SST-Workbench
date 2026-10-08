from __future__ import annotations
from pathlib import Path
import json, hashlib, math
import numpy as np

def write_json(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def append_jsonl(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a',encoding='utf-8') as f:f.write(json.dumps(obj,sort_keys=True,ensure_ascii=False)+"\n")

def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def geometry_sha256(components):
    h=hashlib.sha256();h.update(b'PKLSA-GEOMETRY-SHA256-v1\0')
    for comp in components:
        a=np.asarray(comp,dtype='<f8',order='C')
        h.update(np.asarray(a.shape,dtype='<i8').tobytes())
        h.update(a.tobytes(order='C'))
    return h.hexdigest()

def relerr(a,b,eps=1e-30): return abs(float(a)-float(b))/max(abs(float(a)),abs(float(b)),eps)
def finite(x): return bool(np.all(np.isfinite(np.asarray(x))))
def safe_mean(v):
    a=np.asarray(v,dtype=float);a=a[np.isfinite(a)]
    return float(a.mean()) if a.size else None
def safe_std(v):
    a=np.asarray(v,dtype=float);a=a[np.isfinite(a)]
    return float(a.std(ddof=1)) if a.size>1 else (0.0 if a.size==1 else None)
def safe_cv(v):
    m=safe_mean(v);s=safe_std(v)
    return None if m in (None,0.0) or s is None else abs(s/m)
def crossing_number(topology: str):
    import re
    s=topology.strip()
    m=re.match(r'^(?:L)?(\d+)[an_]',s)
    if m:return int(m.group(1))
    m=re.match(r'^(\d+)_',s)
    return int(m.group(1)) if m else None

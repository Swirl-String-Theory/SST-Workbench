from __future__ import annotations
from pathlib import Path
import hashlib,json
import numpy as np

def sha256_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def atomic_json(path,obj):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8');tmp.replace(path)

def load_centerline(path):
    text=Path(path).read_text(encoding='utf-8',errors='replace');comps=[];cur=[]
    for ln in text.splitlines():
        s=ln.strip()
        if not s:
            if cur:comps.append(np.asarray(cur,float));cur=[]
            continue
        if s.startswith('#'):continue
        parts=s.replace(',',' ').split()
        vals=[]
        for x in parts:
            try:vals.append(float(x))
            except ValueError:break
        if len(vals)>=3:cur.append(vals[:3])
    if cur:comps.append(np.asarray(cur,float))
    out=[]
    for p in comps:
        if len(p)>3 and np.linalg.norm(p[0]-p[-1])<1e-12*max(1.0,float(np.ptp(p,axis=0).max())):p=p[:-1]
        if len(p)>=3:out.append(p)
    if not out:raise ValueError('no XYZ components found')
    return out

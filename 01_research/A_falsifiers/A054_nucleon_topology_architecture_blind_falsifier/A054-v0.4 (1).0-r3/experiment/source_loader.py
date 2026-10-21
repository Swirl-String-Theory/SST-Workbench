from __future__ import annotations
from pathlib import Path
import json, hashlib, numpy as np
from .blind_geometry import load_components_npz, resample_closed_curve

def sha256(path):
    h=hashlib.sha256();
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def load_manifest_cases(root,manifest_rel,data_rel,n=None,limit=None):
    root=Path(root); man=json.loads((root/manifest_rel).read_text()); key='candidates'; rows=[]
    for c in man[key]:
        p=root/data_rel/c['file'];
        if sha256(p)!=c['sha256']: raise RuntimeError(f'hash mismatch: {p}')
        comps=load_components_npz(p)
        if n is not None: comps=[resample_closed_curve(x,int(n)) for x in comps]
        rows.append((c.get('anonymous_id') or c.get('opaque_id'),comps,c))
    rows=sorted(rows,key=lambda x:hashlib.sha256(x[0].encode()).hexdigest())
    return rows if limit is None else rows[:int(limit)]

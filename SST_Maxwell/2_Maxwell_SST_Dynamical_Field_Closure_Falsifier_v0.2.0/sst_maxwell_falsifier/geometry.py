from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

def load_centerline(path):
    text=Path(path).read_text(encoding='utf-8',errors='replace')
    comps=[]; cur=[]
    for ln in text.splitlines():
        if not ln.strip():
            if cur: comps.append(np.asarray(cur,float));cur=[]
            continue
        parts=ln.split()
        if len(parts)<3: continue
        cur.append([float(parts[0]),float(parts[1]),float(parts[2])])
    if cur: comps.append(np.asarray(cur,float))
    if not comps: raise ValueError(f'no xyz components in {path}')
    return comps

def resample_closed(p,n):
    p=np.asarray(p,float); q=np.vstack([p,p[0]]); seg=np.linalg.norm(np.diff(q,axis=0),axis=1); s=np.r_[0,np.cumsum(seg)]; L=s[-1]
    if L<=0: raise ValueError('zero-length component')
    t=np.linspace(0,L,n,endpoint=False); out=np.empty((n,3))
    for j in range(3): out[:,j]=np.interp(t,s,q[:,j])
    return out

def center_components(comps):
    pts=np.vstack(comps); c=pts.mean(axis=0); return [p-c for p in comps],c

def characteristic_diameter(comps):
    pts=np.vstack(comps); c=pts.mean(axis=0); return 2.0*float(np.max(np.linalg.norm(pts-c,axis=1)))

def companion_metrics(path):
    p=Path(path); m=p.with_name(p.stem+'.metrics.json')
    if not m.exists(): return None
    try:return json.loads(m.read_text(encoding='utf-8'))
    except Exception:return None

def discover(root,patterns):
    root=Path(root); out=[]
    for pat in patterns: out.extend(root.glob(pat))
    return sorted(set(out),key=lambda p:p.name.lower())

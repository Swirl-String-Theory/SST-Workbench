from __future__ import annotations
from pathlib import Path
import math,re
import numpy as np

def read_xyz(path:Path):
    pts=[]
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        s=line.strip()
        if not s: continue
        vals=[]
        for tok in re.split(r'[\s,]+',s):
            try: vals.append(float(tok))
            except ValueError: pass
        if len(vals)>=3 and all(math.isfinite(v) for v in vals[:3]): pts.append(vals[:3])
    a=np.asarray(pts,dtype=np.float64)
    if a.ndim!=2 or a.shape[0]<4 or a.shape[1]!=3: raise ValueError(f'No usable XYZ curve in {path}')
    return a

def curve_metrics(x):
    x=np.asarray(x,dtype=np.float64)
    edges=np.roll(x,-1,axis=0)-x
    el=np.linalg.norm(edges,axis=1)
    cen=x.mean(axis=0); rg=float(np.sqrt(np.mean(np.sum((x-cen)**2,axis=1))))
    mean=float(el.mean())
    return {'n':int(len(x)),'length':float(el.sum()),'rg':rg,'edge_cv':float(el.std()/mean if mean else math.inf)}

def resample_closed(x,m=256):
    x=np.asarray(x,dtype=np.float64)
    y=np.vstack([x,x[0]])
    d=np.linalg.norm(np.diff(y,axis=0),axis=1)
    s=np.concatenate([[0.0],np.cumsum(d)])
    L=s[-1]
    if not L>0: raise ValueError('degenerate curve')
    q=np.linspace(0,L,m,endpoint=False)
    out=np.column_stack([np.interp(q,s,y[:,j]) for j in range(3)])
    out-=out.mean(axis=0)
    rg=np.sqrt(np.mean(np.sum(out*out,axis=1)))
    return out/rg

def _kabsch_rms(a,b):
    h=b.T@a
    u,s,vt=np.linalg.svd(h)
    r=u@vt
    if np.linalg.det(r)<0:
        u[:,-1]*=-1; r=u@vt
    z=b@r
    return float(np.sqrt(np.mean(np.sum((a-z)**2,axis=1))))

def shape_distance(a,b,m=128):
    a=resample_closed(a,m); b=resample_closed(b,m)
    best=math.inf
    for rev in (False,True):
        bb=b[::-1].copy() if rev else b
        for sh in range(m):
            best=min(best,_kabsch_rms(a,np.roll(bb,sh,axis=0)))
    return best

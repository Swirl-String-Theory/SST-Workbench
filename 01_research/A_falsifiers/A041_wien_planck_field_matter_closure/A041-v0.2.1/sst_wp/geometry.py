from __future__ import annotations
from pathlib import Path
import re, math
import numpy as np
from .common import sha256_file, geometry_sha256

FLOAT_RE=re.compile(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')

def load_geometry(path):
    path=Path(path); text=path.read_text(encoding='utf-8',errors='ignore')
    comps=[]; cur=[]
    for line in text.splitlines():
        s=line.strip()
        if not s or s.startswith('>') or s.lower().startswith('component'):
            if len(cur)>=3: comps.append(np.array(cur,float));cur=[]
            continue
        vals=FLOAT_RE.findall(s)
        if len(vals)>=3:
            cur.append([float(vals[-3]),float(vals[-2]),float(vals[-1])])
    if len(cur)>=3: comps.append(np.array(cur,float))
    if not comps: raise ValueError(f'No XYZ components parsed from {path}')
    clean=[]
    for c in comps:
        if len(c)>3 and np.linalg.norm(c[0]-c[-1]) < 1e-12*max(1,np.linalg.norm(c).max()): c=c[:-1]
        if len(c)>=3: clean.append(c)
    if not clean: raise ValueError('No usable closed components')
    return clean

def component_length(c): return float(np.sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)))
def total_length(comps): return sum(component_length(c) for c in comps)

def resample_closed(c,n):
    seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); s=np.concatenate([[0],np.cumsum(seg)]); L=s[-1]
    if L<=0: raise ValueError('zero-length component')
    q=np.linspace(0,L,n,endpoint=False); out=np.zeros((n,3))
    for ii,qq in enumerate(q):
        j=min(np.searchsorted(s,qq,side='right')-1,len(c)-1); u=(qq-s[j])/seg[j] if seg[j]>0 else 0; out[ii]=(1-u)*c[j]+u*c[(j+1)%len(c)]
    return out

def normalize_components(comps,n_total=96):
    Ls=np.array([component_length(c) for c in comps]); alloc=np.maximum(8,np.round(n_total*Ls/Ls.sum()).astype(int))
    # exact total correction
    while alloc.sum()<n_total: alloc[np.argmax(Ls/alloc)]+=1
    while alloc.sum()>n_total and alloc.max()>8: alloc[np.argmax(alloc)]-=1
    rs=[resample_closed(c,int(n)) for c,n in zip(comps,alloc)]
    allp=np.vstack(rs); centroid=np.mean(allp,axis=0); rs=[c-centroid for c in rs]; L=total_length(rs); rs=[c/L for c in rs]
    pts=np.vstack(rs); off=[0];
    for c in rs: off.append(off[-1]+len(c))
    return pts,np.array(off,dtype=np.int64)

def split_components(points, offsets): return [points[offsets[i]:offsets[i+1]].copy() for i in range(len(offsets)-1)]
def pack(comps):
    p=np.vstack(comps);o=[0]
    for c in comps:o.append(o[-1]+len(c))
    return p,np.array(o,dtype=np.int64)

def spacing_metrics(points,offsets):
    vals=[]
    for c in split_components(points,offsets): vals.extend(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1))
    a=np.asarray(vals);return {'ds_min':float(a.min()),'ds_max':float(a.max()),'ds_mean':float(a.mean()),'ds_cv':float(a.std()/a.mean()),'edge_ratio':float(a.max()/a.min())}

def reparameterize(points,offsets):
    comps=split_components(points,offsets); return pack([resample_closed(c,len(c)) for c in comps])

def discover(root):
    root=Path(root); exts={'.txt','.xyz','.dat'}; return sorted([p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in exts])

def inventory_record(path,n_total=96):
    comps=load_geometry(path); p,o=normalize_components(comps,n_total)
    return {'path':str(path),'name':Path(path).name,'source_sha256':sha256_file(path),'geometry_sha256':geometry_sha256(p,o),'components':len(o)-1,'n_points':len(p),**spacing_metrics(p,o)}

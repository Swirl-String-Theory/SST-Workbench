from __future__ import annotations
import json, math
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class KnotGeometry:
    path: Path
    components: list[np.ndarray]
    metrics: dict


def read_centerline_txt(path: Path)->list[np.ndarray]:
    comps=[]; cur=[]
    for raw in path.read_text(encoding='utf-8',errors='replace').splitlines():
        s=raw.strip()
        if not s:
            if cur:
                comps.append(np.asarray(cur,float)); cur=[]
            continue
        if s.startswith('#'): continue
        parts=s.replace(',',' ').split()
        if len(parts)<3: continue
        try: cur.append([float(parts[0]),float(parts[1]),float(parts[2])])
        except ValueError: continue
    if cur: comps.append(np.asarray(cur,float))
    if not comps or any(c.ndim!=2 or c.shape[1]!=3 or len(c)<8 for c in comps):
        raise ValueError(f"{path}: expected one or more blank-line-separated XYZ closed centerlines")
    return comps


def _edge_lengths(c):
    return np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)

def infer_metrics(components):
    edges=np.concatenate([_edge_lengths(c) for c in components])
    return {
        'component_count':len(components),
        'vertices_per_component':[int(len(c)) for c in components],
        'length':float(np.sum(edges)),
        'edge_length_mean':float(np.mean(edges)),
        'edge_length_min':float(np.min(edges)),
        'edge_length_max':float(np.max(edges)),
        'edge_length_ratio':float(np.max(edges)/np.min(edges)),
        'edge_length_cv':float(np.std(edges,ddof=1)/np.mean(edges)) if len(edges)>1 else 0.0,
    }

def load_geometry(path: Path)->KnotGeometry:
    comps=read_centerline_txt(path)
    metrics_path=path.with_name(path.stem+'.metrics.json')
    metrics={}
    if metrics_path.exists():
        try: metrics=json.loads(metrics_path.read_text(encoding='utf-8'))
        except Exception: metrics={}
    inferred=infer_metrics(comps)
    for k,v in inferred.items(): metrics.setdefault(k,v)
    return KnotGeometry(path=path,components=comps,metrics=metrics)


def resample_closed(c: np.ndarray, n: int)->np.ndarray:
    c=np.asarray(c,float)
    q=np.vstack([c,c[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1)
    s=np.concatenate([[0.0],np.cumsum(ds)])
    L=float(s[-1])
    if L<=0: raise ValueError('zero-length component')
    targets=np.linspace(0.0,L,int(n)+1)[:-1]
    out=np.empty((len(targets),3),float)
    for d in range(3): out[:,d]=np.interp(targets,s,q[:,d])
    return out


def concatenate_segments(components: list[np.ndarray]):
    aa=[]; bb=[]
    for c in components:
        aa.append(c); bb.append(np.roll(c,-1,axis=0))
    return np.ascontiguousarray(np.vstack(aa),float),np.ascontiguousarray(np.vstack(bb),float)


def list_knot_files(knots_dir: Path, config: dict)->list[Path]:
    sel=config.get('selection',{})
    include=sel.get('include',[])
    exclude=sel.get('exclude',[])
    if include:
        files=[]
        for name in include:
            p=knots_dir/name
            if p.exists(): files.append(p)
    else:
        files=sorted(knots_dir.glob(sel.get('glob','*_final.txt')))
    if exclude:
        import fnmatch
        files=[p for p in files if not any(fnmatch.fnmatch(p.name,pat) for pat in exclude)]
    max_files=int(sel.get('max_files',0) or 0)
    if max_files>0: files=files[:max_files]
    return files

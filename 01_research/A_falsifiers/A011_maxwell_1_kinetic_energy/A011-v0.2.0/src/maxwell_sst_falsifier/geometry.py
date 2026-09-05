from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv, math, re
from typing import Iterable
import numpy as np
from .native_ext import segment_lengths, writhe_midpoint

SUPPORTED_EXTENSIONS={".vect",".xyz",".csv",".txt",".npy"}

@dataclass
class CurveRecord:
    knot_id: str
    parent_id: str
    path: Path
    points: np.ndarray
    closed: bool=True
    component_index: int=0


def sanitize_id(s:str)->str:
    s=re.sub(r"[^A-Za-z0-9_.+-]+","_",s.strip())
    return s.strip("_") or "curve"


def discover_knot_files(root:Path)->list[Path]:
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(f"Knot directory does not exist: {root}")
    out=[]
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and not p.name.startswith("."):
            out.append(p)
    return sorted(out,key=lambda p:str(p).lower())


def _clean_duplicate_endpoint(points:np.ndarray, closed:bool)->np.ndarray:
    p=np.asarray(points,dtype=float)
    if len(p)>=2 and closed:
        scale=max(float(np.linalg.norm(p.max(axis=0)-p.min(axis=0))),1.0)
        if float(np.linalg.norm(p[0]-p[-1])) <= 1e-10*scale:
            p=p[:-1]
    return np.ascontiguousarray(p,dtype=float)


def _parse_vect(path:Path)->list[tuple[np.ndarray,bool]]:
    text=path.read_text(encoding="utf-8",errors="ignore")
    # Strip comments; token mode handles wrapped lines used by KnotPlot/Geomview.
    clean="\n".join(line.split("#",1)[0] for line in text.splitlines())
    toks=clean.split()
    if not toks or toks[0].upper()!="VECT": raise ValueError(f"Not a VECT file: {path}")
    i=1
    try:
        npoly=int(toks[i]); nvert=int(toks[i+1]); ncolor=int(toks[i+2]); i+=3
        counts=[int(toks[i+j]) for j in range(npoly)]; i+=npoly
        color_counts=[int(toks[i+j]) for j in range(npoly)]; i+=npoly
        coords=np.asarray([float(toks[i+j]) for j in range(3*nvert)],dtype=float).reshape(nvert,3)
    except Exception as exc: raise ValueError(f"Malformed VECT header/coordinates in {path}: {exc}") from exc
    out=[]; k=0
    for c in counts:
        n=abs(c); closed=(c<0)
        if n<2: k+=n; continue
        pts=coords[k:k+n].copy(); k+=n
        out.append((_clean_duplicate_endpoint(pts,closed),closed))
    if not out: raise ValueError(f"No polyline with >=2 vertices in {path}")
    return out


def _parse_csv(path:Path)->np.ndarray:
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        sample=f.read(4096); f.seek(0)
        try: dialect=csv.Sniffer().sniff(sample,delimiters=",;\t ")
        except Exception: dialect=csv.excel
        reader=csv.DictReader(f,dialect=dialect)
        names=[(n or "").strip().lower() for n in (reader.fieldnames or [])]
        if all(k in names for k in ("x","y","z")):
            idx={k:names.index(k) for k in ("x","y","z")}; orig=reader.fieldnames or []
            rows=[]
            for r in reader:
                try: rows.append([float(r[orig[idx["x"]]]),float(r[orig[idx["y"]]]),float(r[orig[idx["z"]]])])
                except Exception: pass
            if rows: return np.asarray(rows,dtype=float)
    return _parse_xyz_text(path)


def _parse_xyz_text(path:Path)->np.ndarray:
    rows=[]
    for line in path.read_text(encoding="utf-8",errors="ignore").splitlines():
        line=line.strip()
        if not line or line.startswith(("#",";")): continue
        vals=re.split(r"[,;\s]+",line)
        nums=[]
        for v in vals:
            try: nums.append(float(v))
            except Exception: pass
        if len(nums)>=3: rows.append(nums[:3])
    if len(rows)<2: raise ValueError(f"Could not parse >=2 xyz rows from {path}")
    return np.asarray(rows,dtype=float)


def load_curves(path:Path)->list[CurveRecord]:
    path=Path(path); parent=sanitize_id(path.stem); ext=path.suffix.lower()
    if ext==".vect": comps=_parse_vect(path)
    elif ext==".npy": comps=[(np.asarray(np.load(path),dtype=float),True)]
    elif ext==".csv": comps=[(_parse_csv(path),True)]
    else: comps=[(_parse_xyz_text(path),True)]
    out=[]
    multi=len(comps)>1
    for j,(pts,closed) in enumerate(comps):
        pts=_clean_duplicate_endpoint(pts,closed)
        if pts.ndim!=2 or pts.shape[1]!=3 or len(pts)<3: continue
        kid=f"{parent}__c{j+1:02d}" if multi else parent
        out.append(CurveRecord(kid,parent,path,pts,bool(closed),j))
    return out


def resample_uniform(points:np.ndarray,n:int,closed:bool=True)->np.ndarray:
    p=np.asarray(points,dtype=float)
    if n<8: raise ValueError("resample count must be >=8")
    if closed:
        seg=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
        cumulative=np.concatenate([[0.0],np.cumsum(seg)])
        total=float(cumulative[-1])
        if total<=0: raise ValueError("zero-length curve")
        targets=np.linspace(0,total,n+1)[:-1]
        q=np.vstack([p,p[0]])
    else:
        seg=np.linalg.norm(np.diff(p,axis=0),axis=1); cumulative=np.concatenate([[0.0],np.cumsum(seg)])
        total=float(cumulative[-1]); targets=np.linspace(0,total,n); q=p
    out=np.empty((len(targets),3),dtype=float)
    for k,t in enumerate(targets):
        idx=min(int(np.searchsorted(cumulative,t,side="right")-1),len(cumulative)-2)
        ds=cumulative[idx+1]-cumulative[idx]; u=0.0 if ds<=0 else (t-cumulative[idx])/ds
        out[k]=(1-u)*q[idx]+u*q[idx+1]
    return np.ascontiguousarray(out)


def centered_unit_rms(points:np.ndarray)->tuple[np.ndarray,np.ndarray,float]:
    p=np.asarray(points,dtype=float); c=p.mean(axis=0); q=p-c
    rms=float(np.sqrt(np.mean(np.sum(q*q,axis=1))))
    if rms<=0: raise ValueError("degenerate curve RMS radius")
    return np.ascontiguousarray(q/rms),c,rms


def tangent_vectors(points:np.ndarray,closed:bool=True)->np.ndarray:
    p=np.asarray(points,dtype=float)
    if closed: d=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    else:
        d=np.gradient(p,axis=0)
    n=np.linalg.norm(d,axis=1); n[n==0]=1.0
    return d/n[:,None]


def curvature_samples(points:np.ndarray,closed:bool=True)->np.ndarray:
    p=np.asarray(points,dtype=float); t=tangent_vectors(p,closed)
    if closed:
        dt=np.roll(t,-1,axis=0)-t
        ds=0.5*(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)+np.roll(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1),1))
    else:
        dt=np.gradient(t,axis=0); ds=np.gradient(np.arange(len(p),dtype=float)); ds[:]=max(float(np.mean(np.linalg.norm(np.diff(p,axis=0),axis=1))),1e-300)
    ds=np.maximum(ds,1e-300)
    return np.linalg.norm(dt,axis=1)/ds


def geometry_metrics(rec:CurveRecord,resample_n:int)->tuple[dict,np.ndarray]:
    p=resample_uniform(rec.points,resample_n,rec.closed)
    seg=np.asarray(segment_lengths(p,rec.closed),dtype=float)
    length=float(seg.sum()); mean=float(seg.mean()) if len(seg) else 0.0
    curv=curvature_samples(p,rec.closed)
    c=p.mean(axis=0); rms=float(np.sqrt(np.mean(np.sum((p-c)**2,axis=1))))
    bbox=p.max(axis=0)-p.min(axis=0)
    wr=float(writhe_midpoint(p,rec.closed)) if rec.closed else float("nan")
    row={
        "knot":rec.knot_id,"parent":rec.parent_id,"file":str(rec.path),"component":rec.component_index+1,
        "closed":rec.closed,"input_points":len(rec.points),"resampled_points":len(p),"length_units":length,
        "rms_radius_units":rms,"bbox_x":float(bbox[0]),"bbox_y":float(bbox[1]),"bbox_z":float(bbox[2]),
        "segment_mean":mean,"segment_cv":float(seg.std()/mean) if mean>0 else float("nan"),
        "curvature_mean":float(np.mean(curv)),"curvature_max":float(np.max(curv)),"writhe_midpoint":wr,
        "note":"Geometry-only diagnostics; source-file units are retained. Midpoint writhe is a convergence diagnostic, not an exact invariant."
    }
    return row,p

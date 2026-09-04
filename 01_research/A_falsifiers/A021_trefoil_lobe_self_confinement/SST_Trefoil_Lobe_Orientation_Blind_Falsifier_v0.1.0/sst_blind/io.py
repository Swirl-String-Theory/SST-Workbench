from __future__ import annotations
import hashlib, re
from pathlib import Path
import numpy as np
_FLOAT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][-+]?\d+)?")

def sha256_file(path: str|Path) -> str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def _nums(line:str):
    return [float(x.replace('D','E').replace('d','e')) for x in _FLOAT.findall(line)]

def load_fseries(path: str|Path, n_samples: int=4096) -> np.ndarray:
    """Fremlin .fseries: j=0 line has ax0, ay0, az0; j>=1 lines have ax,bx,ay,by,az,bz."""
    path=Path(path)
    rows=[]
    for raw in path.read_text(encoding='utf-8',errors='replace').splitlines():
        s=raw.strip()
        if not s or s.startswith('%') or s.startswith('#'): continue
        vals=_nums(s)
        if vals: rows.append(vals)
    if not rows: raise ValueError(f"No numeric Fourier rows found in {path}")
    if len(rows[0])==3:
        # Fremlin extended form: explicit j=0 cosine constants ax0, ay0, az0.
        a0=np.asarray(rows[0],float); harm=rows[1:]
    elif len(rows[0])>=6:
        # Fremlin compact form (including knot.3_1.fseries): no constant row;
        # every six-column row is a harmonic, starting at j=1.
        a0=np.zeros(3,float); harm=rows
    else:
        raise ValueError(f"Unsupported first .fseries row with {len(rows[0])} values")
    coeff=[]
    for j,row in enumerate(harm,1):
        if len(row)<6:
            raise ValueError(f"Fourier harmonic {j} has {len(row)} values; expected 6")
        coeff.append(row[:6])
    t=np.linspace(-np.pi,np.pi,int(n_samples),endpoint=False)
    xyz=np.repeat(a0[None,:],len(t),axis=0)
    for j,row in enumerate(coeff,1):
        ax,bx,ay,by,az,bz=row
        c=np.cos(j*t); s=np.sin(j*t)
        xyz[:,0]+=ax*c+bx*s; xyz[:,1]+=ay*c+by*s; xyz[:,2]+=az*c+bz*s
    if not np.isfinite(xyz).all(): raise ValueError('Non-finite Fourier coordinates')
    return xyz

def load_xyz_text(path: str|Path) -> np.ndarray:
    """Tolerant KnotPlot ASCII coordinate reader. Accepts xyz or index+xyz rows."""
    path=Path(path); raw_rows=[]
    for raw in path.read_text(encoding='utf-8',errors='replace').splitlines():
        s=raw.strip()
        if not s or s.startswith('#') or s.startswith('%') or s.lower().startswith('knotplot'): continue
        vals=_nums(s)
        if len(vals)>=3: raw_rows.append(vals)
    if len(raw_rows)<8: raise ValueError(f"Only {len(raw_rows)} coordinate-like rows in {path}")
    # If first column is a monotone integer index, use the next three; otherwise first xyz triple.
    arr=[]
    indexed=False
    if all(len(r)>=4 for r in raw_rows[:min(32,len(raw_rows))]):
        q=np.array([r[0] for r in raw_rows[:min(32,len(raw_rows))]])
        indexed=np.allclose(q,np.round(q)) and np.all(np.diff(q)>=0) and np.ptp(q)>0
    for r in raw_rows:
        arr.append(r[1:4] if indexed and len(r)>=4 else r[:3])
    xyz=np.asarray(arr,float)
    # Drop duplicated closing point.
    if len(xyz)>3 and np.linalg.norm(xyz[0]-xyz[-1]) <= 1e-10*max(1.0,np.linalg.norm(np.ptp(xyz,axis=0))): xyz=xyz[:-1]
    if np.linalg.matrix_rank(xyz-xyz.mean(axis=0))<2: raise ValueError('Coordinate set is degenerate')
    return xyz

def load_curve(path: str|Path, kind: str, n_raw: int=4096) -> np.ndarray:
    if kind=='fseries': return load_fseries(path,n_raw)
    if kind=='knotplot': return load_xyz_text(path)
    raise ValueError(kind)

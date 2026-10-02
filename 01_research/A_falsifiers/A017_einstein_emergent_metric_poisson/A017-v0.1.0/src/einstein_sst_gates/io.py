from __future__ import annotations
from pathlib import Path
import zipfile, numpy as np
GEOM_EXTS={".csv",".txt",".dat",".vect",".npy",".npz"}

def _load_text_xyz(path:Path):
    txt=path.read_text(errors="ignore")
    lines=[ln.strip() for ln in txt.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    for delimiter in [",",None,";"]:
        try:
            arr=np.loadtxt(lines,delimiter=delimiter)
            if arr.ndim==1: arr=arr[None,:]
            if arr.ndim==2 and arr.shape[1]>=3: return np.asarray(arr[:,:3],float)
        except Exception: pass
    raise ValueError(f"cannot parse XYZ text: {path}")

def _load_vect(path:Path):
    lines=[ln.strip() for ln in path.read_text(errors="ignore").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines or lines[0].upper()!="VECT": raise ValueError("not a VECT file")
    npoly,nverts,_=[int(x) for x in lines[1].split()[:3]]; i=2; counts=[]
    while len(counts)<npoly: counts += [int(x) for x in lines[i].split()]; i+=1
    color_counts=[]
    while len(color_counts)<npoly: color_counts += [int(x) for x in lines[i].split()]; i+=1
    n0=abs(counts[0]); verts=[]
    while len(verts)<nverts and i<len(lines):
        parts=lines[i].replace(","," ").split(); i+=1
        if len(parts)>=3:
            try: verts.append([float(parts[0]),float(parts[1]),float(parts[2])])
            except Exception: pass
    if len(verts)<n0: raise ValueError("VECT vertices incomplete")
    return np.asarray(verts[:n0],float)

def load_centerline(path:Path):
    suf=path.suffix.lower()
    if suf==".vect": return _load_vect(path)
    if suf==".npy": return np.asarray(np.load(path),float)[:,:3]
    if suf==".npz":
        with np.load(path,allow_pickle=False) as z:
            for k in ("points","xyz","centerline"):
                if k in z: return np.asarray(z[k],float)[:,:3]
        raise ValueError("NPZ requires points/xyz/centerline")
    return _load_text_xyz(path)

def scan_geometries(input_dir:Path):
    out=[]
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in GEOM_EXTS:
            try:
                pts=load_centerline(p)
                if pts.ndim==2 and pts.shape[1]>=3 and len(pts)>=8: out.append((p,pts[:,:3]))
            except Exception: continue
    return out

def resolve_default_input(explicit=None,base=None):
    import os
    if explicit:
        p=Path(explicit).expanduser().resolve()
        if not p.exists(): raise FileNotFoundError(p)
        return p
    env=os.environ.get("SST_KNOT_DIR")
    if env and Path(env).exists(): return Path(env).resolve()
    base=Path(base or Path.cwd())
    for c in [base/".."/".."/"KnotPlot"/"knots"/"final",base/".."/"KnotPlot"/"knots"/"final",base/"KnotPlot"/"knots"/"final",base/"data"/"knots"]:
        c=c.resolve()
        if c.exists(): return c
    raise FileNotFoundError("No relaxed-knot directory found. Pass it as first argument or set SST_KNOT_DIR.")

def stage_input(path:Path,run_dir:Path):
    if path.is_dir(): return path
    if path.suffix.lower()==".zip":
        dst=run_dir/"_input_extracted"; dst.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(path,"r") as z: z.extractall(dst)
        return dst
    raise ValueError("Input must be a directory or ZIP archive")

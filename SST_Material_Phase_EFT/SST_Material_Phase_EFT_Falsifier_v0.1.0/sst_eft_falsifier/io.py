from pathlib import Path
import numpy as np
EXTENSIONS={".txt",".csv",".xyz",".dat"}
def load_curve(path):
    pts=[]
    with Path(path).open("r",errors="ignore") as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith(("#",";","//")): continue
            parts=s.replace(","," ").replace("\t"," ").split()
            if len(parts)<3: continue
            try: pts.append([float(parts[0]),float(parts[1]),float(parts[2])])
            except Exception: pass
    if len(pts)<16: raise ValueError("fewer than 16 xyz rows")
    x=np.asarray(pts,float)
    scale=max(1.0,float(np.ptp(x,axis=0).max()))
    if np.linalg.norm(x[0]-x[-1])<=1e-12*scale: x=x[:-1]
    if len(x)<16 or not np.all(np.isfinite(x)): raise ValueError("invalid coordinates")
    return x
def discover_curves(dataset_dir):
    out=[]
    for p in sorted(Path(dataset_dir).rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTENSIONS:
            try: out.append((p,load_curve(p)))
            except Exception: pass
    return out

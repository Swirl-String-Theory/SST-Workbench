from __future__ import annotations
from pathlib import Path
import hashlib, json, math, re
import numpy as np

SUPPORTED_EXTENSIONS = {".txt", ".xyz", ".dat", ".csv", ".npy", ".npz", ".json", ".vect"}

def track_trefoil(
    n: int = 512,
    baseR: float = 4.08248290463863,
    bulge_R: float = 2.2,
    z_weave: float = 3.0,
    z0: float = 0.0,
    p: int = 2,
    q: int = 3,
) -> np.ndarray:
    t = np.linspace(0.0, 2.0*np.pi, n, endpoint=False)
    r = baseR + bulge_R*np.cos(q*t)
    x = r*np.cos(p*t)
    y = r*np.sin(p*t)
    z = z_weave*np.sin(q*t) + z0
    return np.column_stack([x,y,z]).astype(np.float64)

def classic_trefoil(n: int = 512) -> np.ndarray:
    t = np.linspace(0.0, 2.0*np.pi, n, endpoint=False)
    x = np.sin(t) + 2.0*np.sin(2.0*t)
    y = np.cos(t) - 2.0*np.cos(2.0*t)
    z = -np.sin(3.0*t)
    return np.column_stack([x,y,z]).astype(np.float64)

def resample_closed(points: np.ndarray, n: int) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 4:
        raise ValueError("Expected Nx3 centerline with N>=4")
    if np.linalg.norm(p[0]-p[-1]) < 1e-12 * max(1.0, np.ptp(p, axis=0).max()):
        p = p[:-1]
    q = np.vstack([p, p[0]])
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    if np.any(seg <= 0):
        keep = np.r_[True, seg[:-1] > 0]
        p = p[keep]
        q = np.vstack([p, p[0]])
        seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.r_[0.0, np.cumsum(seg)]
    total = s[-1]
    target = np.linspace(0.0, total, n, endpoint=False)
    out = np.empty((n,3), dtype=float)
    for k in range(3):
        out[:,k] = np.interp(target, s, q[:,k])
    return out

def _native():
    try:
        import sst_qgi_native
        return sst_qgi_native
    except Exception:
        return None

def polyline_length(points: np.ndarray) -> float:
    native = _native()
    a = np.ascontiguousarray(points, dtype=float)
    if native is not None:
        return float(native.polyline_length(a))
    q = np.vstack([a, a[0]])
    return float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum())

def min_nonlocal_distance(points: np.ndarray, exclude_neighbors: int = 4) -> float:
    a = np.ascontiguousarray(points, dtype=float)
    native = _native()
    if native is not None:
        return float(native.min_nonlocal_distance(a, int(exclude_neighbors)))
    n = len(a)
    best = math.inf
    for i in range(n):
        d = a[i+1:] - a[i]
        if len(d) == 0: continue
        idx = np.arange(i+1,n)
        sep = idx-i
        cyc = np.minimum(sep, n-sep)
        mask = cyc > exclude_neighbors
        if np.any(mask):
            best = min(best, float(np.linalg.norm(d[mask],axis=1).min()))
    return best

def curvature_stats(points: np.ndarray) -> dict:
    a = np.ascontiguousarray(points, dtype=float)
    native = _native()
    if native is not None:
        d = native.curvature_stats(a)
        return {k: float(v) for k,v in d.items()}
    prev = np.roll(a,1,axis=0)
    nxt = np.roll(a,-1,axis=0)
    v1 = a-prev
    v2 = nxt-a
    l1 = np.linalg.norm(v1,axis=1)
    l2 = np.linalg.norm(v2,axis=1)
    t1 = v1 / l1[:,None]
    t2 = v2 / l2[:,None]
    ds = 0.5*(l1+l2)
    k = np.linalg.norm(t2-t1,axis=1)/ds
    return {"mean":float(k.mean()),"rms":float(np.sqrt(np.mean(k*k))),"max":float(k.max())}

def segment_cv(points: np.ndarray) -> float:
    q=np.vstack([points,points[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1)
    return float(ds.std()/ds.mean())

def geometry_sha256(points: np.ndarray) -> str:
    a = np.ascontiguousarray(points, dtype="<f8")
    return hashlib.sha256(a.tobytes()).hexdigest()

def descriptors(points: np.ndarray, min_distance_points: int = 256) -> dict:
    p = np.asarray(points, dtype=float)
    ps = resample_closed(p, min(len(p), min_distance_points))
    c = curvature_stats(p)
    dmin = min_nonlocal_distance(ps, exclude_neighbors=4)
    minrad = (1.0 / c["max"]) if c["max"] > 0 else float("inf")
    thickness_radius_proxy = min(minrad, 0.5 * dmin)
    return {
        "n_points": int(len(p)),
        "length": polyline_length(p),
        "segment_cv": segment_cv(p),
        "curvature_mean": c["mean"],
        "curvature_rms": c["rms"],
        "curvature_max": c["max"],
        "minrad_proxy": minrad,
        "min_nonlocal_distance_proxy": dmin,
        "thickness_radius_proxy": thickness_radius_proxy,
        "geometry_sha256": geometry_sha256(p),
    }

def _load_vect(path: Path) -> np.ndarray:
    # Minimal KnotPlot/Geomview VECT reader: one polyline component is sufficient here.
    text = path.read_text(encoding="utf-8", errors="ignore")
    toks = text.replace("\n"," ").split()
    try:
        idx = next(i for i,t in enumerate(toks) if t.upper()=="VECT")
    except StopIteration:
        idx = -1
    nums=[]
    for t in toks[idx+1:]:
        try: nums.append(float(t))
        except ValueError: pass
    if len(nums) < 10:
        raise ValueError("VECT parse failed")
    ncomp, nvert, _ = map(int, nums[:3])
    if ncomp < 1 or nvert < 4:
        raise ValueError("Invalid VECT counts")
    pos=3
    counts=[int(nums[pos+i]) for i in range(ncomp)]
    pos += ncomp
    pos += ncomp  # color counts
    nv=abs(counts[0])
    coords=np.array(nums[pos:pos+3*nv],dtype=float).reshape(-1,3)
    return coords

def load_points(path: Path) -> np.ndarray:
    path=Path(path)
    ext=path.suffix.lower()
    if ext==".npy":
        a=np.load(path, allow_pickle=False)
    elif ext==".npz":
        z=np.load(path, allow_pickle=False)
        key="points" if "points" in z else list(z.keys())[0]
        a=z[key]
    elif ext==".json":
        obj=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj,dict):
            for key in ("points","centerline","xyz","vertices"):
                if key in obj:
                    obj=obj[key]; break
        a=np.asarray(obj,dtype=float)
    elif ext==".vect":
        a=_load_vect(path)
    else:
        rows=[]
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip() or line.lstrip().startswith(("#",";","//")):
                continue
            vals=re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", line)
            if len(vals)>=3:
                rows.append([float(vals[0]),float(vals[1]),float(vals[2])])
        a=np.asarray(rows,dtype=float)
    if a.ndim!=2 or a.shape[1] < 3 or len(a)<4:
        raise ValueError(f"Cannot interpret centerline: {path}")
    return np.asarray(a[:,:3],dtype=float)

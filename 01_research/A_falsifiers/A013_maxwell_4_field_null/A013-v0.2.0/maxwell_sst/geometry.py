from __future__ import annotations
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
import numpy as np

SUPPORTED = {'.txt', '.csv', '.npy', '.npz', '.vect'}

@dataclass
class CurveSet:
    path: Path
    components: list[np.ndarray]
    metrics: dict
    alias: dict

    @property
    def id(self) -> str:
        stem = self.path.stem
        return stem[:-6] if stem.endswith('_final') else stem

    @property
    def component_count(self) -> int:
        return len(self.components)

def close_curve(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 3:
        raise ValueError("curve must have shape (N,3), N>=3")
    if np.linalg.norm(p[0] - p[-1]) < 1e-12:
        p = p[:-1]
    return p

def segments(points: np.ndarray):
    p = close_curve(points)
    q = np.roll(p, -1, axis=0)
    dl = q - p
    mid = 0.5 * (p + q)
    return p, q, dl, mid

def curve_length(points: np.ndarray) -> float:
    p = close_curve(points)
    return float(np.linalg.norm(np.roll(p, -1, axis=0)-p, axis=1).sum())

def resample_closed(points: np.ndarray, n: int) -> np.ndarray:
    p = close_curve(points)
    q = np.vstack([p, p[0]])
    ds = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(ds)])
    L = s[-1]
    if L <= 0:
        raise ValueError("zero-length curve")
    target = np.linspace(0.0, L, int(n)+1)[:-1]
    return np.column_stack([np.interp(target, s, q[:,k]) for k in range(3)])

def recenter(points: np.ndarray) -> np.ndarray:
    p = close_curve(points)
    return p - p.mean(axis=0)

def recenter_set(components: list[np.ndarray]) -> list[np.ndarray]:
    allp = np.vstack([close_curve(c) for c in components])
    ctr = allp.mean(axis=0)
    return [close_curve(c)-ctr for c in components]

def rescale_to_length(points: np.ndarray, target_length: float) -> np.ndarray:
    p = recenter(points)
    L = curve_length(p)
    return p * (target_length / L)

def trefoil(n: int = 400, scale: float = 1.0) -> np.ndarray:
    t = np.linspace(0.0, 2*np.pi, n, endpoint=False)
    x = (2.0 + np.cos(3*t))*np.cos(2*t)
    y = (2.0 + np.cos(3*t))*np.sin(2*t)
    z = np.sin(3*t)
    return scale*np.column_stack([x,y,z])

def ring(n: int = 400, radius: float = 1.0) -> np.ndarray:
    t = np.linspace(0.0, 2*np.pi, n, endpoint=False)
    return radius*np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])

def local_frame(points: np.ndarray, index: int = 0):
    p = close_curve(points); n = len(p); i = index % n
    tangent = p[(i+1)%n]-p[(i-1)%n]
    tangent /= np.linalg.norm(tangent)
    axis = np.array([0.0,0.0,1.0])
    if abs(np.dot(axis,tangent)) > 0.9: axis = np.array([0.0,1.0,0.0])
    e1 = np.cross(tangent, axis); e1 /= np.linalg.norm(e1)
    e2 = np.cross(tangent, e1); e2 /= np.linalg.norm(e2)
    return p[i], tangent, e1, e2

def meridian(points: np.ndarray, radius: float, n: int = 256, index: int = 0, orientation: int = 1) -> np.ndarray:
    c, _, e1, e2 = local_frame(points, index)
    t = np.linspace(0.0, 2*np.pi, n, endpoint=False)
    if orientation < 0: t = -t
    return c + radius*(np.cos(t)[:,None]*e1 + np.sin(t)[:,None]*e2)

def load_vect(path: str | Path) -> list[np.ndarray]:
    lines = Path(path).read_text(errors='ignore').splitlines()
    lines = [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith('#')]
    if not lines or lines[0].upper() != 'VECT': raise ValueError('not a VECT file')
    nc, nv, _ = map(int, lines[1].split()[:3]); idx=2; counts=[]
    while len(counts)<nc:
        counts.extend(int(x) for x in lines[idx].split()); idx+=1
    counts=counts[:nc]; color_counts=[]
    while len(color_counts)<nc:
        color_counts.extend(int(x) for x in lines[idx].split()); idx+=1
    need=sum(abs(c) for c in counts); pts=[]
    for _ in range(need):
        pts.append([float(x) for x in lines[idx].split()[:3]]); idx+=1
    pts=np.asarray(pts,float); out=[]; j=0
    for c in counts:
        m=abs(c); out.append(close_curve(pts[j:j+m])); j+=m
    return out

def _sidecar(path: Path, suffix: str) -> dict:
    p = path.with_name(path.stem + suffix)
    if not p.exists() and path.stem.endswith('_final'):
        p = path.with_name(path.stem + suffix)
    try: return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    except Exception: return {}

def _metrics_path(path: Path) -> Path:
    # knot_3.1_final.txt -> knot_3.1_final.metrics.json
    return path.with_name(path.stem + '.metrics.json')

def _alias_path(path: Path) -> Path:
    return path.with_name(path.stem + '.alias.json')

def _infer_component_count_from_name(path: Path) -> int | None:
    s=path.stem
    m=re.match(r'torus_(\d+)\.(\d+)_final$',s)
    if m: return math.gcd(int(m.group(1)),int(m.group(2)))
    return None

def load_curve_set(path: str | Path) -> CurveSet:
    path=Path(path)
    metrics={}; alias={}
    mp=_metrics_path(path); ap=_alias_path(path)
    if mp.exists():
        try: metrics=json.loads(mp.read_text(encoding='utf-8'))
        except Exception: pass
    if ap.exists():
        try: alias=json.loads(ap.read_text(encoding='utf-8'))
        except Exception: pass
    if path.suffix.lower()=='.vect':
        comps=load_vect(path)
    elif path.suffix.lower()=='.npy':
        comps=[close_curve(np.load(path))]
    elif path.suffix.lower()=='.npz':
        z=np.load(path)
        if 'components' in z:
            comps=[close_curve(x) for x in z['components']]
        else:
            key='points' if 'points' in z else list(z.keys())[0]
            comps=[close_curve(z[key])]
    else:
        arr=np.loadtxt(path,delimiter=',' if path.suffix.lower()=='.csv' else None)
        arr=np.asarray(arr,float)[:,:3]
        counts=metrics.get('vertices_per_component')
        if counts:
            counts=[int(x) for x in counts]
            if sum(counts)!=len(arr):
                raise ValueError(f"{path.name}: vertices_per_component sums to {sum(counts)} but file has {len(arr)} rows")
            comps=[]; j=0
            for n in counts:
                comps.append(close_curve(arr[j:j+n])); j+=n
        else:
            cc=int(metrics.get('component_count') or _infer_component_count_from_name(path) or 1)
            if cc!=1:
                raise ValueError(f"{path.name}: multi-component file needs vertices_per_component in companion metrics JSON")
            comps=[close_curve(arr)]
    return CurveSet(path=path,components=comps,metrics=metrics,alias=alias)

def discover_final_curves(root: str | Path) -> list[Path]:
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(root)
    files=[]
    for p in root.iterdir():
        if p.is_file() and p.suffix.lower() in SUPPORTED and p.stem.endswith('_final'):
            files.append(p)
    return sorted(files,key=lambda p:p.name.lower())

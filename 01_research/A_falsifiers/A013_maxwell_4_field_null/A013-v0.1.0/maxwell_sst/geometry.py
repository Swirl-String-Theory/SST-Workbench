from __future__ import annotations
import numpy as np
from pathlib import Path


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
    return float(np.linalg.norm(np.roll(close_curve(points), -1, axis=0)-close_curve(points), axis=1).sum())


def resample_closed(points: np.ndarray, n: int) -> np.ndarray:
    p = close_curve(points)
    q = np.vstack([p, p[0]])
    ds = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(ds)])
    L = s[-1]
    if L <= 0:
        raise ValueError("zero-length curve")
    target = np.linspace(0.0, L, n+1)[:-1]
    out = np.column_stack([np.interp(target, s, q[:,k]) for k in range(3)])
    return out


def recenter(points: np.ndarray) -> np.ndarray:
    p = close_curve(points)
    return p - p.mean(axis=0)


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
    p = close_curve(points)
    n = len(p)
    i = index % n
    tangent = p[(i+1)%n]-p[(i-1)%n]
    tangent /= np.linalg.norm(tangent)
    axis = np.array([0.0,0.0,1.0])
    if abs(np.dot(axis,tangent)) > 0.9:
        axis = np.array([0.0,1.0,0.0])
    e1 = np.cross(tangent, axis)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(tangent, e1)
    e2 /= np.linalg.norm(e2)
    return p[i], tangent, e1, e2


def meridian(points: np.ndarray, radius: float, n: int = 256, index: int = 0, orientation: int = 1) -> np.ndarray:
    c, _, e1, e2 = local_frame(points, index)
    t = np.linspace(0.0, 2*np.pi, n, endpoint=False)
    if orientation < 0:
        t = -t
    return c + radius*(np.cos(t)[:,None]*e1 + np.sin(t)[:,None]*e2)


def load_vect(path: str | Path) -> list[np.ndarray]:
    lines = Path(path).read_text(errors='ignore').splitlines()
    lines = [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith('#')]
    if not lines or lines[0].upper() != 'VECT':
        raise ValueError('not a VECT file')
    hdr = lines[1].split()
    nc, nv, _ = map(int, hdr[:3])
    counts = []
    idx = 2
    while len(counts) < nc:
        counts.extend(int(x) for x in lines[idx].split())
        idx += 1
    counts = counts[:nc]
    # color counts follow, one per component (possibly split over lines)
    color_counts = []
    while len(color_counts) < nc:
        color_counts.extend(int(x) for x in lines[idx].split())
        idx += 1
    pts = []
    need = sum(abs(c) for c in counts)
    for _ in range(need):
        vals = [float(x) for x in lines[idx].split()[:3]]
        pts.append(vals); idx += 1
    pts = np.asarray(pts, float)
    out=[]; j=0
    for c in counts:
        m=abs(c); out.append(close_curve(pts[j:j+m])); j+=m
    return out


def load_curve(path: str | Path) -> np.ndarray:
    path = Path(path)
    suf = path.suffix.lower()
    if suf == '.vect':
        curves = load_vect(path)
        if len(curves) != 1:
            raise ValueError(f'{path} has {len(curves)} components; single-component command expected')
        return curves[0]
    if suf == '.npy':
        return close_curve(np.load(path))
    if suf == '.npz':
        z=np.load(path)
        key='points' if 'points' in z else list(z.keys())[0]
        return close_curve(z[key])
    arr=np.loadtxt(path, delimiter=',' if suf=='.csv' else None)
    return close_curve(arr[:,:3])

from __future__ import annotations
import math
from pathlib import Path
import numpy as np


def ring(n: int, radius: float = 1.0) -> np.ndarray:
    th = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return np.column_stack((radius*np.cos(th), radius*np.sin(th), np.zeros_like(th)))


def kelvin_ring(n: int, radius: float = 1.0, amplitude: float = 0.04,
                mode: int = 2, phase: float = 0.0, helical: bool = True) -> np.ndarray:
    th = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    ph = mode*th + phase
    rr = radius + amplitude*np.cos(ph)
    zz = amplitude*np.sin(ph) if helical else amplitude*np.cos(ph)
    return np.column_stack((rr*np.cos(th), rr*np.sin(th), zz))


def symmetric_ring_mode(n: int, radius: float = 1.0, amplitude: float = 0.04,
                        mode: int = 2, phase: float = 0.0) -> np.ndarray:
    """Standing ±m pair: no imposed helical handedness."""
    th = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    ph = mode*th + phase
    rr = radius + amplitude*np.cos(ph)
    zz = amplitude*np.cos(ph)
    return np.column_stack((rr*np.cos(th), rr*np.sin(th), zz))



def multi_kelvin_ring(n: int, radius: float = 1.0, components=None) -> np.ndarray:
    """Superposition of small helical Kelvin-like components [(m,A,phase),...]."""
    if components is None:
        components=[(2,0.05,0.1),(3,0.025,0.7),(5,0.015,0.2)]
    th=np.linspace(0.0,2.0*np.pi,n,endpoint=False)
    dr=np.zeros_like(th); zz=np.zeros_like(th)
    for m,a,ph in components:
        dr += float(a)*np.cos(int(m)*th+float(ph))
        zz += float(a)*np.sin(int(m)*th+float(ph))
    rr=radius+dr
    return np.column_stack((rr*np.cos(th),rr*np.sin(th),zz))

def torus_knot(n: int, p: int = 2, q: int = 3, major: float = 1.0,
               minor: float = 0.35, phase: float = 0.0) -> np.ndarray:
    t = np.linspace(0.0, 2.0*np.pi, n, endpoint=False)
    qt = q*t + phase
    pt = p*t
    rr = major + minor*np.cos(qt)
    return np.column_stack((rr*np.cos(pt), rr*np.sin(pt), minor*np.sin(qt)))


def center(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    return p - p.mean(axis=0, keepdims=True)


def rms_radius(points: np.ndarray) -> float:
    p = center(points)
    return float(np.sqrt(np.mean(np.sum(p*p, axis=1))))


def closed_arclength(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    p = np.asarray(points, dtype=float)
    d = np.roll(p, -1, axis=0) - p
    seg = np.linalg.norm(d, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    return s, seg, float(seg.sum())


def resample_closed(points: np.ndarray, n: int | None = None) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    if n is None:
        n = len(p)
    d = np.roll(p, -1, axis=0) - p
    seg = np.linalg.norm(d, axis=1)
    total = float(seg.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("degenerate closed curve")
    s0 = np.concatenate(([0.0], np.cumsum(seg)))
    pp = np.vstack((p, p[0]))
    target = np.linspace(0.0, total, n, endpoint=False)
    out = np.empty((n, 3), dtype=float)
    for k in range(3):
        out[:, k] = np.interp(target, s0, pp[:, k])
    return out


def parse_vect(path: str | Path) -> list[np.ndarray]:
    """Minimal KnotPlot/Geomview VECT parser; returns closed polylines only."""
    text = Path(path).read_text(errors="ignore").split()
    if not text:
        return []
    i = 0
    if text[i].upper() == "VECT":
        i += 1
    try:
        nvec = int(text[i]); nvert = int(text[i+1]); _ncolor = int(text[i+2]); i += 3
        counts = [int(text[i+j]) for j in range(nvec)]; i += nvec
        color_counts = [int(text[i+j]) for j in range(nvec)]; i += nvec
        coords = np.array([float(text[i+j]) for j in range(3*nvert)], dtype=float).reshape(-1,3)
    except Exception as exc:
        raise ValueError(f"Cannot parse VECT file {path}: {exc}") from exc
    curves: list[np.ndarray] = []
    off = 0
    for c in counts:
        m = abs(c)
        curve = coords[off:off+m].copy(); off += m
        if c < 0 and len(curve) >= 3:
            curves.append(curve)
    _ = color_counts
    return curves


def load_curve_file(path: str | Path) -> list[np.ndarray]:
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".vect":
        return parse_vect(path)
    if ext == ".npy":
        a = np.load(path)
        return [np.asarray(a, float)] if a.ndim == 2 else [np.asarray(x, float) for x in a]
    if ext in {".txt", ".csv", ".dat"}:
        a = np.loadtxt(path, delimiter="," if ext == ".csv" else None)
        if a.ndim == 2 and a.shape[1] >= 3:
            return [a[:, :3].astype(float)]
    return []


def discover_external_curves(root: str | Path | None, max_files: int = 8) -> list[tuple[str, np.ndarray]]:
    if not root:
        return []
    root = Path(root)
    if not root.exists():
        return []
    out: list[tuple[str, np.ndarray]] = []
    exts = {".vect", ".npy", ".txt", ".csv", ".dat"}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in exts:
            try:
                for j, curve in enumerate(load_curve_file(path)):
                    if len(curve) >= 16 and np.isfinite(curve).all():
                        out.append((f"{path.name}#{j}", curve))
                        if len(out) >= max_files:
                            return out
            except Exception:
                continue
    return out

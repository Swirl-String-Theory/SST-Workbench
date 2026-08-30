from __future__ import annotations
import re
from pathlib import Path
import numpy as np

_FLOAT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
SUPPORTED = {".txt", ".xyz", ".dat", ".csv", ".vect", ".npy"}


def _as_curve(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 3:
        raise ValueError(f"expected (N,3), got {a.shape}")
    if len(a) < 8:
        raise ValueError("need at least 8 vertices")
    if not np.isfinite(a).all():
        raise ValueError("non-finite coordinates")
    # Drop explicit duplicate closure and consecutive duplicates.
    if np.linalg.norm(a[0] - a[-1]) <= 1e-12 * max(1.0, np.ptp(a, axis=0).max()):
        a = a[:-1]
    keep = np.ones(len(a), dtype=bool)
    d = np.linalg.norm(np.roll(a, -1, axis=0) - a, axis=1)
    scale = max(1.0, np.ptp(a, axis=0).max())
    keep[1:] = d[:-1] > 1e-14 * scale
    a = a[keep]
    if len(a) < 8:
        raise ValueError("too many duplicate vertices")
    return np.ascontiguousarray(a)


def load_curve(path: str | Path) -> np.ndarray:
    path = Path(path)
    if path.suffix.lower() == ".npy":
        return _as_curve(np.load(path))
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    if lines and lines[0].strip().upper() == "VECT":
        # Minimal KnotPlot VECT reader: locate triples after the four header/count lines.
        triples = []
        for line in lines[4:]:
            vals = [float(x) for x in _FLOAT.findall(line)]
            if len(vals) == 3:
                triples.append(vals)
        if len(triples) >= 8:
            return _as_curve(np.array(triples, dtype=np.float64))
    triples = []
    for line in lines:
        vals = [float(x) for x in _FLOAT.findall(line)]
        if len(vals) == 3:
            triples.append(vals)
    if len(triples) < 8:
        raise ValueError(f"could not parse >=8 XYZ rows from {path}")
    return _as_curve(np.array(triples, dtype=np.float64))


def curve_length(x: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(x, -1, axis=0) - x, axis=1).sum())


def normalize_curve(x: np.ndarray) -> tuple[np.ndarray, dict]:
    x = _as_curve(x).copy()
    centroid = x.mean(axis=0)
    x -= centroid
    L = curve_length(x)
    if not np.isfinite(L) or L <= 0:
        raise ValueError("invalid curve length")
    x /= L
    return np.ascontiguousarray(x), {"input_centroid": centroid.tolist(), "input_length": L}


def resample_closed(x: np.ndarray, n: int) -> np.ndarray:
    x = _as_curve(x)
    if n < 16:
        raise ValueError("n must be >=16")
    nxt = np.roll(x, -1, axis=0)
    seg = np.linalg.norm(nxt - x, axis=1)
    if np.any(seg <= 0):
        raise ValueError("zero segment")
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    L = cum[-1]
    targets = np.linspace(0.0, L, n, endpoint=False)
    idx = np.searchsorted(cum, targets, side="right") - 1
    idx = np.clip(idx, 0, len(x) - 1)
    f = (targets - cum[idx]) / seg[idx]
    out = x[idx] + f[:, None] * (nxt[idx] - x[idx])
    return np.ascontiguousarray(out, dtype=np.float64)


def parity_mirror_physical(x: np.ndarray, axis: int = 0) -> np.ndarray:
    """True spatial-parity partner for a vortex filament with fixed +Gamma.

    Reflect one polar coordinate and reverse centerline orientation.  The reversal is
    essential: vorticity is axial, whereas the centerline tangent is polar.  This
    produces the parity-transformed vortex field without exposing a Gamma sign bit.
    """
    y = np.asarray(x, dtype=np.float64).copy()
    y[:, axis] *= -1.0
    # Preserve index 0 while reversing orientation: i -> (-i) mod N.
    # This keeps arclength correspondence exactly s -> 1-s on uniform grids.
    y = np.concatenate([y[:1], y[:0:-1]], axis=0).copy()
    y -= y.mean(axis=0)
    return np.ascontiguousarray(y)



def time_reverse_filament(x: np.ndarray) -> np.ndarray:
    """Reverse filament orientation at fixed +Gamma, representing v->-v, omega->-omega.

    Index 0 is preserved so uniform-grid correspondence is exactly s -> 1-s.
    """
    y=np.asarray(x,dtype=np.float64)
    y=np.concatenate([y[:1],y[:0:-1]],axis=0).copy()
    y-=y.mean(axis=0)
    return np.ascontiguousarray(y)

def frames(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=np.float64)
    dm = x - np.roll(x, 1, axis=0)
    dp = np.roll(x, -1, axis=0) - x
    t = dm + dp
    tn = np.linalg.norm(t, axis=1)
    t /= np.maximum(tn[:, None], 1e-30)

    dt = np.roll(t, -1, axis=0) - np.roll(t, 1, axis=0)
    nrm = np.linalg.norm(dt, axis=1)
    n = np.zeros_like(x)
    good = nrm > 1e-10
    n[good] = dt[good] / nrm[good, None]
    for i in np.where(~good)[0]:
        ref = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(ref, t[i])) > 0.85:
            ref = np.array([0.0, 1.0, 0.0])
        v = ref - np.dot(ref, t[i]) * t[i]
        n[i] = v / np.linalg.norm(v)
    b = np.cross(t, n)
    b /= np.maximum(np.linalg.norm(b, axis=1)[:, None], 1e-30)
    n = np.cross(b, t)
    n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-30)

    ds = 0.5 * (
        np.linalg.norm(np.roll(x, -1, axis=0) - x, axis=1)
        + np.linalg.norm(x - np.roll(x, 1, axis=0), axis=1)
    )
    curvature = np.linalg.norm(dt, axis=1) / np.maximum(
        np.linalg.norm(np.roll(x, -1, axis=0) - np.roll(x, 1, axis=0), axis=1), 1e-30
    )
    return np.ascontiguousarray(t), np.ascontiguousarray(n), np.ascontiguousarray(b), curvature


def ds_cv(x: np.ndarray) -> float:
    ds = np.linalg.norm(np.roll(x, -1, axis=0) - x, axis=1)
    return float(np.std(ds) / max(np.mean(ds), 1e-30))


def discover_curves(root: str | Path) -> list[Path]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(root)
    paths = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.lower().startswith("readme"):
            paths.append(p)
    return sorted(paths, key=lambda p: str(p).lower())

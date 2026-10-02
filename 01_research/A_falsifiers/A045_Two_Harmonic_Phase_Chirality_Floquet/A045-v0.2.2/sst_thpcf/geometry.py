from __future__ import annotations
from pathlib import Path
import numpy as np


def torus_trefoil(n: int = 96, R: float = 2.0, r: float = 1.0) -> np.ndarray:
    """Analytic dimensionless T(2,3) control seed, arclength-resampled."""
    if n % 3 != 0:
        raise ValueError("n must be divisible by 3 for the analytic C3 control")
    u = np.linspace(0.0, 2.0*np.pi, n, endpoint=False)
    x = (R + r*np.cos(3*u))*np.cos(2*u)
    y = (R + r*np.cos(3*u))*np.sin(2*u)
    z = r*np.sin(3*u)
    return resample_closed_curve(np.column_stack([x, y, z]), n)


def load_curve(path: str | Path) -> np.ndarray:
    p = Path(path)
    if p.suffix.lower() == ".npy":
        X = np.load(p, allow_pickle=False)
    else:
        X = np.loadtxt(p, dtype=float)
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[1] != 3 or len(X) < 12:
        raise ValueError(f"expected Nx3 centerline with N>=12, got {X.shape}")
    if not np.isfinite(X).all():
        raise ValueError("centerline contains non-finite values")
    return X


def resample_closed_curve(X: np.ndarray, n: int | None = None) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    if n is None:
        n = len(X)
    d = np.roll(X, -1, axis=0) - X
    seg = np.linalg.norm(d, axis=1)
    if np.any(seg <= 0):
        raise ValueError("curve has zero-length segment")
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    Xc = np.vstack([X, X[0]])
    target = np.linspace(0.0, total, int(n), endpoint=False)
    out = np.empty((int(n), 3), dtype=float)
    for k in range(3):
        out[:, k] = np.interp(target, s, Xc[:, k])
    return out


def centered(X: np.ndarray) -> np.ndarray:
    return np.asarray(X, float) - np.mean(X, axis=0, keepdims=True)


def normalize_rms_radius(X: np.ndarray) -> np.ndarray:
    Xc = centered(X)
    rr = float(np.sqrt(np.mean(np.sum(Xc*Xc, axis=1))))
    if rr <= 0:
        raise ValueError("degenerate centerline")
    return Xc / rr


def prepare_curve(X: np.ndarray, n: int) -> np.ndarray:
    return normalize_rms_radius(resample_closed_curve(X, n))


def rz(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def c3_geometry_residual(X: np.ndarray) -> float:
    """Descriptor only in v0.2.2; not a seed-admission gate."""
    Xc = centered(X)
    n = len(Xc)
    if n % 3:
        return float("nan")
    lhs = np.roll(Xc, -n//3, axis=0)
    rhs = Xc @ rz(-2.0*np.pi/3.0).T
    return float(np.linalg.norm(lhs-rhs)/(np.linalg.norm(Xc)+1e-30))


def length(X: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.roll(X, -1, axis=0)-X, axis=1)))


def segment_stats(X: np.ndarray) -> tuple[float, float]:
    d = np.linalg.norm(np.roll(X, -1, axis=0)-X, axis=1)
    return float(np.mean(d)), float(np.std(d)/(np.mean(d)+1e-30))


def curvature_stats(X: np.ndarray) -> tuple[float, float]:
    X = np.asarray(X, float)
    xp = np.roll(X, -1, axis=0)
    xm = np.roll(X, 1, axis=0)
    ds = length(X)/len(X)
    Xs = (xp-xm)/(2.0*ds)
    Xss = (xp - 2.0*X + xm)/(ds*ds)
    num = np.linalg.norm(np.cross(Xs, Xss), axis=1)
    den = np.linalg.norm(Xs, axis=1)**3 + 1e-30
    k = num/den
    return float(np.mean(k)), float(np.sqrt(np.mean(k*k)))


def min_nonlocal_distance(X: np.ndarray, exclude: int = 3) -> float:
    X = np.asarray(X, float)
    n = len(X)
    best = np.inf
    for i in range(n):
        for j in range(i+1, n):
            sep = min((j-i) % n, (i-j) % n)
            if sep <= exclude:
                continue
            best = min(best, float(np.linalg.norm(X[i]-X[j])))
    return float(best)

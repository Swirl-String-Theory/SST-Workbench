from __future__ import annotations
import numpy as np


def polygon_length(points: np.ndarray) -> float:
    p = np.asarray(points, dtype=float)
    return float(np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1).sum())


def resample_closed(points: np.ndarray, n: int) -> np.ndarray:
    p = np.asarray(points, dtype=float)
    seg = np.roll(p, -1, axis=0) - p
    ds = np.linalg.norm(seg, axis=1)
    if np.any(ds <= 0):
        raise ValueError("Curve contains duplicate consecutive points")
    cumulative = np.concatenate(([0.0], np.cumsum(ds)))
    total = cumulative[-1]
    target = np.linspace(0.0, total, int(n), endpoint=False)
    ext = np.vstack((p, p[0]))
    out = np.empty((int(n), 3), dtype=float)
    idx = np.searchsorted(cumulative, target, side="right") - 1
    idx = np.clip(idx, 0, len(p) - 1)
    local = (target - cumulative[idx]) / ds[idx]
    out[:] = (1.0 - local)[:, None] * ext[idx] + local[:, None] * ext[idx + 1]
    return np.ascontiguousarray(out)


def _rodrigues(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return v*c + np.cross(axis, v)*s + axis*np.dot(axis, v)*(1.0-c)


def bishop_frame(points: np.ndarray, phase: float = 0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Closed discrete parallel-transport (Bishop) frame.

    A closure mismatch is distributed uniformly around the loop. `phase` rotates the
    material frame about the tangent and is exposed explicitly as a robustness knob.
    """
    p = np.asarray(points, dtype=float)
    chord = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    t = chord / np.linalg.norm(chord, axis=1)[:, None]
    axes = np.eye(3)
    axis0 = axes[np.argmin(np.abs(axes @ t[0]))]
    n0 = axis0 - np.dot(axis0, t[0])*t[0]
    n0 /= np.linalg.norm(n0)
    n = np.empty_like(p)
    n[0] = n0
    for i in range(1, len(p)):
        ta, tb = t[i-1], t[i]
        ax = np.cross(ta, tb)
        sn = np.linalg.norm(ax)
        cs = float(np.clip(np.dot(ta, tb), -1.0, 1.0))
        ni = n[i-1]
        if sn > 1e-14:
            ni = _rodrigues(ni, ax/sn, float(np.arctan2(sn, cs)))
        ni -= np.dot(ni, tb)*tb
        ni /= np.linalg.norm(ni)
        n[i] = ni
    # transport final normal over the closing tangent step and measure holonomy mismatch
    ta, tb = t[-1], t[0]
    ax = np.cross(ta, tb); sn = np.linalg.norm(ax); cs = float(np.clip(np.dot(ta,tb),-1.0,1.0))
    nc = n[-1].copy()
    if sn > 1e-14:
        nc = _rodrigues(nc, ax/sn, float(np.arctan2(sn, cs)))
    nc -= np.dot(nc, tb)*tb; nc /= np.linalg.norm(nc)
    closure_angle = float(np.arctan2(np.dot(tb, np.cross(nc, n0)), np.dot(nc, n0)))
    # distribute closure and requested material-frame phase
    for i in range(len(p)):
        ang = closure_angle * (i/len(p)) + phase
        n[i] = _rodrigues(n[i], t[i], ang)
        n[i] -= np.dot(n[i], t[i])*t[i]
        n[i] /= np.linalg.norm(n[i])
    b = np.cross(t, n); b /= np.linalg.norm(b, axis=1)[:, None]
    return t, n, b


def make_counter_channels(centerline: np.ndarray, offset: float, phase: float = 0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if offset <= 0:
        raise ValueError("offset must be > 0")
    t, n, _ = bishop_frame(centerline, phase=phase)
    plus = np.ascontiguousarray(centerline + offset*n)
    minus = np.ascontiguousarray(centerline - offset*n)
    return plus, minus, t, n


def rigid_rotation_matrix() -> np.ndarray:
    a = 0.731; b = -0.417
    ca, sa = np.cos(a), np.sin(a); cb, sb = np.cos(b), np.sin(b)
    rz = np.array([[ca,-sa,0.0],[sa,ca,0.0],[0.0,0.0,1.0]])
    rx = np.array([[1.0,0.0,0.0],[0.0,cb,-sb],[0.0,sb,cb]])
    return rz @ rx


def rigid_transform(points: np.ndarray) -> np.ndarray:
    R = rigid_rotation_matrix()
    return np.asarray(points) @ R.T + np.array([0.31,-0.27,0.19])

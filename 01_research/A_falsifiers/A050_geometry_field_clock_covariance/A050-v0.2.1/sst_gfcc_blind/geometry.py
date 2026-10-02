import numpy as np

def _center_scale(p):
    p = np.asarray(p, dtype=float)
    p = p - p.mean(axis=0, keepdims=True)
    r = np.sqrt(np.mean(np.sum(p*p, axis=1)))
    if not np.isfinite(r) or r <= 0:
        raise ValueError("degenerate curve")
    return p / r

def resample_closed(points, n=None):
    p = np.asarray(points, dtype=float)
    if n is None:
        n = len(p)
    q = np.vstack([p, p[0]])
    ds = np.linalg.norm(np.diff(q, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(ds)])
    if s[-1] <= 0:
        raise ValueError("zero-length curve")
    targets = np.linspace(0.0, s[-1], n + 1)[:-1]
    out = np.empty((n, 3), float)
    for j in range(3):
        vals = np.concatenate([p[:, j], p[:1, j]])
        out[:, j] = np.interp(targets, s, vals)
    return out

def make_curve(code, n=64, seed=0):
    t = np.linspace(0.0, 2.0*np.pi, n, endpoint=False)
    if code == "G0001":
        p = np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])
    elif code == "G0002":
        p = np.column_stack([
            (2.0 + np.cos(3.0*t))*np.cos(2.0*t),
            (2.0 + np.cos(3.0*t))*np.sin(2.0*t),
            np.sin(3.0*t),
        ])
    elif code == "G0003":
        p = np.column_stack([
            (2.0 + np.cos(2.0*t))*np.cos(3.0*t),
            (2.0 + np.cos(2.0*t))*np.sin(3.0*t),
            np.sin(4.0*t),
        ])
    elif code == "G0004":
        rng = np.random.default_rng(seed + 4004)
        p = np.column_stack([np.cos(t), np.sin(t), 0.2*np.sin(2*t)])
        for k in range(2, 6):
            amp = 0.18 / k
            phase = rng.uniform(0, 2*np.pi, size=3)
            p[:,0] += amp*np.cos(k*t + phase[0])
            p[:,1] += amp*np.sin(k*t + phase[1])
            p[:,2] += amp*np.sin((k+1)*t + phase[2])
    else:
        raise KeyError(code)
    return resample_closed(_center_scale(p), n)

def curve_metrics(points):
    p = np.asarray(points, float)
    d = np.roll(p, -1, axis=0) - p
    seg = np.linalg.norm(d, axis=1)
    return {
        "n": int(len(p)),
        "length": float(seg.sum()),
        "segment_cv": float(seg.std() / max(seg.mean(), 1e-15)),
        "rms_radius": float(np.sqrt(np.mean(np.sum((p-p.mean(0))**2, axis=1))))
    }

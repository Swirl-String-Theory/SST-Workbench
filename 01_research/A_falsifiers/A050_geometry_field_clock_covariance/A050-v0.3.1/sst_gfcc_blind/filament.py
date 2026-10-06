import numpy as np
from .geometry import resample_closed

try:
    from .native_ext import HAVE_NATIVE, filament_field as _native_field
except Exception:
    HAVE_NATIVE = False
    _native_field = None

def filament_field(eval_points, curve_points, core, chunk=4096, prefer_native=True):
    x = np.asarray(eval_points, dtype=float)
    p = np.asarray(curve_points, dtype=float)
    if prefer_native and HAVE_NATIVE:
        return np.asarray(_native_field(x, p, float(core)))
    q = np.roll(p, -1, axis=0)
    dl = q - p
    mid = 0.5*(p + q)
    out = np.zeros((len(x),3), dtype=float)
    c2 = float(core)**2
    factor = 1.0/(4.0*np.pi)
    for a in range(0, len(x), int(chunk)):
        xx = x[a:a+int(chunk)]
        r = xx[:,None,:] - mid[None,:,:]
        den = (np.sum(r*r, axis=2) + c2)**1.5
        cross = np.cross(dl[None,:,:], r)
        out[a:a+len(xx)] = factor*np.sum(cross/den[:,:,None], axis=1)
    return out

def evolve_curve(points, core, dt, steps, reparameterize_every=2, chunk=4096):
    p = np.asarray(points, float).copy()
    frames = [p.copy()]
    for step in range(1, int(steps)+1):
        v1 = filament_field(p, p, core, chunk=chunk, prefer_native=False)
        # Remove rigid translation; only shape dynamics are retained.
        v1 -= v1.mean(axis=0, keepdims=True)
        half = p + 0.5*dt*v1
        v2 = filament_field(half, half, core, chunk=chunk, prefer_native=False)
        v2 -= v2.mean(axis=0, keepdims=True)
        p = p + dt*v2
        p -= p.mean(axis=0, keepdims=True)
        if reparameterize_every and step % int(reparameterize_every) == 0:
            p = resample_closed(p, len(p))
        frames.append(p.copy())
    return frames

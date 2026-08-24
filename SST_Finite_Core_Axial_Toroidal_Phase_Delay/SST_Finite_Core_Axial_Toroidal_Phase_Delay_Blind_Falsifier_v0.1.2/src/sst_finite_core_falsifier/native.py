from __future__ import annotations
import numpy as np
try:
    from . import _native
except Exception:
    _native=None

def backend_name(): return 'cpp-pybind11' if _native is not None else 'python-fallback'

def curve_basic_stats(c):
    c=np.asarray(c,float)
    if _native is not None:return _native.curve_basic_stats(c)
    d=np.roll(c,-1,axis=0)-c; L=float(np.sum(np.linalg.norm(d,axis=1))); return {'length':L,'n_points':len(c)}

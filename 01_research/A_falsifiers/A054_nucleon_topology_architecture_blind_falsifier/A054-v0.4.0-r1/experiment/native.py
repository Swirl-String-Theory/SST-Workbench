from __future__ import annotations
import numpy as np
try:
    from . import _native
except Exception:
    _native=None

def available(): return _native is not None
def openmp_enabled(): return bool(_native is not None and _native.openmp_enabled())
def elastic_raw_native(curve):
    if _native is None: raise RuntimeError('native unavailable')
    return np.asarray(_native.elastic_raw(np.asarray(curve,float)),float)
def core_force_native(x,others,core,sr,sa,chi):
    if _native is None: raise RuntimeError('native unavailable')
    return np.asarray(_native.core_force(np.asarray(x,float),[np.asarray(y,float) for y in others],float(core),float(sr),float(sa),float(chi)),float)

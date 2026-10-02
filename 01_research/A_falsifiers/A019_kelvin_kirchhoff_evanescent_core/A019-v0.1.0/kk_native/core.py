from __future__ import annotations
import importlib
import numpy as np

_BACKEND=None; _NAME=None

def load_backend(require_native=False, force_python=False, force_build=False, build_verbose=False):
    global _BACKEND,_NAME
    if force_python:
        from . import fallback as fb
        return fb,fb.backend_info()
    if _BACKEND is not None and not force_build: return _BACKEND,_NAME
    if not force_build:
        try:
            mod=importlib.import_module('kk_native._native')
            _BACKEND=mod; _NAME=mod.backend_info(); return mod,_NAME
        except Exception:
            pass
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build,verbose=build_verbose,strict=require_native)
        mod=importlib.import_module('kk_native._native')
        _BACKEND=mod; _NAME=mod.backend_info(); return mod,_NAME
    except Exception:
        if require_native: raise
        from . import fallback as fb
        _BACKEND=fb; _NAME=fb.backend_info(); return fb,_NAME

def induced_velocity(curve, offsets, core_radius, circulation=1.0, threads=0, **kw):
    b,n=load_backend(**kw)
    return np.asarray(b.induced_velocity(np.ascontiguousarray(curve,float),list(map(int,offsets)),float(core_radius),float(circulation),int(threads))),n

def velocity_at_points(targets, curve, offsets, core_radius, circulation=1.0, threads=0, **kw):
    b,n=load_backend(**kw)
    return np.asarray(b.velocity_at_points(np.ascontiguousarray(targets,float),np.ascontiguousarray(curve,float),list(map(int,offsets)),float(core_radius),float(circulation),int(threads))),n

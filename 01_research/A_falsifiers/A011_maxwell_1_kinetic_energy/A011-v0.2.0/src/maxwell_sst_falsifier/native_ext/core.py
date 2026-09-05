from __future__ import annotations
import importlib, sys
from typing import Any
from . import fallback

_BACKEND=None
_BACKEND_NAME=None

def _load(force_python=False, force_build=False, verbose=False):
    global _BACKEND,_BACKEND_NAME
    if force_python:
        return fallback,"python"
    if _BACKEND is not None and not force_build:
        return _BACKEND,_BACKEND_NAME
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build,verbose=verbose)
        mod=importlib.import_module("maxwell_sst_falsifier.native_ext._native")
        _BACKEND,_BACKEND_NAME=mod,"cpp"
    except Exception as exc:
        if verbose: print(f"[1_MaxwellSST/native] using Python fallback: {exc}",file=sys.stderr)
        _BACKEND,_BACKEND_NAME=fallback,"python"
    return _BACKEND,_BACKEND_NAME

def backend_info(force_build=False,verbose=False)->dict[str,Any]:
    mod,name=_load(False,force_build,verbose)
    try: ver=str(mod.backend_version())
    except Exception: ver="unknown"
    return {"backend":name,"version":ver,"native":name=="cpp"}

def require_native(force_build=False,verbose=True):
    info=backend_info(force_build,verbose)
    if not info["native"]: raise RuntimeError("Native C++ backend required but unavailable. Run run_00_install.cmd and install MSVC C++ Build Tools/pybind11.")
    return info

def segment_lengths(points,closed=True,force_python=False):
    mod,_=_load(force_python); return mod.segment_lengths(points,closed)

def writhe_midpoint(points,closed=True,force_python=False):
    mod,_=_load(force_python); return float(mod.writhe_midpoint(points,closed))

def biot_savart_velocity(source,evaluation,gamma=1.0,core_radius=1e-3,source_closed=True,force_python=False):
    mod,_=_load(force_python); return mod.biot_savart_velocity(source,evaluation,float(gamma),float(core_radius),bool(source_closed))

def min_segment_distance(a,b,closed_a=True,closed_b=True,force_python=False):
    mod,_=_load(force_python); return float(mod.min_segment_distance(a,b,closed_a,closed_b))

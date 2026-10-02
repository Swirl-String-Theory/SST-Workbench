from __future__ import annotations
import os
import numpy as np
from . import fallback

_BACKEND=None
_NATIVE=None


def _load(force_python=False,skip_build=False,force_build=False):
    global _BACKEND,_NATIVE
    if force_python:
        _BACKEND="python"; _NATIVE=None; return
    if not skip_build:
        try:
            from .build_ext_if_needed import build
            build(force=force_build,strict=False,quiet=True)
        except Exception:
            pass
    try:
        from . import _native
        _NATIVE=_native; _BACKEND="cpp"
    except Exception:
        _NATIVE=None; _BACKEND="python"


def backend_name():
    if _BACKEND is None:
        _load(force_python=os.environ.get("SST_FORCE_PYTHON")=="1")
    return _BACKEND


def filament_velocity(eval_points,filament_points,component_offsets,gammas,core_radius=0.05,
                      force_python=False,skip_build=False,force_build=False):
    if force_python:
        return fallback.filament_velocity(eval_points,filament_points,component_offsets,gammas,core_radius)
    global _BACKEND
    if _BACKEND is None or force_build: _load(False,skip_build,force_build)
    if _NATIVE is not None:
        return _NATIVE.filament_velocity(eval_points,filament_points,component_offsets,gammas,float(core_radius))
    return fallback.filament_velocity(eval_points,filament_points,component_offsets,gammas,core_radius)


def biot_savart(points,component_offsets,gamma=1.0,core_radius=0.05,**kw):
    o=np.asarray(component_offsets,dtype=np.int64)
    g=np.full(len(o)-1,float(gamma),dtype=np.float64)
    return filament_velocity(points,points,o,g,core_radius,**kw)


def evolve_frozen_background(points,component_offsets,gamma,knot_core_radius,
                             thread_points,thread_offsets,thread_gammas,thread_core_radius,
                             dt,steps,boost=None,force_python=False,skip_build=False,force_build=False):
    if force_python:
        return fallback.evolve_frozen_background(points,component_offsets,gamma,knot_core_radius,
            thread_points,thread_offsets,thread_gammas,thread_core_radius,dt,steps,boost)
    global _BACKEND
    if _BACKEND is None or force_build: _load(False,skip_build,force_build)
    U=np.zeros(3,dtype=np.float64) if boost is None else np.asarray(boost,dtype=np.float64)
    if _NATIVE is not None:
        return _NATIVE.evolve_frozen_background(points,component_offsets,float(gamma),float(knot_core_radius),
            thread_points,thread_offsets,thread_gammas,float(thread_core_radius),float(dt),int(steps),U)
    return fallback.evolve_frozen_background(points,component_offsets,gamma,knot_core_radius,
        thread_points,thread_offsets,thread_gammas,thread_core_radius,dt,steps,U)

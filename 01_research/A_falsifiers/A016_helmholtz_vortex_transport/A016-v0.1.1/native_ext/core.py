from __future__ import annotations
import importlib
import numpy as np
from .build_ext_if_needed import build_if_needed
_backend=None

def _load(force_build=False,verbose=False):
    global _backend
    if _backend is not None:return _backend
    try:_backend=importlib.import_module('native_ext._native');return _backend
    except Exception:pass
    if build_if_needed(force=force_build,verbose=verbose):
        importlib.invalidate_caches()
        try:_backend=importlib.import_module('native_ext._native');return _backend
        except Exception:pass
    return None

def backend_info(force_build=False):
    b=_load(force_build=force_build,verbose=force_build);return {'backend':'cpp' if b is not None else 'python','native_available':b is not None}

def _fn(name,force_python=False,force_build=False):
    if not force_python:
        b=_load(force_build=force_build,verbose=force_build)
        if b is not None:return getattr(b,name)
    from . import fallback
    return getattr(fallback,name)

def polyline_stats(points,closed=True,**kw):return _fn('polyline_stats',kw.get('force_python',False),kw.get('force_build',False))(np.asarray(points,float),bool(closed))
def interaction_energy(a,b,core_radius=0.0,threads=0,**kw):return float(_fn('interaction_energy',kw.get('force_python',False),kw.get('force_build',False))(np.asarray(a,float),np.asarray(b,float),float(core_radius),int(threads)))
def biot_savart(source,query,core_radius=0.0,kernel='softcore',threads=0,**kw):return np.asarray(_fn('biot_savart',kw.get('force_python',False),kw.get('force_build',False))(np.asarray(source,float),np.asarray(query,float),float(core_radius),str(kernel),int(threads)),float)
def gauss_linking(a,b,core_radius=0.0,threads=0,**kw):return float(_fn('gauss_linking',kw.get('force_python',False),kw.get('force_build',False))(np.asarray(a,float),np.asarray(b,float),float(core_radius),int(threads)))
def min_segment_distance(a,b,same_component=False,exclude_neighbors=2,threads=0,**kw):return float(_fn('min_segment_distance',kw.get('force_python',False),kw.get('force_build',False))(np.asarray(a,float),np.asarray(b,float),bool(same_component),int(exclude_neighbors),int(threads)))

def doubly_critical_distance(a,b,same_component=False,exclude_neighbors=3,cos_tol=0.20,threads=0,**kw):return float(_fn('doubly_critical_distance',kw.get('force_python',False),kw.get('force_build',False))(np.asarray(a,float),np.asarray(b,float),bool(same_component),int(exclude_neighbors),float(cos_tol),int(threads)))

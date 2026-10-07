from __future__ import annotations
from pathlib import Path
import importlib,sys
import numpy as np
from ..native_build import build_pybind
from ..backend_contract import BackendResult
from ..util import sha256_file


def load(instance_root: str|Path, *, force_build=False, require=True, verbose=False):
    root=Path(instance_root).resolve()
    br=build_pybind(root,force=force_build,verbose=verbose)
    if not br.success:
        if require: raise RuntimeError(f"strict C++ backend unavailable: {br.error}")
        return None,br
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    importlib.invalidate_caches()
    mod=importlib.import_module("native_ext._sst_native")
    return mod,br


def biot_savart(instance_root,points,queries,gamma=1.0,core=0.04,*,force_build=False,require=True):
    mod,br=load(instance_root,force_build=force_build,require=require)
    if mod is None: return None,BackendResult("cpp","python-fallback","float64","DEVELOPMENT",False,{"error":br.error})
    vel=np.asarray(mod.biot_savart(np.asarray(points,float),np.asarray(queries,float),float(gamma),float(core)))
    info=dict(mod.backend_info()) if hasattr(mod,"backend_info") else {}
    actual=info.get("backend",br.actual_backend)
    return vel,BackendResult("cpp",actual,"float64","CERTIFICATION",bool(np.isfinite(vel).all()),info,sha256_file(Path(instance_root)/"native/cpp/native.cpp"),br.fingerprint_sha256)

from __future__ import annotations
import os,sys
from typing import Any
from . import _config
from .fallback import python_backend_info

def _import_native():
    try:return __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}",fromlist=["*"])
    except Exception:return None

def _load_cpp_backend(*,force_build=False,build_verbose=False,skip_build=False):
    if skip_build:return _import_native()
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build,verbose=build_verbose)
        return _import_native()
    except Exception as exc:
        print(f"{_config.LOG_PREFIX} native load failed: {exc}",file=sys.stderr);return None

def native_info(mod:Any|None)->dict[str,Any]:
    if mod is None:
        d=python_backend_info();d.update({"native_loaded":False,"has_gpu":False});return d
    try:d=dict(mod.backend_info())
    except Exception:d={}
    d["native_loaded"]=True
    d["sycl_compiled"]=bool(getattr(mod,"sycl_compiled",d.get("sycl_compiled",False)))
    d["openmp_compiled"]=bool(getattr(mod,"openmp_compiled",d.get("openmp_compiled",False)))
    try:d["has_gpu"]=bool(mod.probe_sycl_gpu())
    except Exception:d["has_gpu"]=bool(d.get("is_gpu",False))
    return d

def resolve_backend(requested,info,*,allow_sycl_cpu=False,strict_sycl=False):
    req=(requested or os.environ.get("SST_BACKEND") or "auto").lower()
    if req=="python":return "python"
    has_native=bool(info.get("native_loaded"))
    sycl_gpu=bool(info.get("sycl_compiled") and (info.get("has_gpu") or info.get("is_gpu")))
    if req=="sycl":
        if sycl_gpu:return "sycl"
        if info.get("sycl_compiled") and allow_sycl_cpu:return "sycl"
        raise RuntimeError("SYCL GPU required but not visible. Use run_arc*.cmd after oneAPI setvars.")
    if req=="openmp":return "openmp" if has_native else "python"
    if sycl_gpu:return "sycl"
    if info.get("sycl_compiled") and allow_sycl_cpu:return "sycl"
    if has_native:return "openmp"
    return "python"

def run_smoke(backend="auto",allow_sycl_cpu=False,force_build=False):
    import numpy as np
    from .fallback import biot_savart as py_biot, filament_hamiltonian as py_h
    mod=_load_cpp_backend(force_build=force_build,build_verbose=force_build)
    info=native_info(mod);chosen=resolve_backend(backend,info,allow_sycl_cpu=allow_sycl_cpu)
    t=np.linspace(0,2*np.pi,64,endpoint=False);p=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    if mod is None or chosen=="python":
        v=py_biot(p,p,1.0,0.1);h=py_h(p,1.0,1.0,0.1)
    else:
        v=np.asarray(mod.biot_savart(p,p,1.0,0.1,chosen=="sycl",allow_sycl_cpu));h=float(mod.filament_hamiltonian(p,1.0,1.0,0.1,chosen=="sycl",allow_sycl_cpu))
    return {"ok":bool(np.isfinite(v).all() and np.isfinite(h)),"backend":chosen,"hamiltonian":float(h),**native_info(mod)}

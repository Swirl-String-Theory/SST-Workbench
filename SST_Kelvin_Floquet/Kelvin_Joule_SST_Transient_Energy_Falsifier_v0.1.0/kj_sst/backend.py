from __future__ import annotations
import time
import numpy as np
from native_ext import fallback
from native_ext.core import _load_cpp_backend, native_info, resolve_backend

_CACHE: dict[tuple[str,bool], tuple[object|None,str,dict]] = {}

def _chosen(requested: str, allow_sycl_cpu: bool, force_build: bool = False):
    key=(requested,bool(allow_sycl_cpu))
    if key in _CACHE and not force_build:
        return _CACHE[key]
    mod=_load_cpp_backend(force_build=force_build,build_verbose=force_build,skip_build=False)
    info=native_info(mod); chosen=resolve_backend(requested,info,allow_sycl_cpu=allow_sycl_cpu)
    _CACHE[key]=(mod,chosen,info)
    return _CACHE[key]

def biot_savart(points,queries,gamma,core,*,backend,allow_sycl_cpu=False,force_build=False):
    if backend=="python":
        t0=time.perf_counter();v=fallback.biot_savart(points,queries,gamma,core)
        return v,{"backend":"python","last_kernel_ms":1e3*(time.perf_counter()-t0),"is_gpu":False}
    mod,chosen,_=_chosen(backend,allow_sycl_cpu,force_build)
    if mod is None or chosen=="python": return biot_savart(points,queries,gamma,core,backend="python")
    v=np.asarray(mod.biot_savart(np.asarray(points,float),np.asarray(queries,float),float(gamma),float(core),chosen=="sycl",allow_sycl_cpu))
    info=native_info(mod);info["backend"]=chosen;return v,info

def hamiltonian(points,rho,gamma,core,*,backend,allow_sycl_cpu=False):
    if backend=="python":
        t0=time.perf_counter();h=fallback.filament_hamiltonian(points,rho,gamma,core)
        return float(h),{"backend":"python","last_kernel_ms":1e3*(time.perf_counter()-t0),"is_gpu":False}
    mod,chosen,_=_chosen(backend,allow_sycl_cpu)
    if mod is None or chosen=="python": return hamiltonian(points,rho,gamma,core,backend="python")
    h=float(mod.filament_hamiltonian(np.asarray(points,float),float(rho),float(gamma),float(core),chosen=="sycl",allow_sycl_cpu))
    info=native_info(mod);info["backend"]=chosen;return h,info

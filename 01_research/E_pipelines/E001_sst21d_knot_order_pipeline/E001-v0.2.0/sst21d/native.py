from __future__ import annotations
from pathlib import Path
import ctypes, os, subprocess, sys, shutil
import numpy as np

_LIB=None
_LAST_ERROR=None

def _root()->Path: return Path(__file__).resolve().parents[1]

def candidates()->list[Path]:
    b=_root()/'cpp'/'build'
    names=['sst21d_native.dll','libsst21d_native.so','libsst21d_native.dylib']
    return [p for n in names for p in [b/n,b/'Release'/n,b/'Debug'/n]]

def build_native(clean:bool=False)->Path:
    src=_root()/'cpp'; build=src/'build'
    if clean and build.exists(): shutil.rmtree(build)
    build.mkdir(parents=True,exist_ok=True)
    if shutil.which('cmake'):
        subprocess.run(['cmake','-S',str(src),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release'],check=True)
        subprocess.run(['cmake','--build',str(build),'--config','Release','--parallel'],check=True)
    else:
        cxx=os.environ.get('SST21D_CXX') or os.environ.get('CXX') or shutil.which('c++') or shutil.which('g++') or shutil.which('clang++') or shutil.which('cl')
        if not cxx: raise RuntimeError('CMake is absent and no C++ compiler was found. Set SST21D_CXX or CXX.')
        source=src/'src'/'sst21d_native.cpp'; inc=src/'include'
        if os.name=='nt' and Path(cxx).name.lower().startswith('cl'):
            out=build/'sst21d_native.dll'
            subprocess.run([cxx,'/nologo','/LD','/O2','/EHsc',f'/I{inc}',str(source),f'/Fe:{out}'],check=True,cwd=build)
        else:
            ext='.dll' if os.name=='nt' else ('.dylib' if sys.platform=='darwin' else '.so')
            out=build/(('' if os.name=='nt' else 'lib')+'sst21d_native'+ext)
            cmd=[cxx,'-std=c++17','-O3','-shared']
            if os.name!='nt': cmd.append('-fPIC')
            cmd += [str(source),'-I',str(inc),'-o',str(out)]
            subprocess.run(cmd,check=True)
    for p in candidates():
        if p.exists(): return p
    found=[p for p in build.rglob('*sst21d_native*') if p.is_file()]
    if found: return found[0]
    raise FileNotFoundError('native library was not produced')

def load(auto_build:bool=False):
    global _LIB, _LAST_ERROR
    if _LIB is not None: return _LIB
    p=next((p for p in candidates() if p.exists()),None)
    if p is None and auto_build:
        try: p=build_native()
        except Exception as exc:
            _LAST_ERROR=f'{type(exc).__name__}: {exc}'
            return None
    if p is None: return None
    lib=ctypes.CDLL(str(p))
    cdp=ctypes.POINTER(ctypes.c_double)
    lib.sst21d_native_version.restype=ctypes.c_int
    lib.sst21d_sampled_dcsd.argtypes=[cdp,ctypes.c_size_t,ctypes.c_int]
    lib.sst21d_sampled_dcsd.restype=ctypes.c_double
    lib.sst21d_inter_component_min_segment_distance.argtypes=[cdp,ctypes.c_size_t,cdp,ctypes.c_size_t]
    lib.sst21d_inter_component_min_segment_distance.restype=ctypes.c_double
    lib.sst21d_writhe_acn_midpoint.argtypes=[cdp,ctypes.c_size_t,ctypes.c_int,cdp,cdp]
    lib.sst21d_linking_acn_midpoint.argtypes=[cdp,ctypes.c_size_t,cdp,ctypes.c_size_t,cdp,cdp]
    _LIB=lib; return lib

def _arr(points): return np.ascontiguousarray(points,dtype=np.float64)

def sampled_dcsd(points,neighbor_skip=4,auto_build=False):
    a=_arr(points); lib=load(auto_build)
    if lib is None: return None
    return float(lib.sst21d_sampled_dcsd(a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),len(a),neighbor_skip))

def inter_min_distance(a,b,auto_build=False):
    a=_arr(a); b=_arr(b); lib=load(auto_build)
    if lib is None: return None
    return float(lib.sst21d_inter_component_min_segment_distance(a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),len(a),b.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),len(b)))

def writhe_acn(points,neighbor_skip=4,auto_build=False):
    a=_arr(points); lib=load(auto_build)
    if lib is None: return None
    wr=ctypes.c_double(); acn=ctypes.c_double()
    lib.sst21d_writhe_acn_midpoint(a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),len(a),neighbor_skip,ctypes.byref(wr),ctypes.byref(acn))
    return float(wr.value),float(acn.value)

def linking_acn(a,b,auto_build=False):
    a=_arr(a); b=_arr(b); lib=load(auto_build)
    if lib is None: return None
    lk=ctypes.c_double(); acn=ctypes.c_double()
    lib.sst21d_linking_acn_midpoint(a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),len(a),b.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),len(b),ctypes.byref(lk),ctypes.byref(acn))
    return float(lk.value),float(acn.value)

def last_error():
    return _LAST_ERROR

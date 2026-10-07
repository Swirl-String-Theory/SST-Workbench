from __future__ import annotations
from pathlib import Path
import json, math
import numpy as np
from .backends import parity
from .provenance import load_json_if_exists


def _segments(points):
    p=np.asarray(points,float)
    q=np.roll(p,-1,axis=0)
    return 0.5*(p+q), q-p


def _circle(n=256):
    u=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[np.cos(u),np.sin(u),np.zeros_like(u)]


def _trefoil(n=384):
    u=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+np.cos(3*u))*np.cos(2*u),(2+np.cos(3*u))*np.sin(2*u),np.sin(3*u)]


def _targets():
    return np.array([[0.1,0.2,0.35],[1.4,-0.3,0.8],[-0.7,0.55,1.2],[2.1,1.0,-0.4]],float)


def run_backend_selftest(root: Path, require_native=True, native_tol=1e-10):
    rows=[]
    for name,pts in (("circle",_circle()),("trefoil",_trefoil())):
        mids,dls=_segments(pts)
        r=parity(_targets(),mids,dls,1.0,0.04)
        passed=bool(r.get('available') and r.get('relative_l2') is not None and r['relative_l2']<=native_tol)
        if not r.get('available') and not require_native:
            status='SKIP'
        else:
            status='PASS' if passed else 'FAIL'
        rows.append({'case':name,'backend':'cpp-fp64','reference':'python-fp64','status':status,'tolerance':native_tol,**r})
    build=load_json_if_exists(Path(root)/'build/COMPILER_PROVENANCE.json')
    build_ok=bool(build and build.get('status')=='PASS')
    native_ok=all(r['status']=='PASS' for r in rows) if require_native else all(r['status'] in {'PASS','SKIP'} for r in rows)
    status='PASS' if native_ok and (build_ok or not require_native) else 'FAIL'
    dd32=load_json_if_exists(Path(root)/'build/DD32_BACKEND_SELFTEST.json')
    return {
      'schema':'SST-BACKEND-SELFTEST-2',
      'framework_version':'1.0.2.dev0',
      'status':status,
      'authority':{'python_fp64':'reference','cpp_fp64':'confirmatory','sycl_fp32':'screening-only','sycl_dd32':'experimental-screening-not-IEEE-FP64'},
      'thresholds':{'cpp_fp64_relative_l2_max':native_tol,'sycl_fp32_relative_l2_max':5e-4,'sycl_fp64_relative_l2_max':1e-9,
                    'sycl_dd32_relative_l2_max':1e-8,'sycl_dd32_min_fp32_improvement':20.0},
      'native_cases':rows,
      'compiler_provenance':build,
      'dd32_selftest':dd32,
    }

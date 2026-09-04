"""Pure-Python parity kernels. Heavy campaigns should use SYCL/OpenMP."""
from __future__ import annotations
import math
from typing import Any
import numpy as np
PI=math.pi

def vec_add(a,b): return np.asarray(a,float).reshape(-1)+np.asarray(b,float).reshape(-1)
def min_abs(x):
    x=np.asarray(x,float).reshape(-1); return float(np.min(np.abs(x))) if x.size else float("inf")

def biot_savart(points,queries,gamma=1.0,core=1.0):
    p=np.asarray(points,float); q=np.asarray(queries,float)
    if p.ndim!=2 or p.shape[1]!=3 or q.ndim!=2 or q.shape[1]!=3: raise ValueError("points/queries must be Nx3/Mx3")
    nxt=np.roll(p,-1,axis=0); dl=nxt-p; mid=.5*(p+nxt); scale=float(gamma)/(4*PI); a2=float(core)**2
    vel=np.zeros((len(q),3),float)
    for s in range(len(p)):
        r=q-mid[s]; d=np.sum(r*r,axis=1)+a2; cr=np.cross(np.broadcast_to(dl[s],r.shape),r)
        vel += scale*cr*(d**-1.5)[:,None]
    return vel

def filament_hamiltonian(points,rho,gamma,core):
    p=np.asarray(points,float); nxt=np.roll(p,-1,axis=0); dl=nxt-p; mid=.5*(p+nxt); a2=float(core)**2
    total=0.0
    for i in range(len(p)):
        r=mid[i]-mid
        total += float(np.sum((dl @ dl[i]) / np.sqrt(np.sum(r*r,axis=1)+a2)))
    return float(rho)*float(gamma)**2/(8*PI)*total

def python_backend_info(*,last_kernel_ms=0.0):
    return {"backend":"python","sycl_compiled":False,"openmp_compiled":False,"is_gpu":False,"device_name":"host-python","queue_reused":False,"last_kernel_ms":float(last_kernel_ms),"openmp_max_threads":1}

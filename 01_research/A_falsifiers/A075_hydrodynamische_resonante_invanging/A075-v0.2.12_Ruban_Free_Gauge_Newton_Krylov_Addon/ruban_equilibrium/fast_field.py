"""Optional Numba-accelerated O(N^2) quadrature; mathematically same as high_order.field.

The original A075-v0.2.9 source remains pinned untouched. Numba is optional;
SciPy/NumPy-only slow reference always remains available and is cross-checked.
"""
from __future__ import annotations
import numpy as np
from .core import DELTA,LOCAL_COEFFICIENT,derivative
from .high_order import validate
try:
    from numba import njit
except ImportError:
    njit=None

if njit is not None:
    @njit(cache=True)
    def _sum(src, dl, target, delta):
        n=target.shape[0]
        out=np.zeros((n,3),np.float64)
        dd=delta*delta
        for i in range(n):
            a=b=c=0.
            for j in range(n):
                rx=target[i,0]-src[j,0]
                ry=target[i,1]-src[j,1]
                rz=target[i,2]-src[j,2]
                inv=0.5/((rx*rx+ry*ry+rz*rz+dd)**1.5)
                a+=(dl[j,1]*rz-dl[j,2]*ry)*inv
                b+=(dl[j,2]*rx-dl[j,0]*rz)*inv
                c+=(dl[j,0]*ry-dl[j,1]*rx)*inv
            out[i,0]=a;out[i,1]=b;out[i,2]=c
        return out
else:
    _sum=None


def field(x,scheme='trapezoid',delta=DELTA,local_coefficient=LOCAL_COEFFICIENT):
    if _sum is None:raise ImportError('Install optional numba to enable accelerated quadrature')
    x,speed=validate(x)
    if scheme=='trapezoid':
        dl=derivative(x)*(2*np.pi/len(x)); src=x
    elif scheme=='midpoint':
        dl=np.roll(x,-1,axis=0)-x;src=x+dl/2
    else: raise ValueError('Invalid quadrature')
    out=_sum(src,dl,x,float(delta))
    d1=derivative(x);d2=derivative(x,2)
    out+=local_coefficient*np.cross(d1,d2)/(speed**3)[:,None]
    return out

"""CPU emulation of the framework's DD32/FP32x2 arithmetic.

This module exists for algorithmic regression tests. Production DD32 runs in the
external SYCL worker. DD32 is double-single arithmetic, not IEEE binary64.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class DS:
    hi: np.float32
    lo: np.float32
    @staticmethod
    def from_float(x: float) -> "DS": return DS(np.float32(x),np.float32(0.0))
    @staticmethod
    def from_double(x: float) -> "DS":
        h=np.float32(x); return DS(h,np.float32(float(x)-float(h)))
    def value(self) -> float: return float(self.hi)+float(self.lo)

def quick_two_sum(a,b):
    a=np.float32(a);b=np.float32(b);s=np.float32(a+b);e=np.float32(b-np.float32(s-a));return DS(s,e)
def two_sum(a,b):
    a=np.float32(a);b=np.float32(b);s=np.float32(a+b);bb=np.float32(s-a);e=np.float32(np.float32(a-np.float32(s-bb))+np.float32(b-bb));return DS(s,e)
def add(a:DS,b:DS)->DS:
    t=two_sum(a.hi,b.hi);e=np.float32(t.lo+np.float32(a.lo+b.lo));return quick_two_sum(t.hi,e)
def neg(a:DS)->DS:return DS(np.float32(-a.hi),np.float32(-a.lo))
def sub(a:DS,b:DS)->DS:return add(a,neg(b))
def mul(a:DS,b:DS)->DS:
    p=np.float32(a.hi*b.hi)
    # Product of two binary32 values is exactly representable in binary64, so
    # this CPU emulation recovers the same residual targeted by device FMA.
    e=np.float32(float(a.hi)*float(b.hi)-float(p))
    e=np.float32(e+np.float32(np.float32(a.hi*b.lo)+np.float32(a.lo*b.hi)))
    e=np.float32(e+np.float32(a.lo*b.lo))
    return quick_two_sum(p,e)
def div(a:DS,b:DS)->DS:
    q=DS.from_float(np.float32(a.hi/b.hi))
    for _ in range(3):
        r=sub(a,mul(b,q));qi=np.float32(np.float32(r.hi+r.lo)/b.hi);q=add(q,DS.from_float(qi))
    return q
def sqrt(a:DS)->DS:
    y=DS.from_float(np.float32(np.sqrt(np.float32(a.hi+a.lo))));two=DS.from_float(2.0)
    for _ in range(2):
        r=sub(a,mul(y,y));y=add(y,div(r,mul(two,y)))
    return y

def biot_savart(points,queries,gamma=1.0,core=0.04):
    p=np.asarray(points,dtype=np.float64);q=np.asarray(queries,dtype=np.float64)
    P=[[DS.from_double(v) for v in row] for row in p];Q=[[DS.from_double(v) for v in row] for row in q]
    scale=mul(DS.from_double(float(gamma)),DS.from_double(1.0/(4.0*math.pi)));c=DS.from_double(float(core));a2=mul(c,c);half=DS.from_float(0.5);one=DS.from_float(1.0)
    out=np.zeros((len(q),3),dtype=np.float64);n=len(P)
    for j,x in enumerate(Q):
        acc=[DS.from_float(0.0),DS.from_float(0.0),DS.from_float(0.0)]
        for s in range(n):
            t=(s+1)%n;a=P[s];b=P[t]
            dl=[sub(b[k],a[k]) for k in range(3)];mid=[mul(half,add(a[k],b[k])) for k in range(3)];r=[sub(x[k],mid[k]) for k in range(3)]
            D=add(add(mul(r[0],r[0]),mul(r[1],r[1])),add(mul(r[2],r[2]),a2));inv=div(one,mul(D,sqrt(D)))
            cross=[sub(mul(dl[1],r[2]),mul(dl[2],r[1])),sub(mul(dl[2],r[0]),mul(dl[0],r[2])),sub(mul(dl[0],r[1]),mul(dl[1],r[0]))]
            f=mul(scale,inv)
            for k in range(3):acc[k]=add(acc[k],mul(f,cross[k]))
        out[j]=[v.value() for v in acc]
    return out

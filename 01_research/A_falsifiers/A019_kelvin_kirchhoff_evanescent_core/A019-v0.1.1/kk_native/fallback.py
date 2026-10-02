from __future__ import annotations
import math
import numpy as np


def _segments(curve: np.ndarray, offsets: list[int]):
    mids=[]; dss=[]
    for lo,hi in zip(offsets[:-1], offsets[1:]):
        c=curve[lo:hi]
        q=np.roll(c,-1,axis=0)
        mids.append(0.5*(c+q)); dss.append(q-c)
    return np.vstack(mids), np.vstack(dss)


def velocity_at_points(targets, curve, offsets, core_radius, circulation=1.0, threads=0):
    targets=np.asarray(targets,float); curve=np.asarray(curve,float)
    mids,dss=_segments(curve,list(map(int,offsets)))
    out=np.empty_like(targets)
    pref=float(circulation)/(4.0*math.pi); a2=float(core_radius)**2
    for i,x in enumerate(targets):
        r=x[None,:]-mids
        den=(np.einsum('ij,ij->i',r,r)+a2)**1.5
        out[i]=pref*np.sum(np.cross(dss,r)/den[:,None],axis=0)
    return out


def induced_velocity(curve, offsets, core_radius, circulation=1.0, threads=0):
    return velocity_at_points(curve,curve,offsets,core_radius,circulation,threads)


def backend_info(): return "python-numpy-reference"

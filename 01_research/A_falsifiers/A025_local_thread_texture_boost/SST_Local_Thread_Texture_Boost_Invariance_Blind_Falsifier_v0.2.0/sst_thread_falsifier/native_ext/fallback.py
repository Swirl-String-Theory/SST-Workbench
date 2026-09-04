from __future__ import annotations
import numpy as np


def filament_velocity(eval_points, filament_points, component_offsets, gammas, core_radius=0.05):
    x=np.ascontiguousarray(eval_points,dtype=np.float64)
    p=np.ascontiguousarray(filament_points,dtype=np.float64)
    o=np.asarray(component_offsets,dtype=np.int64)
    g=np.asarray(gammas,dtype=np.float64)
    if len(g) != len(o)-1: raise ValueError("gammas must match filament components")
    out=np.zeros((len(x),3),dtype=np.float64)
    a2=float(core_radius)**2
    inv4pi=1.0/(4.0*np.pi)
    for ci,(lo,hi) in enumerate(zip(o[:-1],o[1:])):
        lo=int(lo); hi=int(hi)
        if hi-lo<3: continue
        q=p[lo:hi]
        qb=np.roll(q,-1,axis=0)
        dl=qb-q; mid=0.5*(q+qb)
        pref=float(g[ci])*inv4pi
        for i in range(len(x)):
            r=x[i][None,:]-mid
            den=(np.einsum('ij,ij->i',r,r)+a2)**1.5
            out[i]+=pref*np.sum(np.cross(dl,r)/den[:,None],axis=0)
    return out


def biot_savart(points, component_offsets, gamma=1.0, core_radius=0.05):
    o=np.asarray(component_offsets,dtype=np.int64)
    g=np.full(len(o)-1,float(gamma),dtype=np.float64)
    return filament_velocity(points,points,o,g,core_radius)


def evolve_frozen_background(points, component_offsets, gamma, knot_core_radius,
                             thread_points, thread_offsets, thread_gammas, thread_core_radius,
                             dt, steps, boost=None):
    """RK2 midpoint evolution of knot/link in a source-anchored frozen thread substrate.

    The complete substrate is advected by the same `boost` as the knot.  This makes
    common translation a covariance test rather than an externally fixed ether wind.
    """
    P=np.asarray(points,dtype=float).copy()
    O=np.asarray(component_offsets,dtype=np.int64)
    T0=np.asarray(thread_points,dtype=float)
    TO=np.asarray(thread_offsets,dtype=np.int64)
    TG=np.asarray(thread_gammas,dtype=float)
    U=np.zeros(3,float) if boost is None else np.asarray(boost,dtype=float)
    kg=np.full(len(O)-1,float(gamma),dtype=float)
    dt=float(dt); steps=int(steps)
    for s in range(steps):
        t=s*dt
        T=T0+t*U
        v1=filament_velocity(P,P,O,kg,knot_core_radius)
        if len(T0): v1+=filament_velocity(P,T,TO,TG,thread_core_radius)
        v1+=U
        Pm=P+0.5*dt*v1
        Tm=T0+(t+0.5*dt)*U
        v2=filament_velocity(Pm,Pm,O,kg,knot_core_radius)
        if len(T0): v2+=filament_velocity(Pm,Tm,TO,TG,thread_core_radius)
        v2+=U
        P=P+dt*v2
    return P

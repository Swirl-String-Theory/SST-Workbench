from __future__ import annotations
import numpy as np


def zero(points):
    return np.zeros_like(points,dtype=float)


def uniform_boost(points, direction, amplitude):
    d=np.asarray(direction,float); d/=np.linalg.norm(d)
    return np.repeat((float(amplitude)*d)[None,:],len(points),axis=0)


def point_source_radial(points, source, amplitude, rg, regularization=0.05):
    """Divergence-free point-source potential flow away from source.
    amplitude is the target velocity scale; mean advection is removed so only texture/tidal structure remains.
    """
    p=np.asarray(points,float); s=np.asarray(source,float)
    r=p-s[None,:]
    r2=np.sum(r*r,axis=1)+(regularization*rg)**2
    D=max(float(np.linalg.norm(np.mean(p,axis=0)-s)),1e-12)
    q=float(amplitude)*D*D
    v=q*r/(r2[:,None]**1.5)
    return v-np.mean(v,axis=0)


def director_affine(points, direction, amplitude, rg):
    """Conditional bridge: incompressible trace-free affine strain from T=nn-I/3."""
    p=np.asarray(points,float); c=np.mean(p,axis=0)
    n=np.asarray(direction,float); n/=np.linalg.norm(n)
    S=np.outer(n,n)-np.eye(3)/3.0
    return float(amplitude)*((p-c)@S.T)/max(float(rg),1e-15)

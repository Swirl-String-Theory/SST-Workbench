"""Geometric linking / regulated filament circulation benchmarks.

This is not a derived SST gauge connection or a physical stability solver.
All input geometry coordinates remain in original native KnotPlot units.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_points(path):
    p = Path(path)
    if p.suffix.lower() == '.npz':
        with np.load(p, allow_pickle=False) as z:
            names=sorted([n for n in z.files if n.startswith('component_')],key=lambda s:int(s.split('_')[-1]))
            if names:
                return [validate(z[n]) for n in names]
            if 'points' in z:
                return [validate(z['points'])]
            raise ValueError(f'Unsupported npz schema {p.name}: {z.files}')
    if p.suffix.lower() == '.npy':
        return [validate(np.load(p,allow_pickle=False))]
    if p.suffix.lower() in ('.json',):
        obj=json.loads(p.read_text(encoding='utf-8'))
        if isinstance(obj,dict):
            if 'components' in obj: return [validate(x) for x in obj['components']]
            if 'points' in obj: return [validate(obj['points'])]
        return [validate(obj)]
    if p.suffix.lower() in ('.txt','.xyz','.csv'):
        return [validate(np.loadtxt(p,delimiter=',' if p.suffix=='.csv' else None,comments='#'))]
    raise ValueError(f'Unsupported file format: {p}')


def validate(a):
    a=np.asarray(a,dtype=np.float64)
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<8 or not np.isfinite(a).all():
        raise ValueError('Expected finite N x 3 coordinates, N>=8')
    if np.linalg.norm(a[0]-a[-1]) < 1.e-12:
        a=a[:-1]   # remove repeated endpoint, periodic closure is implicit
    if len(a)<8 or np.min(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1))<1e-12:
        raise ValueError('Degenerate segment or duplicated coordinate')
    return a


def split_native(path, entries):
    comps=load_points(path)
    if len(comps)!=1: raise ValueError('Unexpected native components')
    a=comps[0]
    counts=[int(i['n_beads']) for i in entries]
    if sum(counts)!=len(a):
        raise ValueError('Native coordinate count mismatches PKLSA registry')
    return [validate(x) for x in np.split(a,np.cumsum(counts)[:-1])]


def gauss_link(a,b,order=4,core=0.):
    """Gauss linking integral for disjoint closed polygon curves.

    Tensor-product Gauss-Legendre quadrature for every pair of straight
    segments. core=0 gives Gauss linking; nonzero core is a *regulator* and
    is no longer a topological invariant. Positive normalized circulation
    equals linking number in the zero-core limit.
    """
    a,b=validate(a),validate(b)
    x=np.roll(a,-1,axis=0)-a
    y=np.roll(b,-1,axis=0)-b
    cross=np.cross(x[:,None,:],y[None,:,:])
    nodes,weights=np.polynomial.legendre.leggauss(order)
    nodes=(nodes+1)/2; weights=weights/2
    accum=0.
    for t,wt in zip(nodes,weights):
        p=a+t*x
        for u,wu in zip(nodes,weights):
            d=p[:,None,:]-(b+u*y)[None,:,:]
            d2=np.einsum('ijk,ijk->ij',d,d)+core**2
            if np.min(d2)<1e-20: raise ValueError('Coincident/intersecting geometry')
            accum+=wt*wu*np.sum(np.einsum('ijk,ijk->ij',cross,d)/d2**1.5)
    return float(accum/(4*np.pi))


def arclength_perimeter(a):
    a=validate(a)
    return float(np.sum(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)))


def meridian(a,n=96,radius_fraction=0.8):
    """Create a local meridional probe around one segment midpoint.
    This is a probe / designed positive control, not a knot identifier.
    """
    a=validate(a)
    p=a[0]; d=a[1]-a[0]; L=np.linalg.norm(d); T=d/L
    t=np.eye(3)[np.argmin(np.abs(T))]
    nvec=np.cross(T,t); nvec/=np.linalg.norm(nvec)
    bvec=np.cross(T,nvec)
    ctr=p+0.5*d
    theta=2*np.pi*np.arange(n)/n
    return ctr+radius_fraction*L*(np.cos(theta)[:,None]*nvec+np.sin(theta)[:,None]*bvec)


def interference_visibility(link,charge=0.5):
    """Assigned representation, NOT derived from vortex dynamics.

    q=1/2 maps an integer linking number to a Z2 sign.
    P=(1+cos(2*pi*q*Lk))/2. This is a reference toy model only.
    """
    phase=float(2*np.pi*charge*link)
    return float(0.5*(1+np.cos(phase))),phase


def hopf_pair(n=96):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return (np.column_stack((np.cos(t),np.sin(t),np.zeros_like(t))),
            np.column_stack((1+np.cos(t),np.zeros_like(t),np.sin(t))))


def unlink_pair(n=96):
    a,b=hopf_pair(n);return a,b+np.array([5.,0,0])


def rotation_x(phi):
    c,s=np.cos(phi),np.sin(phi)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]])

def polygon_pair_min_clearance(a,b):
    """Approximate minimum Euclidean distance between all polygon segment pairs.

    Uses a convergent box-constrained 2-variable quadratic minimization
    (clipped alternating projections); includes segment endpoints.
    """
    a,b=validate(a),validate(b)
    x=np.roll(a,-1,axis=0)-a
    y=np.roll(b,-1,axis=0)-b
    w=a[:,None,:]-b[None,:,:]
    aa=np.einsum('id,id->i',x,x)[:,None]
    bb=np.einsum('jd,jd->j',y,y)[None,:]
    ab=np.einsum('id,jd->ij',x,y)
    uw=np.einsum('ijd,id->ij',w,x)
    vw=np.einsum('ijd,jd->ij',w,y)
    den=aa*bb-ab**2
    s=np.clip(np.divide(ab*vw-bb*uw,den,out=np.zeros_like(den),where=den>1e-14*aa*bb),0,1)
    t=np.clip((vw+ab*s)/bb,0,1)
    for _ in range(24):
        s=np.clip((ab*t-uw)/aa,0,1)
        t=np.clip((vw+ab*s)/bb,0,1)
    diff=w+s[:,:,None]*x[:,None,:]-t[:,:,None]*y[None,:,:]
    return float(np.min(np.linalg.norm(diff,axis=-1)))

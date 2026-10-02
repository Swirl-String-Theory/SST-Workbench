from __future__ import annotations
import math, numpy as np
try:
    from scipy.interpolate import CubicSpline
except Exception:
    CubicSpline=None

def clean_closed(points):
    p=np.asarray(points,float)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<4: raise ValueError('expected Nx3, N>=4')
    if not np.isfinite(p).all(): raise ValueError('non-finite geometry')
    if np.linalg.norm(p[0]-p[-1]) < 1e-12*max(1.0,np.linalg.norm(p,axis=1).max()): p=p[:-1]
    # remove zero-length consecutive edges
    keep=np.ones(len(p),bool)
    d=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    keep &= d>max(1e-15,float(np.nanmax(d))*1e-14)
    p=p[keep]
    if len(p)<4: raise ValueError('degenerate geometry after duplicate removal')
    return p

def polygon_length(points):
    p=clean_closed(points); return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())

def normalize(points,target_length=1.0):
    p=clean_closed(points).copy(); p-=p.mean(axis=0); L=polygon_length(p)
    if L<=0: raise ValueError('zero length')
    return p*(float(target_length)/L)

def arclength_linear(points,n):
    p=clean_closed(points); q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1); s=np.concatenate([[0.0],np.cumsum(ds)])
    u=np.linspace(0,float(s[-1]),int(n),endpoint=False)
    return np.column_stack([np.interp(u,s,q[:,j]) for j in range(3)])

def periodic_spline(points):
    if CubicSpline is None: raise RuntimeError('scipy is required for periodic cubic qualification')
    p=clean_closed(points); q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1); s=np.concatenate([[0.0],np.cumsum(ds)])
    # zero-length edges were removed; still guard pathological input
    if np.any(np.diff(s)<=0): raise ValueError('non-increasing arc parameter')
    spl=[CubicSpline(s,q[:,j],bc_type='periodic') for j in range(3)]
    return s[-1], spl

def sample_spline(points,n):
    L0,spl=periodic_spline(points); u=np.linspace(0,L0,int(n),endpoint=False)
    r=np.column_stack([f(u) for f in spl])
    d1=np.column_stack([f(u,1) for f in spl])
    d2=np.column_stack([f(u,2) for f in spl])
    d3=np.column_stack([f(u,3) for f in spl])
    speed=np.linalg.norm(d1,axis=1)
    cr=np.cross(d1,d2); crn=np.linalg.norm(cr,axis=1)
    with np.errstate(divide='ignore',invalid='ignore'):
        kappa=crn/np.maximum(speed,1e-300)**3
        tau=np.einsum('ij,ij->i',cr,d3)/np.maximum(crn,1e-300)**2
    # quadrature in spline parameter
    length=float(L0*np.mean(speed))
    return {'points':r,'tangent_raw':d1,'kappa':kappa,'tau':tau,'length':length,'parameter_period':float(L0)}

def local_metrics(sample):
    k=np.asarray(sample['kappa']); t=np.asarray(sample['tau']); p=np.asarray(sample['points'])
    edge=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1); em=float(edge.mean())
    finite_k=k[np.isfinite(k)]; finite_t=t[np.isfinite(t)]
    return {
      'L':float(sample['length']),
      'kappa_max':float(np.max(finite_k)) if len(finite_k) else None,
      'kappa_rms':float(np.sqrt(np.mean(finite_k**2))) if len(finite_k) else None,
      'kappa_std':float(np.std(finite_k)) if len(finite_k) else None,
      'tau_rms':float(np.sqrt(np.mean(finite_t**2))) if len(finite_t) else None,
      'tau_std':float(np.std(finite_t)) if len(finite_t) else None,
      'edge_cv':float(edge.std()/em) if em>0 else None,
    }

def tangent_unit(d1):
    d=np.asarray(d1,float); n=np.linalg.norm(d,axis=1)
    return d/np.maximum(n[:,None],1e-300)

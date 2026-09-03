from __future__ import annotations
import math
import numpy as np
from .geometry import _closed, curve_length, resample_closed

try:
    from . import _sstknot_native as _native
except Exception:
    _native = None


def closure_error(points):
    p = _closed(points)
    d = np.linalg.norm(p[0]-p[-1])
    return float(d)


def segment_stats(points):
    p = _closed(points)
    ds = np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    return {
        'min': float(ds.min()), 'max': float(ds.max()), 'mean': float(ds.mean()),
        'cv': float(ds.std()/max(ds.mean(),1e-30))
    }


def curvature(points):
    p = _closed(points)
    # three-point circumcircle curvature; stable for near-uniform samples
    a = p - np.roll(p,1,axis=0)
    b = np.roll(p,-1,axis=0) - p
    c = np.roll(p,-1,axis=0) - np.roll(p,1,axis=0)
    cr = np.linalg.norm(np.cross(a,b),axis=1)
    den = np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)*np.linalg.norm(c,axis=1)
    return 2.0*cr/np.maximum(den,1e-30)


def _segseg_distance(p1, q1, p2, q2):
    """Shortest distance between two 3D line segments."""
    u=q1-p1; v=q2-p2; w=p1-p2
    a=float(np.dot(u,u)); b=float(np.dot(u,v)); c=float(np.dot(v,v)); d=float(np.dot(u,w)); e=float(np.dot(v,w))
    D=a*c-b*b; eps=1e-30
    sN=D; sD=D; tN=D; tD=D
    if D < eps:
        sN=0.0; sD=1.0; tN=e; tD=c
    else:
        sN=b*e-c*d; tN=a*e-b*d
        if sN < 0.0:
            sN=0.0; tN=e; tD=c
        elif sN > sD:
            sN=sD; tN=e+b; tD=c
    if tN < 0.0:
        tN=0.0
        if -d < 0.0: sN=0.0
        elif -d > a: sN=sD
        else: sN=-d; sD=a
    elif tN > tD:
        tN=tD
        if (-d+b) < 0.0: sN=0.0
        elif (-d+b) > a: sN=sD
        else: sN=(-d+b); sD=a
    sc=0.0 if abs(sN)<eps else sN/max(sD,eps)
    tc=0.0 if abs(tN)<eps else tN/max(tD,eps)
    dp=w+sc*u-tc*v
    return float(np.linalg.norm(dp))

def min_nonlocal_distance(points, skip: int = 8):
    """Minimum distance between non-neighboring polyline segments (not just vertices)."""
    p = _closed(points)
    if _native is not None:
        return float(_native.min_nonlocal_distance(p, int(skip)))
    n=len(p); best=float('inf')
    for i in range(n):
        i2=(i+1)%n
        for j in range(i+1,n):
            dcy=min((j-i)%n,(i-j)%n)
            if dcy <= skip: continue
            j2=(j+1)%n
            d=_segseg_distance(p[i],p[i2],p[j],p[j2])
            if d<best: best=d
    return best

def thickness_estimate(points, skip: int = 8):
    k=curvature(points)
    rho=float(1.0/max(float(k.max()),1e-30))
    d=min_nonlocal_distance(points,skip=skip)
    return min(rho,0.5*d), rho, d


def _midseg(points):
    p=_closed(points); q=np.roll(p,-1,axis=0)
    return 0.5*(p+q), q-p


def writhe(points):
    p=_closed(points)
    if _native is not None:
        return float(_native.writhe_midpoint(p))
    m,dl=_midseg(p); n=len(p); acc=0.0
    for i in range(n):
        r=m[i]-m
        num=np.einsum('ij,ij->i',np.cross(dl[i],dl),r)
        den=np.linalg.norm(r,axis=1)**3
        mask=np.ones(n,dtype=bool); mask[i]=False; mask[(i-1)%n]=False; mask[(i+1)%n]=False
        acc += np.sum(num[mask]/np.maximum(den[mask],1e-30))
    return float(acc/(4*math.pi))


def linking_number(a,b):
    a=_closed(a); b=_closed(b)
    if _native is not None:
        return float(_native.linking_midpoint(a,b))
    ma,dla=_midseg(a); mb,dlb=_midseg(b); acc=0.0
    for i in range(len(a)):
        r=ma[i]-mb
        num=np.einsum('ij,ij->i',np.cross(np.broadcast_to(dla[i],dlb.shape),dlb),r)
        den=np.linalg.norm(r,axis=1)**3
        acc += np.sum(num/np.maximum(den,1e-30))
    return float(acc/(4*math.pi))


def self_linking_report(centerline, offset_curve):
    """Călugăreanu-White diagnostic from a centerline and one disjoint ribbon/material edge.

    Returns approximate Lk, Wr and Tw=Lk-Wr. Lk should converge toward an integer for a valid closed framing.
    """
    wr=writhe(centerline)
    lk=linking_number(centerline,offset_curve)
    return {'linking':lk,'writhe':wr,'twist_from_Lk_minus_Wr':lk-wr,'linking_integer_residual':abs(lk-round(lk))}

def convergence_report(points, levels=(256,512,1024), skip_fraction=0.05):
    rows=[]
    for n in levels:
        p=resample_closed(points,n)
        skip=max(3,int(n*skip_fraction))
        thick,rho,d=thickness_estimate(p,skip)
        rows.append({
            'N':n,'length':curve_length(p),'writhe':writhe(p),
            'kappa_max':float(curvature(p).max()),'rho_min':rho,
            'min_nonlocal':d,'thickness_est':thick,'segment_cv':segment_stats(p)['cv']
        })
    if len(rows)>1:
        ref=rows[-1]
        for r in rows[:-1]:
            r['rel_length_vs_finest']=abs(r['length']-ref['length'])/max(abs(ref['length']),1e-30)
            r['abs_writhe_vs_finest']=abs(r['writhe']-ref['writhe'])
            r['rel_clearance_vs_finest']=abs(r['min_nonlocal']-ref['min_nonlocal'])/max(abs(ref['min_nonlocal']),1e-30)
        ref['rel_length_vs_finest']=0.0; ref['abs_writhe_vs_finest']=0.0; ref['rel_clearance_vs_finest']=0.0
    return rows


def qualify_seed(points, core_radius: float, n: int = 512, min_clearance_core: float = 2.2,
                 max_kappa_core: float = 0.35, max_segment_cv: float = 0.03,
                 skip_fraction: float = 0.05):
    p=resample_closed(points,n)
    skip=max(3,int(n*skip_fraction))
    k=curvature(p); d=min_nonlocal_distance(p,skip); thick,rho,_=thickness_estimate(p,skip)
    metrics={
        'N':n,'length':curve_length(p),'writhe':writhe(p),'kappa_max':float(k.max()),
        'rho_min':rho,'min_nonlocal':d,'thickness_est':thick,'segment_cv':segment_stats(p)['cv'],
        'clearance_over_core':d/max(core_radius,1e-30),
        'kappa_core_max':float(k.max()*core_radius),
        'thickness_over_core':thick/max(core_radius,1e-30),
    }
    gates={
        'uniform_sampling': metrics['segment_cv'] <= max_segment_cv,
        'clearance': metrics['clearance_over_core'] >= min_clearance_core,
        'curvature_core': metrics['kappa_core_max'] <= max_kappa_core,
        'tube_embeddability_proxy': metrics['thickness_over_core'] > 1.0,
    }
    return {'metrics':metrics,'gates':gates,'pass':all(gates.values())}


def linking_matrix(components):
    """Symmetric Gauss-linking matrix for a multi-component polygonal link.

    Diagonal entries are zero (self-linking requires a framing, not a single centerline).
    """
    comps=[_closed(c) for c in components]
    m=np.zeros((len(comps),len(comps)),float)
    for i in range(len(comps)):
        for j in range(i+1,len(comps)):
            m[i,j]=m[j,i]=linking_number(comps[i],comps[j])
    return m

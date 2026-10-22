"""Conservative local curvature repair for periodic knot polylines.

This is a geometric candidate, NOT a proof of ambient isotopy. High-turn corners
that cannot be improved within a small displacement budget are explicitly flagged.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree


def metrics(p):
    p=np.asarray(p,float)
    e=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    a=p-np.roll(p,1,axis=0);b=np.roll(p,-1,axis=0)-p
    angle=np.arccos(np.clip(np.sum(a*b,axis=1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)),-1,1))
    curvature=angle/(0.5*(np.roll(e,1)+e))
    return {'n':len(p),'length':float(e.sum()),'max_turn_rad':float(angle.max()),
      'max_curvature_per_coordinate':float(curvature.max()),'median_edge':float(np.median(e)),
      'min_edge_over_median':float(e.min()/np.median(e)),
      'max_edge_over_median':float(e.max()/np.median(e)),
      'closing_edge_over_median':float(e[-1]/np.median(e))}

def local_vertex_gap(p,skip=4):
    # Conservative screening number only: not equivalent to true segment clearance.
    p=np.asarray(p,float);n=len(p);tree=cKDTree(p)
    ids=tree.query(p,k=min(32,n))[1]
    v=np.full(n,np.inf)
    for i in range(n):
        choices=ids[i][np.minimum(abs(ids[i]-i),n-abs(ids[i]-i))>skip]
        if len(choices):v[i]=np.linalg.norm(p[i]-p[choices[0]])
    return float(np.min(v))

def bounded_smooth(p,iterations=20):
    p=np.asarray(p,float)
    m0=metrics(p);e=m0['median_edge'];n=len(p)
    a=p-np.roll(p,1,axis=0);b=np.roll(p,-1,axis=0)-p
    angle=np.arccos(np.clip(np.sum(a*b,axis=1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)),-1,1))
    threshold=max(0.20,float(np.percentile(angle,99.5)))
    peaks=np.flatnonzero(angle>threshold)
    if not len(peaks):
        return p.copy(),{'method':'unchanged_smooth_source','peaks':0,'max_displacement':0.0,
           'before':m0,'after':m0,'embedding_isotopy':'UNRESOLVED'}
    # Scale smoothing by available clearance and original resolution, without an
    # unsupported assumption about physical core radius.
    coarse_gap=local_vertex_gap(p)
    budget=min(0.35*coarse_gap,0.40*e,0.32)
    weights=np.zeros(n)
    for at in peaks:
        for d in range(-8,9):
            weights[(at+d)%n]=max(weights[(at+d)%n],float(np.exp(-0.5*(d/3.)**2)))
    q=p.copy()
    for _ in range(iterations):
        step=0.22*weights[:,None]*(0.5*(np.roll(q,1,axis=0)+np.roll(q,-1,axis=0))-q)
        trial=q+step
        max_move=float(np.linalg.norm(trial-p,axis=1).max())
        if max_move>budget:trial=p+(trial-p)*(budget/max_move)
        if np.max(np.linalg.norm(trial-q,axis=1))<1e-10:break
        q=trial
    m1=metrics(q)
    return q,{'method':'bounded_periodic_local_laplacian','peaks':int(len(peaks)),
       'displacement_limit':budget,'coarse_vertex_gap_before':coarse_gap,
       'max_displacement':float(np.linalg.norm(q-p,axis=1).max()),
       'before':m0,'after':m1,'embedding_isotopy':'UNRESOLVED',
       'turn_improvement_pct':100*(m0['max_turn_rad']-m1['max_turn_rad'])/m0['max_turn_rad'],
       'caution':'Coarse vertex gaps and local fairing do not certify isotopy or post-relaxation stability'}

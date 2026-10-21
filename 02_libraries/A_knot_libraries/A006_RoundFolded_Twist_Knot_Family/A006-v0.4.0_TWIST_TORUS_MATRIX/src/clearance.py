"""Adaptive global segment-distance search, excluding a declared local neighbor band."""
import numpy as np
from scipy.spatial import cKDTree

def _segment_distance(p0,p1,q0,q1):
    # Full clamped finite-segment formula (Real-Time Collision Detection).
    u=p1-p0;v=q1-q0;w=p0-q0
    a=float(u@u);b=float(u@v);c=float(v@v);d=float(u@w);e=float(v@w)
    D=a*c-b*b
    sN=D;sD=D;tN=D;tD=D
    if D<1.e-18:
        sN=0.0;sD=1.0;tN=e;tD=c
    else:
        sN=b*e-c*d;tN=a*e-b*d
        if sN<0:sN=0;tN=e;tD=c
        elif sN>sD:sN=sD;tN=e+b;tD=c
    if tN<0:
        tN=0
        if -d<0:sN=0
        elif -d>a:sN=sD
        else:sN=-d;sD=a
    elif tN>tD:
        tN=tD
        if (-d+b)<0:sN=0
        elif (-d+b)>a:sN=sD
        else:sN=-d+b;sD=a
    sc=0 if abs(sN)<1e-18 else sN/sD
    tc=0 if abs(tN)<1e-18 else tN/tD
    return float(np.linalg.norm(w+sc*u-tc*v))

def global_min_nonlocal(x,skip=None):
    """Globally exact search up to numerical precision, for non-neighbor segments.
    Initial nearest-midpoint candidates supply an upper bound; all segments
    whose bounding midpoint balls might beat it are examined. Handles cases
    with no neighbor closer than a fixed radius (unlike the older 2.5 filter).
    """
    x=np.asarray(x,dtype=float);n=len(x)
    skip=max(4,int(n*0.005)) if skip is None else skip
    e=np.roll(x,-1,axis=0)-x
    seglen=np.linalg.norm(e,axis=1)
    mids=x+.5*e
    tree=cKDTree(mids)
    def eligible(i,j):return j>i and min(j-i,n-(j-i))>skip
    # With large enough k there is always a non-local candidate.
    near=tree.query(mids,k=min(n,max(2*skip+20,36)))[1]
    best=float('inf');pair=None
    for i,neighbors in enumerate(near):
        for j in np.atleast_1d(neighbors):
            j=int(j)
            if eligible(i,j):
                d=_segment_distance(x[i],x[(i+1)%n],x[j],x[(j+1)%n])
                if d<best:best=d;pair=(i,j)
    if not np.isfinite(best):raise ValueError('No nonlocal candidate')
    # Midpoint separation <= exact segment separation + (Li+Lj)/2 <= d + max edge.
    radius=best+float(seglen.max())+1.e-9
    examined=0
    for i in range(n):
        for j in tree.query_ball_point(mids[i],radius):
            if not eligible(i,j):continue
            examined+=1
            d=_segment_distance(x[i],x[(i+1)%n],x[j],x[(j+1)%n])
            if d<best:best=d;pair=(i,j)
    return {'distance':float(best),'witness_segments':list(pair),'neighbor_skip':skip,
            'search_method':'adaptive exact finite-segment + certified midpoint exclusion bound',
            'searched_pairs':examined}

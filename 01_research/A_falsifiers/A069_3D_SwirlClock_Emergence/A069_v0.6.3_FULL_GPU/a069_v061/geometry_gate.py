"""Conservative source-native geometry and GP core/readiness audit.

The nonlocal separation computed here is a sampled segment screening bound,
not the mathematically exact thickness (reach) or a certified doubly-critical
self-distance; arclength exclusion is explicit. All units are GP dimensionless.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree


def segment_distance(a,b,c,d):
    """Minimum Euclidean distance between two finite 3D line segments."""
    u=b-a; v=d-c; w=a-c
    aa=np.dot(u,u); bb=np.dot(u,v); cc=np.dot(v,v); dd=np.dot(u,w); ee=np.dot(v,w)
    D=aa*cc-bb*bb
    sN,sD=D,D; tN,tD=D,D
    if D<1e-14:
        sN=0.0;sD=1.0;tN=ee;tD=cc
    else:
        sN=bb*ee-cc*dd; tN=aa*ee-bb*dd
        if sN<0:sN=0.0;tN=ee;tD=cc
        elif sN>sD:sN=sD;tN=ee+bb;tD=cc
    if tN<0:
        tN=0.0
        if -dd<0:sN=0.0
        elif -dd>aa:sN=sD
        else:sN=-dd;sD=aa
    elif tN>tD:
        tN=tD
        if (-dd+bb)<0:sN=0.0
        elif (-dd+bb)>aa:sN=sD
        else:sN=(-dd+bb);sD=aa
    s=0.0 if abs(sN)<1e-15 else sN/sD
    t=0.0 if abs(tN)<1e-15 else tN/tD
    return float(np.linalg.norm(w+s*u-t*v))


def geometry_screen(curve:np.ndarray, *, exclude_fraction:float=.07, neighbor_k:int=192) -> dict:
    x=np.asarray(curve,dtype=float)
    if x.ndim!=2 or x.shape[1]!=3 or len(x)<32 or not np.isfinite(x).all():
        raise ValueError('finite Nx3 closed periodic samples required')
    n=len(x)
    dif=np.roll(x,-1,axis=0)-x
    lens=np.linalg.norm(dif,axis=1)
    if np.min(lens)<1e-12:raise ValueError('zero-length centerline segment')
    length=float(np.sum(lens)); gap=int(max(4,np.ceil(n*exclude_fraction)))
    # KDTree indexes segment midpoints; candidates within local region plus
    # candidate enriched by endpoints; missing a pair means UNKNOWN, not PASS.
    mid=x+.5*dif
    tree=cKDTree(mid)
    best=float('inf'); pair=None; sampled=0
    neighbors=tree.query(mid,k=min(n,max(8,neighbor_k)))[1]
    for i in range(n):
        for j in neighbors[i,1:]:
            j=int(j)
            if min((j-i)%n,(i-j)%n)<=gap:continue
            if j<i:continue
            d=segment_distance(x[i],x[(i+1)%n],x[j],x[(j+1)%n]);sampled+=1
            if d<best:best=d;pair=[int(i),j]
    # ensure all potential closer pairs are considered (up to segment radius)
    # via rigorous midpoint triangle bound: d_seg >= d_mid - (l_i+l_j)/2.
    # If nearest pair is unavailable, the status remains UNRESOLVED.
    if np.isfinite(best):
        radius=best+float(np.max(lens))
        for i,j in tree.query_pairs(radius):
            if min((j-i)%n,(i-j)%n)<=gap:continue
            d=segment_distance(x[i],x[(i+1)%n],x[j],x[(j+1)%n]);sampled+=1
            if d<best:best=d;pair=[int(i),int(j)]
    # discrete curvature using turning angles (diagnostic only)
    a=np.roll(dif,1,axis=0); b=dif
    cos=np.clip(np.sum(a*b,axis=1)/(np.linalg.norm(a,axis=1)*lens),-1,1)
    turns=np.arccos(cos)
    k=2*np.sin(turns/2)/np.maximum(.5*(np.roll(lens,1)+lens),1e-15)
    return {'schema':'A069-V061-GEOMETRY-SCREEN-1','samples':n,'length':length,
       'approx_min_nonlocal_segment_distance':best if np.isfinite(best) else None,
       'closest_segment_pair':pair,'exclude_fraction':exclude_fraction,
       'excluded_segment_gap':gap,'screened_pairs':sampled,
       'max_discrete_curvature':float(np.max(k)),
       'max_segment_length':float(np.max(lens)),
       'method':'periodic_segment_distance_with_arclength_exclusion_and_midpoint_bound',
       'certified_reach':False,'topology_certified':False}


def readiness(screen:dict, *, xi:float,n:int,box:float,
              min_cells:float=4.0,max_core_to_gap:float=.3,max_curvature_core:float=.3):
    if xi<=0 or n<=0 or box<=0:raise ValueError('positive xi,n,box required')
    dx=box/n;d=screen['approx_min_nonlocal_segment_distance'];curv=screen['max_discrete_curvature']
    cells=xi/dx;gap_ratio=None if d is None else xi/d
    flags={'core_resolution':cells>=min_cells,
           'nonlocal_core_separation': bool(d is not None and gap_ratio<=max_core_to_gap),
           'curvature_core':xi*curv<=max_curvature_core}
    return {'schema':'A069-V061-CORE-READINESS-1','n':n,'box':box,'dx':dx,'xi':xi,
        'cells_per_xi':cells,'xi_to_nonlocal_gap':gap_ratio,'xi_times_kmax':xi*curv,
        'thresholds':{'cells_per_xi_min':min_cells,'xi_to_gap_max':max_core_to_gap,
                      'xi_times_kmax_max':max_curvature_core},'gates':flags,
        'qualified':all(flags.values()),'status':'GEOMETRY_NUMERIC_PREFLIGHT_ONLY' if all(flags.values()) else 'FAIL_CLOSED_CORE_OR_GRID',
        'physics_stability_certified':False}

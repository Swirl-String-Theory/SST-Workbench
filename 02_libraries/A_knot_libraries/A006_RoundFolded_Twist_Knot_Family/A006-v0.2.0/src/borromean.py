"""Borromean locally-knotted link candidate from projection-first twist-knot seeds.

Core is closure of (sigma1 sigma2^-1)^3; inserted knot uses a local connected-sum
surgery. Pairwise linking and clearances are numerical; the Milnor triple invariant
and exact ambient-isotopy certificate remain UNRESOLVED.
"""
import numpy as np
import braid_backend as b
from roundfold import fourplat,resample_closed

def unit(a):
    norm=np.linalg.norm(a)
    if norm<1e-12:raise ValueError('zero direction')
    return a/norm

def bridge(a,z,ta,tz,count=24,bulge=None):
    distance=np.linalg.norm(z-a);d=min(.4*distance,.75)
    s=np.arange(1,count+1)[:,None]/(count+1)
    out=(2*s**3-3*s**2+1)*a+(-2*s**3+3*s**2)*z+(s**3-2*s**2+s)*(d*unit(ta))+(s**3-s**2)*(d*unit(tz))
    if bulge is not None:out+=np.sin(np.pi*s)**2*np.asarray(bulge)
    return out

def splice(skeleton,source,site,knot_diameter=1.8,altitude=1.55,ngap=5):
    """Explicit local source insertion, no stochastic relaxation."""
    sk=np.asarray(skeleton);src=np.asarray(source);n=len(sk)
    aa=(site-ngap)%n;bb=(site+ngap)%n
    outside=np.array([sk[(bb+i)%n] for i in range((aa-bb)%n+1)])
    A=outside[-1];B=outside[0]
    k,cutedge=b.cut_and_lift_knot(src,(A+B)/2,B-A,altitude=altitude,diameter=knot_diameter)
    k=k[::-1].copy()
    # smooth Hermite join and weak opposing radial shoulders
    normal=unit(np.array([(A[0]+B[0])/2,(A[1]+B[1])/2,0.0]))
    left=bridge(A,k[0],A-outside[-2],k[1]-k[0],bulge=.55*normal)
    right=bridge(k[-1],B,k[-1]-k[-2],outside[1]-B,bulge=-.55*normal)
    return np.vstack((outside,left,k,right)),{'cut_edge':int(cutedge),'n_outside':len(outside),'n_local_knot':len(k),'n_leftbridge':len(left),'n_rightbridge':len(right)}

def make(ms,n=768,scale=10.0):
    if len(ms)!=3:raise ValueError('Borromean must have exactly 3 knot indices')
    b.N_PER_EVENT=80;b.R=11.0;b.BETA=1.9
    sk=b.base_components();comps=[];metas=[]
    for i,m in enumerate(ms):
        source,detail=fourplat(m)
        openk,meta=splice(sk[i],resample_closed(source,512),site=(1+2*i)*b.N_PER_EVENT)
        dense=resample_closed(openk,n)
        comps.append(dense*scale);metas.append(meta)
    # Scale down only when calling KD-tree clearance helper with fixed search radius.
    inter={f'{i}-{j}':float(scale*b.min_segsep(comps[i]/scale,comps[j]/scale)) for i,j in [(0,1),(0,2),(1,2)]}
    lk={f'{i}-{j}':float(b.ringlinking(comps[i],comps[j])) for i,j in [(0,1),(0,2),(1,2)]}
    selfdist=[float(scale*b.min_segsep(c/scale,c/scale,True)) for c in comps]
    return comps,{'pairwise_linking_numerical':lk,'intercomponent_segment_clearance':inter,
                   'self_segment_clearance_screen':selfdist,'splices':metas,'scale':scale,
                   'skeleton_word':'(sigma_1 sigma_2^-1)^3',
                   'triple_linking':'UNRESOLVED','connected_sum_isotopy':'UNRESOLVED'}

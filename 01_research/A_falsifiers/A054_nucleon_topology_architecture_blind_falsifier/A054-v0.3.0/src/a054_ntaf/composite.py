from __future__ import annotations
import numpy as np
from .geometry import (
    close_curve,resample_closed_curve,normalize_total_length,
    pairwise_link_matrix,min_intercomponent_distance
)

class CompositeConstructionError(RuntimeError): pass


def loose_components(knots: list[np.ndarray], separation: float=2.8, n: int=192):
    """Place three supplied PKLSA knot carriers in mutually disjoint boxes."""
    if len(knots)!=3: raise ValueError("exactly 3 components required")
    centers=np.array([[-separation,-0.6,0],[separation,-0.6,0],[0,2.4,0]],float)
    out=[]
    for k,ctr in zip(knots,centers):
        x=resample_closed_curve(k,n); x=x-x.mean(0)
        rad=np.max(np.linalg.norm(x,axis=1)); x=x/max(rad,1e-12)*0.7
        out.append(x+ctr)
    return normalize_total_length(out)


def _rotation_a_to_b(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b)
    v=np.cross(a,b); c=float(np.dot(a,b)); s=float(np.linalg.norm(v))
    if s<1e-12:
        if c>0: return np.eye(3)
        # 180 degrees about any axis perpendicular to a.
        q=np.array([1.,0.,0.]) if abs(a[0])<0.8 else np.array([0.,1.,0.])
        q-=a*np.dot(a,q); q/=np.linalg.norm(q)
        return 2*np.outer(q,q)-np.eye(3)
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+K+K@K*((1-c)/(s*s))


def _cyclic_distance(i,j,n):
    d=abs(i-j); return min(d,n-d)


def _best_insertion_edge(component, all_components, comp_index, exclusion=8):
    s=close_curve(component); n=len(s); best=None
    stride=max(1,n//64)
    for i in range(0,n,stride):
        j=(i+1)%n; mid=.5*(s[i]+s[j]); edge=np.linalg.norm(s[j]-s[i])
        dmin=np.inf
        # Remote points on same component.
        for q,p in enumerate(s):
            if _cyclic_distance(q,i,n)<=exclusion or _cyclic_distance(q,j,n)<=exclusion: continue
            dmin=min(dmin,float(np.linalg.norm(p-mid)))
        for k,c in enumerate(all_components):
            if k==comp_index: continue
            dmin=min(dmin,float(np.min(np.linalg.norm(np.asarray(c)-mid,axis=1))))
        score=dmin/max(edge,1e-15)
        if best is None or score>best[0]: best=(score,i,dmin,edge)
    if best is None or not np.isfinite(best[2]): raise CompositeConstructionError('no certified insertion edge')
    return best


def _insert_local_knot(skeleton, knot, all_components, comp_index, n_out=192, ball_fraction=.28):
    s=resample_closed_curve(skeleton,max(n_out,192)); k=resample_closed_curve(knot,max(n_out,192))
    score,i,clearance,edge=_best_insertion_edge(s,all_components,comp_index)
    j=(i+1)%len(s); A=s[i]; B=s[j]; mid=.5*(A+B); tangent=B-A
    ball_radius=ball_fraction*clearance
    if .5*edge>=.45*ball_radius:
        raise CompositeConstructionError(f'insertion edge too large for certified ball: edge={edge:g}, ball={ball_radius:g}')

    # Cut the source knot at one existing edge. The remaining long arc is a knotted tangle.
    # Select the edge whose midpoint has the greatest radius from the source centroid, which
    # tends to keep the closure bridges outside the dense interior of the tangle.
    kc=k.mean(0); kn=len(k)
    mids=.5*(k+np.roll(k,-1,axis=0)); cut=int(np.argmax(np.linalg.norm(mids-kc,axis=1)))
    a=cut; b=(cut+1)%kn
    order=[b]+[(b+t)%kn for t in range(1,kn-1)]+[a]
    chain=k[order].copy(); chain-=chain.mean(0)
    endpoint_vec=chain[-1]-chain[0]
    if np.linalg.norm(endpoint_vec)<1e-12: raise CompositeConstructionError('degenerate source-knot cut')
    R=_rotation_a_to_b(endpoint_vec,tangent)
    chain=chain@R.T
    rad=float(np.max(np.linalg.norm(chain,axis=1)))
    target_rad=.42*ball_radius
    chain*=target_rad/max(rad,1e-15)
    # Place the source tangle at the insertion-ball centre.
    chain+=mid
    if np.max(np.linalg.norm(chain-mid,axis=1))>.43*ball_radius:
        raise CompositeConstructionError('tangle escaped certified insertion ball')

    # Orient chain so its first endpoint is closest to A.
    if np.linalg.norm(chain[0]-A)>np.linalg.norm(chain[-1]-A): chain=chain[::-1].copy()
    # The convex straight bridges remain inside the certified ball because all endpoints do.
    if max(np.linalg.norm(A-mid),np.linalg.norm(B-mid),np.linalg.norm(chain[0]-mid),np.linalg.norm(chain[-1]-mid))>=ball_radius:
        raise CompositeConstructionError('bridge endpoint outside insertion ball')

    # A -> source tangle -> B -> remainder of original skeleton -> A.
    tail=[]; q=(j+1)%len(s)
    while q!=i:
        tail.append(s[q]); q=(q+1)%len(s)
    raw=np.vstack([A[None,:],chain,B[None,:],np.asarray(tail) if tail else np.empty((0,3))])
    out=resample_closed_curve(raw,n_out)
    cert={
      'construction':'local_connected_sum_in_disjoint_ball',
      'skeleton_component_index':int(comp_index),'skeleton_edge_index':int(i),'source_knot_cut_edge':int(cut),
      'pre_insertion_clearance':float(clearance),'insertion_ball_radius':float(ball_radius),
      'edge_length':float(edge),'clearance_to_edge_ratio':float(clearance/max(edge,1e-15)),
      'topology_argument':'skeleton component is an unknot; local connected sum with source knot gives source-knot component type if the certified ball is disjoint from remote arcs'
    }
    return out,cert


def decorate_skeleton(skeleton: list[np.ndarray], knots: list[np.ndarray], n: int=192,
                      link_tolerance: float=.08):
    """Decorate three unknotted link components by local connected sum with source knots.

    The routine is fail-closed: each insertion uses a ball separated from remote sampled arcs,
    and the final pairwise Gauss-linking matrix must remain within `link_tolerance` of the
    original skeleton. This numerically certifies the intended *link skeleton* preservation;
    source component knot identity follows from the connected-sum construction, conditional on
    the sampled-ball clearance certificate.
    """
    if len(skeleton)!=3 or len(knots)!=3: raise ValueError('three skeleton and three knot components required')
    base=[resample_closed_curve(c,max(n,192)) for c in skeleton]
    L0=pairwise_link_matrix(base)
    work=[c.copy() for c in base]; certs=[]
    for idx in range(3):
        new,cert=_insert_local_knot(work[idx],knots[idx],work,idx,n_out=max(n,192))
        work[idx]=new; certs.append(cert)
    work=normalize_total_length([resample_closed_curve(c,n) for c in work])
    L1=pairwise_link_matrix(work); drift=float(np.max(np.abs(L1-L0)))
    inter=float(min_intercomponent_distance(work))
    if not np.isfinite(inter) or inter<=1e-5:
        raise CompositeConstructionError(f'component clearance failed after decoration: {inter}')
    if drift>link_tolerance:
        raise CompositeConstructionError(f'link-skeleton preservation failed: max |dLk|={drift:g}>{link_tolerance:g}')
    return work,{
      'status':'CERTIFIED_SAMPLED_CONNECTED_SUM','insertions':certs,
      'initial_pairwise_link_matrix':L0.tolist(),'final_pairwise_link_matrix':L1.tolist(),
      'max_pairwise_linking_drift':drift,'final_min_intercomponent_distance':inter,
      'caveat':'numerical sampled-geometry certificate; exact knot-polynomial cross-check is a v0.2 certification gate'
    }

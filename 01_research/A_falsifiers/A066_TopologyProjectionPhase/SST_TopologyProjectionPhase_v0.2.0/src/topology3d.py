"""Topological screening for closed polygonal oriented filaments.

Alexander determinant at -1 via Fox tricoloring/Wirtiger crossing relations,
with several generic projection directions; numerical quadrature for Gauss linking.
These are knot/link geometry tests, NOT evidence of non-ideal Euler reconnection.
"""
from __future__ import annotations
import math
from bisect import bisect_right
import numpy as np


def _curve(curve):
    p=np.asarray(curve,dtype=np.float64)
    if p.ndim !=2 or p.shape[1]!=3 or len(p)<12 or not np.isfinite(p).all():
        raise ValueError('curve must be finite Nx3, N>=12')
    d=np.diff(np.r_[p,p[:1]],axis=0)
    if np.min(np.linalg.norm(d,axis=1)) <= 1e-12:
        raise ValueError('zero length polygon edge')
    return p


def _basis(normal):
    n=np.asarray(normal,dtype=float)
    n=n/np.linalg.norm(n)
    seed=np.eye(3)[np.argmin(np.abs(n))]
    x=np.cross(n,seed);x/=np.linalg.norm(x)
    y=np.cross(n,x)
    return np.column_stack((x,y,n))


def _cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]


def _crossings(p,normal):
    p=_curve(p);n=len(p);proj=p@_basis(normal);crosses=[]
    # Polygon edge intersections in a generic projection.
    for i in range(n):
        a=proj[i];d=proj[(i+1)%n]-a
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            b=proj[j];e=proj[(j+1)%n]-b
            den=_cross2(d[:2],e[:2])
            if abs(den)<1e-11:continue
            w=b[:2]-a[:2]
            s=_cross2(w,e[:2])/den; t=_cross2(w,d[:2])/den
            if not (1e-7<s<1-1e-7 and 1e-7<t<1-1e-7):continue
            hi=a[2]+s*d[2];hj=b[2]+t*e[2]
            if abs(hi-hj)<1e-9:raise ValueError('degenerate projection: coincident height')
            if hi>hj:crosses.append((i+s,j+t))
            else:crosses.append((j+t,i+s))
    return crosses


def _bareiss_det(matrix):
    """Integer exact determinant via Bareiss elimination."""
    a=[list(map(int,row)) for row in matrix];n=len(a)
    if n==0:return 1
    sign=1;prev=1
    for k in range(n-1):
        if a[k][k]==0:
            q=next((i for i in range(k+1,n) if a[i][k]),None)
            if q is None:return 0
            a[k],a[q]=a[q],a[k];sign=-sign
        pivot=a[k][k]
        for i in range(k+1,n):
            for j in range(k+1,n):
                num=a[i][j]*pivot-a[i][k]*a[k][j]
                if num%prev:raise ArithmeticError('noninteger Bareiss division')
                a[i][j]=num//prev
        for i in range(k+1,n):a[i][k]=0
        prev=pivot
    return sign*a[-1][-1]


def alexander_determinant(curve,normal=(0.17,0.53,0.83)):
    """Abs(Delta(-1)); 1 for unknot, 3 trefoil, 5 figure-eight.

    For 0/1 crossings the determinant is 1. A crossing diagram with
    m undercrossings has m Wirtinger arcs; delete any row & column.
    """
    crosses=_crossings(curve,normal);m=len(crosses)
    if m<=1:return {'determinant':1,'crossings':m,'status':'QUALIFIED'}
    under=sorted((u,k) for k,(_,u) in enumerate(crosses))
    sorted_pos=[row[0] for row in under]
    index={original:slot for slot,(_,original) in enumerate(under)}
    M=np.zeros((m,m),dtype=int)
    for k,(over,u) in enumerate(crosses):
        i=index[k];b=(i-1)%m;a=i
        o=(bisect_right(sorted_pos,over)-1)%m
        M[i,o]+=2;M[i,b]-=1;M[i,a]-=1
    val=abs(_bareiss_det(M[:-1,:-1]))
    return {'determinant':int(val),'crossings':m,'status':'QUALIFIED' if val>=1 and val%2==1 else 'DEGENERATE'}


def knot_signature(curve):
    normals=[(0.17,0.53,0.83),(0.81,-0.27,0.53),(-0.33,0.91,0.24)]
    results=[]
    for norm in normals:
        try:results.append(alexander_determinant(curve,norm))
        except (ValueError,ArithmeticError) as exc:results.append({'status':'UNRESOLVED','reason':str(exc)})
    good=[v['determinant'] for v in results if v['status']=='QUALIFIED']
    agree=len(good)>=2 and len(set(good))==1
    return {'status':'QUALIFIED' if agree else 'UNRESOLVED',
            'alexander_det_at_minus_one':good[0] if agree else None,
            'independent_projection_results':results,
            'limitation':'Determinant 1 does not establish the unknot; nontrivial knots can have determinant 1.'}


def gauss_link(curve_a,curve_b,quadrature_order=3):
    """Gauss linking integral with tensor Gauss-Legendre panel quadrature.

    Both loops disjoint and oriented, any length unit. Quadrature convergence
    and absolute centerline separation are checked separately.
    """
    a,b=_curve(curve_a),_curve(curve_b)
    da=np.roll(a,-1,axis=0)-a;db=np.roll(b,-1,axis=0)-b
    nodes,weights=np.polynomial.legendre.leggauss(quadrature_order)
    nodes=(nodes+1)/2;weights=weights/2
    cross=np.cross(da[:,None,:],db[None,:,:])
    total=0.
    for s,ws in zip(nodes,weights):
        aa=a+s*da
        for t,wt in zip(nodes,weights):
            bb=b+t*db
            r=aa[:,None,:]-bb[None,:,:]
            r2=np.einsum('ijk,ijk->ij',r,r)
            if r2.min()<1e-22:raise ValueError('nearly intersecting loops in quadrature')
            total+=ws*wt*np.sum(np.einsum('ijk,ijk->ij',r,cross)/(r2*np.sqrt(r2)))
    return float(total/(4*np.pi))


def _segment_distance_pairs(a,b):
    """Exact minimum distance for all 3D polygon segment pairs (vectorized).

    Candidate min from interiors (if both parameters in [0,1]), plus
    four closest endpoint-to-opposite-segment projections.
    """
    p=np.asarray(a);q=np.asarray(b)
    ap=p[:,None,:];bp=q[None,:,:]
    u=np.roll(p,-1,axis=0)-p;v=np.roll(q,-1,axis=0)-q
    u=u[:,None,:];v=v[None,:,:]
    w=ap-bp
    A=np.sum(u*u,axis=-1);B=np.sum(u*v,axis=-1);C=np.sum(v*v,axis=-1)
    D=np.sum(u*w,axis=-1);E=np.sum(v*w,axis=-1)
    den=A*C-B**2
    denok=den>1e-16*(A*C+1)
    sc=np.divide(B*E-C*D,den,out=np.full_like(den,np.nan),where=denok)
    tc=np.divide(A*E-B*D,den,out=np.full_like(den,np.nan),where=denok)
    valid=denok & (sc>=0)&(sc<=1)&(tc>=0)&(tc<=1)
    interior=np.where(valid,np.linalg.norm(w+sc[...,None]*u-tc[...,None]*v,axis=-1),np.inf)
    def endpoint_on_segment(point_from_first, offset):
        # w + offset*u - t*v : first-segment endpoints to second segment
        vec=w+offset*u
        tv=np.clip(np.sum(vec*v,axis=-1)/C,0,1)
        return np.linalg.norm(vec-tv[...,None]*v,axis=-1)
    def endpoint_second(offset):
        # w - offset*v + s*u
        vec=w-offset*v
        su=np.clip(-np.sum(vec*u,axis=-1)/A,0,1)
        return np.linalg.norm(vec+su[...,None]*u,axis=-1)
    return np.minimum.reduce([interior,endpoint_on_segment(0,0),endpoint_on_segment(0,1),endpoint_second(0),endpoint_second(1)])


def min_curve_distance(a,b):
    return float(np.min(_segment_distance_pairs(_curve(a),_curve(b))))


def min_nonlocal_self_distance(a,exclusion=3):
    p=_curve(a);n=len(p)
    if n<2*exclusion+3:raise ValueError('too few vertices')
    d=_segment_distance_pairs(p,p)
    ii=np.arange(n)[:,None];jj=np.arange(n)[None,:]
    delta=np.minimum(abs(ii-jj),n-abs(ii-jj))
    return float(d[delta>exclusion].min())


def link_signature(filaments, present, gamma=None):
    """One-frame link and knot geometry with separate circulation consistency."""
    curves=[_curve(filaments[j]) for j,p in enumerate(present) if p]
    result={'components':len(curves),'knots':[], 'links':[], 'min_distance':None}
    for a in curves:result['knots'].append(knot_signature(a))
    mind=[]
    for i in range(len(curves)):
        for j in range(i+1,len(curves)):
            v3=gauss_link(curves[i],curves[j],3)
            v5=gauss_link(curves[i],curves[j],5)
            gap=min_curve_distance(curves[i],curves[j]);mind.append(gap)
            nearest=int(round(v5));err=abs(v5-nearest)
            qual=(err<0.075 and abs(v5-v3)<0.075 and gap>1e-6)
            result['links'].append({'a':i,'b':j,'lk_gauss_q3':v3,'lk_gauss_q5':v5,
              'lk_integer':nearest if qual else None,
              'status':'QUALIFIED' if qual else 'UNRESOLVED',
              'centerline_min_separation':gap,'integration_delta':abs(v5-v3)})
    result['min_distance']=min(mind) if mind else None
    if gamma is not None:result['component_gamma']=[float(v) for v in np.asarray(gamma)[np.asarray(present,dtype=bool)]]
    return result

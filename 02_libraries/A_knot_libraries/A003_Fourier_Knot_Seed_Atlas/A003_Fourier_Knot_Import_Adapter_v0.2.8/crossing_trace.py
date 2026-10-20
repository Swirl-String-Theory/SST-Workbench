"""A003 v0.2.6 independent geometric crossing trace (not a topology certificate).

Raw polygon segment intersection and over/under Gauss events. No pyknotid is used.
Reconstructs an Alexander *determinant* at t=-1 using Fox/Wirtinger coloring.
It is NOT the full Alexander polynomial and cannot certify chirality or isotopy.
"""
from __future__ import annotations
import bisect, math
import numpy as np


def crossing_trace(points: np.ndarray) -> dict:
    pts=np.asarray(points,dtype=np.float64)
    if pts.ndim!=2 or pts.shape[1]!=3 or len(pts)<4 or not np.isfinite(pts).all():
        raise ValueError('invalid 3D polygon')
    n=len(pts); edges=np.roll(pts,-1,axis=0)-pts
    a=pts[:,:2]; u=edges[:,:2]; b=a+u
    low=np.minimum(a,b);high=np.maximum(a,b)
    diameter=float(np.linalg.norm(np.ptp(pts,axis=0)))
    crossings=[]
    for i in range(n-2):
        js=np.arange(i+2,n if i else n-1,dtype=int)
        keep=(low[js,0]<=high[i,0])&(high[js,0]>=low[i,0]) & (low[js,1]<=high[i,1])&(high[js,1]>=low[i,1])
        js=js[keep]
        if not len(js): continue
        v=u[js];w=a[js]-a[i]
        det=u[i,0]*v[:,1]-u[i,1]*v[:,0]
        norms=np.linalg.norm(u[i])*np.linalg.norm(v,axis=1)
        valid=np.abs(det)>16*np.finfo(float).eps*np.maximum(norms,1.e-300)
        js=js[valid];v=v[valid];w=w[valid];det=det[valid];norms=norms[valid]
        if not len(js):continue
        alpha=(w[:,0]*v[:,1]-w[:,1]*v[:,0])/det
        beta=(w[:,0]*u[i,1]-w[:,1]*u[i,0])/det
        select=(alpha>0)&(alpha<1)&(beta>0)&(beta<1)
        js=js[select];det=det[select];norms=norms[select];alpha=alpha[select];beta=beta[select]
        for j,D,norm,t,s in zip(js,det,norms,alpha,beta):
            za=pts[i,2]+t*edges[i,2];zb=pts[j,2]+s*edges[j,2]
            sign=np.sign(za-zb)
            crossings.append({'edge_a':int(i),'edge_b':int(j),'t_a':float(t),'t_b':float(s),
                's_a':float(i+t),'s_b':float(j+s), 'z_a':float(za),'z_b':float(zb),
                'over':'a' if sign>0 else 'b' if sign<0 else 'ambiguous',
                'abs_sin_angle':float(abs(D)/norm),
                'depth_delta_over_diameter':float(abs(za-zb)/diameter),
                'signed_projective_crossing':int(np.sign(D)*sign)})
    crossings.sort(key=lambda x:(x['s_a'],x['s_b']))
    events=[]
    for idx,c in enumerate(crossings):
        c['crossing_id']=idx+1
        for side in ('a','b'):
            events.append({'s':c['s_'+side], 'crossing_id':idx+1, 'role':'OVER' if c['over']==side else 'UNDER' if c['over']!='ambiguous' else 'AMBIGUOUS'})
    events.sort(key=lambda x:x['s'])
    crossing_count=len(crossings)
    near=sum(c['abs_sin_angle']<1e-5 or c['depth_delta_over_diameter']<1e-6 for c in crossings)
    return {'schema':'sst.a003.raw-projected-crossings/1','N':n,'crossing_count':crossing_count,
        'nearly_degenerate_crossings':near,'crossings':crossings,'gauss_events':events,
        'gauss_code':[int(e['crossing_id'])*(1 if e['role']=='OVER' else -1) for e in events],
        'diagram_determinant':wirtinger_determinant(crossings,events)}


def bareiss_det(a: list[list[int]])->int:
    """Exact integer Bareiss determinant with row pivoting."""
    if not a:return 1
    n=len(a);a=[list(map(int,row)) for row in a];sign=1;prev=1
    for k in range(n-1):
        if a[k][k]==0:
            j=next((i for i in range(k+1,n) if a[i][k]!=0),None)
            if j is None:return 0
            a[j],a[k]=a[k],a[j];sign=-sign
        pivot=a[k][k]
        for i in range(k+1,n):
            for j in range(k+1,n):
                val=a[i][j]*pivot-a[i][k]*a[k][j]
                if val%prev:raise ArithmeticError('nonintegral Bareiss intermediate')
                a[i][j]=val//prev
        for i in range(k+1,n):a[i][k]=0
        prev=pivot
    return sign*a[-1][-1]


def wirtinger_determinant(crossings:list[dict],events:list[dict])->dict:
    if any(c['over']=='ambiguous' for c in crossings):
        return {'status':'UNRESOLVED_AMBIGUOUS_OVER_UNDER','value':None}
    under=sorted((e['s'],e['crossing_id']) for e in events if e['role']=='UNDER')
    n=len(under)
    if n!=len(crossings):return {'status':'ERROR_EVENT_MISMATCH','value':None}
    if n==0:return {'status':'COMPUTED_DIAGRAM_ONLY','value':1,'arc_count':0,'definition':'absolute Fox/Wirtinger minor at t=-1'}
    uidx={cid:i for i,(_,cid) in enumerate(under)}
    positions=[s for s,_ in under]
    overevents={e['crossing_id']:e['s'] for e in events if e['role']=='OVER'}
    matrix=[[0]*n for _ in range(n)]
    for cid,under_idx in uidx.items():
        # arc index k is the arc *after* underpass k, wrapping around the knot.
        preceding=bisect.bisect_left(positions,overevents[cid])-1
        over_idx=preceding%n
        matrix[under_idx][over_idx]+=2
        matrix[under_idx][(under_idx-1)%n]-=1
        matrix[under_idx][under_idx]-=1
    minor=[row[:-1] for row in matrix[:-1]]
    return {'status':'COMPUTED_DIAGRAM_ONLY','value':abs(bareiss_det(minor)),
        'arc_count':n,'definition':'absolute Fox/Wirtinger minor at t=-1',
        'matrix_minus_one':matrix}

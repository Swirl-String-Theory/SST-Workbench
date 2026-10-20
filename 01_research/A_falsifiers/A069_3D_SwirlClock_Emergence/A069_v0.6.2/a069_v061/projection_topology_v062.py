"""Numerical projection/Fox determinant diagnostics for reconstructed GP cycles.

Adapted from A069 Historical Trefoil Geometry and Biot-Savart Preflight v0.1.0.
Projection crossings of a single numerical polygon are NOT ambient-isotopy or
continuous-time reconnection certification; they are local screening evidence.
"""
from __future__ import annotations
import numpy as np
ANGLES=((21.,37.,14.), (44.,-30.,69.), (10.,68.,17.), (37.,47.,63.), (-19.,24.,7.))


def rotate(points,ang):
    x,y,z=np.deg2rad(ang)
    cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
    rx=np.array([[1.,0.,0.],[0.,cx,-sx],[0.,sx,cx]])
    ry=np.array([[cy,0.,sy],[0.,1.,0.],[-sy,0.,cy]])
    rz=np.array([[cz,-sz,0.],[sz,cz,0.],[0.,0.,1.]])
    return points@(rz@ry@rx).T


def crossings(points,angles):
    p=rotate(np.asarray(points,float),angles);n=len(p)
    xy=p[:,:2];d=np.roll(xy,-1,axis=0)-xy
    z=p[:,2]; dz=np.roll(z,-1)-z
    cross=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
    result=[];min_depth=float('inf')
    for i in range(n):
        j=np.arange(i+1,n); ifn=len(j)
        if not ifn:continue
        v=xy[i+1:]-xy[i];r=d[i];s=d[i+1:]
        denom=cross(r,s)
        good=np.abs(denom)>1e-13
        t=np.zeros(ifn);u=np.zeros(ifn)
        t[good]=cross(v[good],s[good])/denom[good]
        u[good]=cross(v[good],r)/denom[good]
        select=np.flatnonzero(good&(t>1e-9)&(t<1-1e-9)&(u>1e-9)&(u<1-1e-9))
        for k in select:
            idx=i+1+int(k)
            if idx-i<3 or n-(idx-i)<3:continue
            zi=z[i]+t[k]*dz[i];zj=z[idx]+u[k]*dz[idx];depth=zi-zj
            if abs(depth)<1e-8:raise ValueError('nontransverse or nearly touching crossing')
            min_depth=min(min_depth,abs(depth))
            result.append({'over':float(i+t[k] if depth>0 else idx+u[k]),
                           'under':float(idx+u[k] if depth>0 else i+t[k]),
                           'sign':int(np.sign(cross(r,s[k]))*np.sign(depth))})
    return result,min_depth


def determinant(rows):
    k=len(rows)
    if not k:return 1
    under=np.array(sorted(row['under'] for row in rows))
    mat=np.zeros((k,k),dtype=int)
    for ix,row in enumerate(rows):
        j=int(np.searchsorted(under,row['under']))
        if j>=k or abs(under[j]-row['under'])>1e-7:raise ValueError('unstable underpass order')
        over=(int(np.searchsorted(under,row['over'],side='right'))-1)%k
        mat[ix,over]+=2;mat[ix,(j-1)%k]-=1;mat[ix,j]-=1
    if k==1:return 1
    val=abs(float(np.linalg.det(mat[:-1,:-1])))
    if abs(val-round(val))>1e-6:raise ValueError('unstable determinant')
    return int(round(val))


def numerical_projection_audit(polyline,angles=ANGLES):
    if polyline is None or len(polyline)<12:
        return {'status':'UNRESOLVED_NO_VALID_POLYGON','topology_certified':False}
    x=np.asarray(polyline,float)
    if x.ndim!=2 or x.shape[1]!=3 or not np.isfinite(x).all():
        return {'status':'UNRESOLVED_INVALID_POLYGON','topology_certified':False}
    results=[]
    for angle in angles:
        try:
            cross,depth=crossings(x,angle)
            results.append({'rotation_deg':list(angle),'crossings':len(cross),
                            'fox_determinant':determinant(cross),
                            'signed_writhe_diagram':sum(r['sign'] for r in cross),
                            'min_depth_gap':None if not np.isfinite(depth) else float(depth),
                            'status':'DIAGNOSTIC'})
        except (ValueError,OverflowError,np.linalg.LinAlgError) as e:
            results.append({'rotation_deg':list(angle),'status':'UNRESOLVED_PROJECTION',
                            'reason':str(e)[:160]})
    good=[p for p in results if p['status']=='DIAGNOSTIC']
    dets={p['fox_determinant'] for p in good}
    return {'schema':'A069-V062-PROJECTION-DIAGNOSTIC-1','status':
            'PROJECTION_CONSISTENT_DIAGNOSTIC_ONLY' if len(good)>=3 and len(dets)==1 else 'UNRESOLVED_PROJECTION_DISAGREEMENT',
            'projections':results,'common_determinant':next(iter(dets)) if len(dets)==1 else None,
            'one_projection_three_crossing_trefoil':any(p['crossings']==3 and p['fox_determinant']==3 for p in good),
            'topology_certified':False,'reconnection_certified':False,
            'warning':'Snapshots and projection determinants cannot prove ambient isotopy, provider independence or evolving GP knot stability.'}

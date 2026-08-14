from __future__ import annotations
import math
import numpy as np

PI = math.pi

def _pts(a):
    x=np.ascontiguousarray(a,dtype=float)
    if x.ndim!=2 or x.shape[1]!=3: raise ValueError("points must have shape (N,3)")
    return x

def segment_lengths(points, closed: bool=True):
    p=_pts(points)
    if len(p)==0: return np.empty(0)
    if closed: return np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    return np.linalg.norm(np.diff(p,axis=0),axis=1)

def biot_savart_velocity(source,evaluation,gamma:float=1.0,core_radius:float=1e-3,source_closed:bool=True):
    s=_pts(source); e=_pts(evaluation)
    nseg=len(s) if source_closed else len(s)-1
    if nseg<1: raise ValueError("source requires >=2 points")
    out=np.zeros_like(e)
    a2=float(core_radius)**2
    pref=float(gamma)/(4.0*PI)
    for i in range(nseg):
        j=(i+1)%len(s)
        dl=s[j]-s[i]; mid=0.5*(s[i]+s[j])
        r=e-mid
        den=(np.sum(r*r,axis=1)+a2)**1.5
        mask=den>1e-300
        out[mask]+=pref*np.cross(np.broadcast_to(dl,r[mask].shape),r[mask])/den[mask,None]
    return out

def writhe_midpoint(points,closed:bool=True):
    p=_pts(points)
    nseg=len(p) if closed else len(p)-1
    if nseg<3: return 0.0
    dl=[]; mid=[]
    for i in range(nseg):
        j=(i+1)%len(p); dl.append(p[j]-p[i]); mid.append(0.5*(p[j]+p[i]))
    total=0.0
    for i in range(nseg):
        for j in range(i+1,nseg):
            if j==i+1 or (closed and i==0 and j==nseg-1): continue
            r=mid[i]-mid[j]; r2=float(np.dot(r,r))
            if r2<=1e-24: continue
            total += float(np.dot(r,np.cross(dl[i],dl[j])))/(r2*math.sqrt(r2))
    return total/(2.0*PI)

def _segseg_dist2(p1,q1,p2,q2):
    eps=1e-30; d1=q1-p1; d2=q2-p2; r=p1-p2
    a=float(d1@d1); e=float(d2@d2); f=float(d2@r)
    if a<=eps and e<=eps: return float(r@r)
    if a<=eps: s=0.; t=float(np.clip(f/e,0,1))
    else:
        c=float(d1@r)
        if e<=eps: t=0.; s=float(np.clip(-c/a,0,1))
        else:
            b=float(d1@d2); den=a*e-b*b
            s=float(np.clip((b*f-c*e)/den,0,1)) if abs(den)>eps else 0.
            t=(b*s+f)/e
            if t<0: t=0.; s=float(np.clip(-c/a,0,1))
            elif t>1: t=1.; s=float(np.clip((b-c)/a,0,1))
    c1=p1+s*d1; c2=p2+t*d2
    d=c1-c2; return float(d@d)

def min_segment_distance(a,b,closed_a:bool=True,closed_b:bool=True):
    A=_pts(a); B=_pts(b)
    sa=len(A) if closed_a else len(A)-1; sb=len(B) if closed_b else len(B)-1
    best=float("inf")
    for i in range(sa):
        for j in range(sb):
            best=min(best,_segseg_dist2(A[i],A[(i+1)%len(A)],B[j],B[(j+1)%len(B)]))
    return math.sqrt(best)

def backend_version(): return "0.2.0-python"

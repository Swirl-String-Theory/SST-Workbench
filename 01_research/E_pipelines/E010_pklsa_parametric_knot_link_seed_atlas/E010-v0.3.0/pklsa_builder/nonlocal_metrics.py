from __future__ import annotations
import math, numpy as np

def _native():
    try:
        from . import _native as n
        return n
    except Exception:
        return None

def cyclic_sep(i,j,n):
    d=abs(i-j); return min(d,n-d)

def segment_distance(a0,a1,b0,b1):
    # Standard closest-points-on-segments algorithm.
    u=a1-a0; v=b1-b0; w=a0-b0
    A=float(u@u); B=float(u@v); C=float(v@v); D=float(u@w); E=float(v@w)
    den=A*C-B*B; eps=1e-15*max(1.0,A*C)
    if den<eps:
        s=0.0; t=np.clip(E/max(C,eps),0.0,1.0)
    else:
        s=np.clip((B*E-C*D)/den,0.0,1.0)
        t=np.clip((A*E-B*D)/den,0.0,1.0)
        # one corrective projection after clipping
        if s in (0.0,1.0): t=np.clip((B*s+E)/max(C,eps),0.0,1.0)
        if t in (0.0,1.0): s=np.clip((B*t-D)/max(A,eps),0.0,1.0)
    return float(np.linalg.norm(w+s*u-t*v))

def min_nonlocal_segment_distance(points, exclusion=2):
    p=np.asarray(points,float); n=len(p); nat=_native()
    if nat is not None: return float(nat.min_nonlocal_segment_distance(p,int(exclusion)))
    best=float('inf')
    for i in range(n):
        a0=p[i]; a1=p[(i+1)%n]
        for j in range(i+1,n):
            if cyclic_sep(i,j,n)<=exclusion or cyclic_sep(i,(j+1)%n,n)<=exclusion: continue
            d=segment_distance(a0,a1,p[j],p[(j+1)%n])
            if d<best: best=d
    return best

def approximate_dcsd(points,tangents,exclusion=2,orth_tol=0.12):
    p=np.asarray(points,float); t=np.asarray(tangents,float); n=len(p); nat=_native()
    if nat is not None:
        return float(nat.approximate_dcsd(p,t,int(exclusion),float(orth_tol)))
    best=float('inf')
    for i in range(n):
        for j in range(i+1,n):
            if cyclic_sep(i,j,n)<=exclusion: continue
            d=p[j]-p[i]; dn=float(np.linalg.norm(d))
            if dn<=0: continue
            u=d/dn
            if abs(float(u@t[i]))<=orth_tol and abs(float(u@t[j]))<=orth_tol:
                best=min(best,dn)
    return best

def writhe_acn(points):
    p=np.asarray(points,float); nat=_native()
    if nat is not None:
        w,a=nat.writhe_acn(p); return float(w),float(a)
    n=len(p); mids=0.5*(p+np.roll(p,-1,axis=0)); dr=np.roll(p,-1,axis=0)-p
    wr=0.0; acn=0.0
    for i in range(n):
        for j in range(i+1,n):
            if cyclic_sep(i,j,n)<=1: continue
            r=mids[i]-mids[j]; r3=float(np.linalg.norm(r))**3
            if r3<=1e-300: continue
            g=float(np.dot(np.cross(dr[i],dr[j]),r))/r3
            wr += 2*g; acn += 2*abs(g)
    c=1/(4*math.pi); return wr*c,acn*c

def linking_number(a,b):
    A=np.asarray(a,float); B=np.asarray(b,float); nat=_native()
    if nat is not None: return float(nat.linking_number(A,B))
    ma=.5*(A+np.roll(A,-1,axis=0)); mb=.5*(B+np.roll(B,-1,axis=0))
    da=np.roll(A,-1,axis=0)-A; db=np.roll(B,-1,axis=0)-B
    s=0.0
    for i in range(len(A)):
        for j in range(len(B)):
            r=ma[i]-mb[j]; r3=float(np.linalg.norm(r))**3
            if r3>1e-300: s+=float(np.dot(np.cross(da[i],db[j]),r))/r3
    return s/(4*math.pi)

def min_intercomponent_segment_distance(a,b):
    A=np.asarray(a,float); B=np.asarray(b,float); nat=_native()
    if nat is not None: return float(nat.min_intercomponent_segment_distance(A,B))
    best=float('inf')
    for i in range(len(A)):
        for j in range(len(B)):
            best=min(best,segment_distance(A[i],A[(i+1)%len(A)],B[j],B[(j+1)%len(B)]))
    return best

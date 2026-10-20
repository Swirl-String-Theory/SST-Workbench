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

def _triangle_solid_angle(a,b,c):
    """Oriented solid angle of a spherical triangle spanned by 3 vectors.

    Van Oosterom--Strackee atan2 form. The result is in radians.
    """
    na=float(np.linalg.norm(a)); nb=float(np.linalg.norm(b)); nc=float(np.linalg.norm(c))
    if min(na,nb,nc)<=1e-15:
        return 0.0
    num=float(np.dot(a,np.cross(b,c)))
    den=na*nb*nc + float(a@b)*nc + float(b@c)*na + float(c@a)*nb
    return 2.0*math.atan2(num,den)

def _segment_pair_solid_angle(a0,a1,b0,b1):
    """Exact Gauss solid angle for two oriented straight segments."""
    r00=b0-a0; r10=b0-a1; r11=b1-a1; r01=b1-a0
    return _triangle_solid_angle(r00,r10,r11) + _triangle_solid_angle(r00,r11,r01)

def writhe_acn(points):
    """Exact polygonal writhe and average crossing number.

    Each segment pair is integrated analytically through its oriented solid
    angle instead of midpoint quadrature. This makes the discrete observable
    appropriate for the Cantarella polygon-vs-smooth writhe convergence gate.
    Both outputs are dimensionless.
    """
    p=np.asarray(points,float); nat=_native()
    if nat is not None and hasattr(nat,'writhe_acn_exact'):
        w,a=nat.writhe_acn_exact(p); return float(w),float(a)
    n=len(p); wr=0.0; acn=0.0
    for i in range(n):
        a0=p[i]; a1=p[(i+1)%n]
        for j in range(i+1,n):
            if cyclic_sep(i,j,n)<=1: continue
            omega=_segment_pair_solid_angle(a0,a1,p[j],p[(j+1)%n])
            wr += 2.0*omega; acn += 2.0*abs(omega)
    c=1.0/(4.0*math.pi)
    return wr*c,acn*c

def linking_number(a,b):
    """Exact polygonal Gauss linking integral (dimensionless)."""
    A=np.asarray(a,float); B=np.asarray(b,float); nat=_native()
    if nat is not None and hasattr(nat,'linking_number_exact'):
        return float(nat.linking_number_exact(A,B))
    s=0.0
    for i in range(len(A)):
        a0=A[i]; a1=A[(i+1)%len(A)]
        for j in range(len(B)):
            s += _segment_pair_solid_angle(a0,a1,B[j],B[(j+1)%len(B)])
    return s/(4.0*math.pi)

def min_intercomponent_segment_distance(a,b):
    A=np.asarray(a,float); B=np.asarray(b,float); nat=_native()
    if nat is not None: return float(nat.min_intercomponent_segment_distance(A,B))
    best=float('inf')
    for i in range(len(A)):
        for j in range(len(B)):
            best=min(best,segment_distance(A[i],A[(i+1)%len(A)],B[j],B[(j+1)%len(B)]))
    return best

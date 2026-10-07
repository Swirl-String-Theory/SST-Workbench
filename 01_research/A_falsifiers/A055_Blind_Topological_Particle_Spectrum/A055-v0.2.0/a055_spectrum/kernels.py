from __future__ import annotations
import math

def _sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def _mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def _dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _norm(a): return math.sqrt(_dot(a,a))
def _mid(a,b): return ((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2)
def _circ_sep(i,j,n):
    d=abs(i-j); return min(d,n-d)

def _segment_distance(p1,q1,p2,q2):
    # Ericson-style closest points of two finite 3-D segments.
    d1=_sub(q1,p1); d2=_sub(q2,p2); r=_sub(p1,p2)
    a=_dot(d1,d1); e=_dot(d2,d2); f=_dot(d2,r); eps=1e-15
    if a<=eps and e<=eps: return _norm(r)
    if a<=eps:
        s=0.0; t=max(0.0,min(1.0,f/e))
    else:
        c=_dot(d1,r)
        if e<=eps:
            t=0.0; s=max(0.0,min(1.0,-c/a))
        else:
            b=_dot(d1,d2); den=a*e-b*b
            s=0.0 if abs(den)<=eps else max(0.0,min(1.0,(b*f-c*e)/den))
            t=(b*s+f)/e
            if t<0.0: t=0.0; s=max(0.0,min(1.0,-c/a))
            elif t>1.0: t=1.0; s=max(0.0,min(1.0,(b-c)/a))
    return _norm(_sub(_add(p1,_mul(d1,s)),_add(p2,_mul(d2,t))))

def measure_python(components, core=0.03, arclength_exclusion_fraction=0.08):
    segs=[]; total=0.0; bend=0.0; comp_lengths=[]
    for ci,c in enumerate(components):
        n=len(c); lengths=[_norm(_sub(c[(i+1)%n],c[i])) for i in range(n)]
        L=sum(lengths); comp_lengths.append(L); total+=L
        cum=0.0
        for i,ds in enumerate(lengths):
            a=c[i]; b=c[(i+1)%n]; dl=_sub(b,a)
            segs.append((ci,i,n,_mid(a,b),dl,a,b,cum+0.5*ds,L)); cum+=ds
        for i in range(n):
            v1=_sub(c[i],c[(i-1)%n]); v2=_sub(c[(i+1)%n],c[i])
            n1=_norm(v1); n2=_norm(v2)
            if n1*n2>1e-15:
                co=max(-1.0,min(1.0,_dot(v1,v2)/(n1*n2)))
                ang=math.acos(co); bend += ang*ang/(0.5*(n1+n2)+1e-15)

    min_d=float("inf")
    for i in range(len(segs)):
        ci,ii,ni,mi,dli,a1,b1,s1,L1=segs[i]
        for j in range(i+1,len(segs)):
            cj,ij,nj,mj,dlj,a2,b2,s2,L2=segs[j]
            if ci==cj:
                ds=abs(s1-s2); arc=min(ds,L1-ds)
                if arc < float(arclength_exclusion_fraction)*L1: continue
            d=_segment_distance(a1,b1,a2,b2)
            if d<min_d: min_d=d
    if not math.isfinite(min_d): min_d=0.0

    neumann=0.0; writhe=0.0
    k=len(components); link=[[0.0]*k for _ in range(k)]
    for i in range(len(segs)):
        ci,ii,ni,mi,dli,*_=segs[i]
        for j in range(i+1,len(segs)):
            cj,ij,nj,mj,dlj,*_=segs[j]
            if ci==cj and _circ_sep(ii,ij,ni)<=1: continue
            r=_sub(mi,mj); bare_r2=_dot(r,r)
            reg_r2=bare_r2+core*core
            neumann += _dot(dli,dlj)/math.sqrt(reg_r2)
            if bare_r2<=1e-24: continue
            # Writhe/linking are topological/geometric Gauss integrals and are
            # deliberately UNREGULARIZED in v0.1.2.
            g=_dot(r,_cross(dli,dlj))/(bare_r2**1.5)/(4*math.pi)
            if ci==cj: writhe += 2.0*g
            else: link[ci][cj]+=g; link[cj][ci]+=g
    residuals=[]; strength=0.0; integer_strength=0.0
    for i in range(k):
        for j in range(i+1,k):
            x=link[i][j]; strength+=abs(x); integer_strength+=abs(round(x)); residuals.append(abs(x-round(x)))
    mean_seg=total/max(1,len(segs))
    return {"total_length":total,"bend_energy":bend,"min_distance":min_d,
            "mean_segment":mean_seg,"contact_ratio":min_d/(mean_seg+1e-15),
            "neumann_energy":neumann,"abs_neumann_energy":abs(neumann),
            "writhe":writhe,"abs_writhe":abs(writhe),
            "linking_strength":strength,"linking_integer_strength":integer_strength,
            "linking_residual":sum(residuals)/len(residuals) if residuals else 0.0,
            "component_count":k,"linking_matrix":link,
            "arclength_exclusion_fraction":float(arclength_exclusion_fraction)}

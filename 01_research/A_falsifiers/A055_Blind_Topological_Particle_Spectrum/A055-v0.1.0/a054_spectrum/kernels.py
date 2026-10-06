from __future__ import annotations
import math

def _sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _norm(a): return math.sqrt(_dot(a,a))
def _mid(a,b): return ((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2)
def _circ_sep(i,j,n):
    d=abs(i-j); return min(d,n-d)

def measure_python(components, core=0.03):
    segs=[]; total=0.0; bend=0.0
    for ci,c in enumerate(components):
        n=len(c)
        for i in range(n):
            a=c[i]; b=c[(i+1)%n]; dl=_sub(b,a); ds=_norm(dl); total+=ds
            segs.append((ci,i,n,_mid(a,b),dl))
        for i in range(n):
            v1=_sub(c[i],c[(i-1)%n]); v2=_sub(c[(i+1)%n],c[i])
            n1=_norm(v1); n2=_norm(v2)
            if n1*n2>1e-15:
                co=max(-1.0,min(1.0,_dot(v1,v2)/(n1*n2)))
                ang=math.acos(co)
                bend += ang*ang/(0.5*(n1+n2)+1e-15)

    min_d=float("inf")
    for ca,a in enumerate(components):
        for ia,pa in enumerate(a):
            for cb in range(ca,len(components)):
                b=components[cb]; start=ia+1 if cb==ca else 0
                for ib in range(start,len(b)):
                    if ca==cb and _circ_sep(ia,ib,len(a))<=2: continue
                    d=_norm(_sub(pa,b[ib]))
                    if d<min_d: min_d=d
    if not math.isfinite(min_d): min_d=0.0

    neumann=0.0; writhe=0.0
    k=len(components); link=[[0.0]*k for _ in range(k)]
    for i in range(len(segs)):
        ci,ii,ni,mi,dli=segs[i]
        for j in range(i+1,len(segs)):
            cj,ij,nj,mj,dlj=segs[j]
            if ci==cj and _circ_sep(ii,ij,ni)<=1: continue
            r=_sub(mi,mj); r2=_dot(r,r)+core*core
            neumann += _dot(dli,dlj)/math.sqrt(r2)
            g=_dot(r,_cross(dli,dlj))/(r2**1.5)/(4*math.pi)
            if ci==cj:
                writhe += 2.0*g
            else:
                link[ci][cj]+=g; link[cj][ci]+=g
    mean_seg=total/max(1,len(segs))
    residuals=[]; strength=0.0
    for i in range(k):
        for j in range(i+1,k):
            strength += abs(link[i][j])
            residuals.append(abs(link[i][j]-round(link[i][j])))
    return {
        "total_length":total,
        "bend_energy":bend,
        "min_distance":min_d,
        "mean_segment":mean_seg,
        "contact_ratio":min_d/(mean_seg+1e-15),
        "neumann_energy":neumann,
        "abs_neumann_energy":abs(neumann),
        "writhe":writhe,
        "abs_writhe":abs(writhe),
        "linking_strength":strength,
        "linking_residual":sum(residuals)/len(residuals) if residuals else 0.0,
        "component_count":k,
        "linking_matrix":link
    }

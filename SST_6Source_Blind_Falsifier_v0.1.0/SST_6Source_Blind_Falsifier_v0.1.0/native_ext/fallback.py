from __future__ import annotations
import math
import numpy as np


def _segments(vertices: np.ndarray, offsets: list[int]):
    out=[]
    for c,(lo,hi) in enumerate(zip(offsets[:-1],offsets[1:])):
        p=np.asarray(vertices[lo:hi],float)
        q=np.roll(p,-1,axis=0)
        dl=q-p
        mid=(p+q)*0.5
        ln=np.linalg.norm(dl,axis=1)
        t=dl/np.maximum(ln[:,None],1e-300)
        for i in range(len(p)):
            out.append((p[i],q[i],mid[i],dl[i],t[i],c,i,len(p)))
    return out


def biot_savart_velocity(queries, vertices, offsets, gamma, core):
    q=np.asarray(queries,float)
    u=np.zeros_like(q)
    fac=float(gamma)/(4*math.pi)
    a2=float(core)**2
    for _,_,mid,dl,_,_,_,_ in _segments(np.asarray(vertices,float),list(offsets)):
        r=q-mid
        den=(np.sum(r*r,axis=1)+a2)**1.5
        u += fac*np.cross(np.broadcast_to(dl,q.shape),r)/den[:,None]
    return u


def regularized_energy(vertices, offsets, rho, gamma, core):
    seg=_segments(np.asarray(vertices,float),list(offsets))
    mids=np.array([s[2] for s in seg]); dls=np.array([s[3] for s in seg])
    total=0.0; a2=float(core)**2
    for i in range(len(seg)):
        r=mids[i]-mids
        den=np.sqrt(np.sum(r*r,axis=1)+a2)
        total += np.sum((dls[i]@dls.T)/den)
    return float(rho)*float(gamma)**2/(8*math.pi)*float(total)


def gauss_linking_components(vertices, offsets, comp_a, comp_b):
    seg=_segments(np.asarray(vertices,float),list(offsets))
    a=[s for s in seg if s[5]==comp_a]; b=[s for s in seg if s[5]==comp_b]
    total=0.0
    for sa in a:
        for sb in b:
            r=sa[2]-sb[2]; r2=float(r@r)
            if r2<=1e-30: continue
            total += float(np.dot(np.cross(sa[3],sb[3]),r))/(r2*math.sqrt(r2))
    return total/(4*math.pi)


def gauss_writhe_component(vertices, offsets, comp):
    seg=[s for s in _segments(np.asarray(vertices,float),list(offsets)) if s[5]==comp]
    n=len(seg); total=0.0
    for i in range(n):
        for j in range(n):
            if i==j: continue
            d=min(abs(i-j),n-abs(i-j))
            if d<=1: continue
            r=seg[i][2]-seg[j][2]; r2=float(r@r)
            if r2<=1e-30: continue
            total += float(np.dot(np.cross(seg[i][3],seg[j][3]),r))/(r2*math.sqrt(r2))
    return total/(4*math.pi)


def _seg_dist(p1,q1,p2,q2):
    # robust closest points from Real-Time Collision Detection
    eps=1e-15
    d1=q1-p1; d2=q2-p2; r=p1-p2
    a=float(d1@d1); e=float(d2@d2); f=float(d2@r)
    if a<=eps and e<=eps: return float(np.linalg.norm(r))
    if a<=eps:
        s=0.0; t=float(np.clip(f/e,0,1))
    else:
        c=float(d1@r)
        if e<=eps:
            t=0.0; s=float(np.clip(-c/a,0,1))
        else:
            b=float(d1@d2); den=a*e-b*b
            s=float(np.clip((b*f-c*e)/den,0,1)) if abs(den)>eps else 0.0
            t=(b*s+f)/e
            if t<0: t=0.0; s=float(np.clip(-c/a,0,1))
            elif t>1: t=1.0; s=float(np.clip((b-c)/a,0,1))
    return float(np.linalg.norm((p1+d1*s)-(p2+d2*t)))


def nearest_segment_contacts(vertices, offsets, adjacency_exclusion=3, top_k=32):
    seg=_segments(np.asarray(vertices,float),list(offsets)); rec=[]
    for i,a in enumerate(seg):
        for b in seg[i+1:]:
            if a[5]==b[5]:
                d=min(abs(a[6]-b[6]),a[7]-abs(a[6]-b[6]))
                if d<=adjacency_exclusion: continue
            rec.append({"distance":_seg_dist(a[0],a[1],b[0],b[1]),"tangent_dot":float(a[4]@b[4]),"comp_a":a[5],"seg_a":a[6],"comp_b":b[5],"seg_b":b[6]})
    rec.sort(key=lambda r:r["distance"])
    return rec[:top_k]

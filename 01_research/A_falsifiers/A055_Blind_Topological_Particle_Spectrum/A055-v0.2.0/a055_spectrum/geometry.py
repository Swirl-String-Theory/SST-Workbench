from __future__ import annotations
import math, random, hashlib
import networkx as nx
import numpy as np
from .atlas import component_cycles, validate_pd
from .util import canonical

def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def norm(a): return math.sqrt(a[0]*a[0]+a[1]*a[1]+a[2]*a[2])
def dist(a,b): return norm(sub(a,b))

def _seed(rec, public_seed, replicate):
    payload={"pd":rec["pd"],"seed":public_seed,"replicate":replicate}
    return int(hashlib.sha256(canonical(payload)).hexdigest()[:16],16)

def _resample_closed(points, n):
    if len(points)<3: raise ValueError("too few points")
    p=[points[0]]
    for q in points[1:]:
        if dist(q,p[-1])>1e-13: p.append(q)
    if dist(p[0],p[-1])<1e-13: p.pop()
    seg=[dist(p[i],p[(i+1)%len(p)]) for i in range(len(p))]
    total=sum(seg)
    if total<=0: raise ValueError("zero length")
    cum=[0.0]
    for s in seg: cum.append(cum[-1]+s)
    out=[]; j=0
    for k in range(n):
        target=total*k/n
        while j+1<len(cum) and cum[j+1]<target: j+=1
        i=j%len(p); s=seg[i]
        t=0.0 if s<=1e-15 else (target-cum[j])/s
        a=p[i]; b=p[(i+1)%len(p)]
        out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*(b[2]-a[2])))
    return out

def _normalize2(v):
    d=math.hypot(v[0],v[1])
    return (1.0,0.0) if d<=1e-15 else (v[0]/d,v[1]/d)

def _planar_pd_positions(rec):
    """Straight-line planar realization of the PD rotation system.

    Crossing nodes have the PD tuple's cyclic port order.  Each PD edge label
    is subdivided by a degree-2 node, eliminating multiedges for NetworkX's
    PlanarEmbedding.  No random global routing lanes are used in v0.1.2.
    """
    occ=validate_pd(rec); pd=rec["pd"]
    E=nx.PlanarEmbedding()
    for ci,x in enumerate(pd):
        u=("c",ci); ns=[("e",int(lbl)) for lbl in x]
        E.add_half_edge_first(u,ns[0]); ref=ns[0]
        for v in ns[1:]:
            E.add_half_edge_cw(u,v,ref); ref=v
    for lbl,nodes in occ.items():
        u=("e",int(lbl)); ns=[("c",int(ci)) for ci,_ in nodes]
        E.add_half_edge_first(u,ns[0])
        if len(ns)>1: E.add_half_edge_cw(u,ns[1],ns[0])
    E.check_structure()
    pos=nx.combinatorial_embedding_to_pos(E)
    xs=[float(p[0]) for p in pos.values()]; ys=[float(p[1]) for p in pos.values()]
    cx=sum(xs)/len(xs); cy=sum(ys)/len(ys)
    span=max(max(xs)-min(xs),max(ys)-min(ys),1.0)
    return {u:((float(p[0])-cx)/span,(float(p[1])-cy)/span) for u,p in pos.items()}

def _fourier_smooth_closed(points, work_n=512, sigma_fraction=0.010):
    """Periodic C-infinity low-pass smoothing of an arclength-resampled loop."""
    work_n=max(128,int(work_n))
    p=np.asarray(_resample_closed(points,work_n),dtype=float)
    F=np.fft.fft(p,axis=0)
    harmonic=np.fft.fftfreq(work_n)*work_n
    filt=np.exp(-2.0*(math.pi**2)*(float(sigma_fraction)**2)*(harmonic**2))
    q=np.fft.ifft(F*filt[:,None],axis=0).real
    return [tuple(map(float,row)) for row in q]

def build_embedding(rec, points_per_component=160, public_seed="A055-v0.1.2", replicate=0):
    """Topology-preserving PD screening embedding.

    Replicates vary only local crossing height, port radius and smooth-kernel
    width.  They never permute global routing lanes; the planar PD rotation
    system remains fixed.
    """
    rng=random.Random(_seed(rec,public_seed,replicate))
    pd=rec["pd"]; pos=_planar_pd_positions(rec)
    h=0.026*(1.0+rng.uniform(-0.06,0.06))
    port_fraction=0.145*(1.0+rng.uniform(-0.04,0.04))
    sigma=0.010*(1.0+rng.uniform(-0.08,0.08))
    ports={}
    for ci,x in enumerate(pd):
        c=pos[("c",ci)]
        mind=min(math.hypot(pos[("e",int(lbl))][0]-c[0],pos[("e",int(lbl))][1]-c[1]) for lbl in x)
        radius=port_fraction*mind
        for pi,lbl in enumerate(x):
            q=pos[("e",int(lbl))]; u=_normalize2((q[0]-c[0],q[1]-c[1]))
            # KnotTheory PD X[a,b,c,d]: opposite ports form the two strands.
            # Which strand is chosen over only mirrors the global convention;
            # absolute linking calibrations are invariant under that choice.
            z=h if pi in (0,2) else -h
            ports[(ci,pi)]=(c[0]+radius*u[0],c[1]+radius*u[1],z)
    comps=[]
    for segs in component_cycles(rec):
        pts=[]
        for typ,a,b in segs:
            if typ=="cross":
                c=pos[("c",a[0])]; z=ports[a][2]
                poly=[ports[a],(c[0],c[1],z),ports[b]]
            else:
                lbl=int(pd[a[0]][a[1]]); e=pos[("e",lbl)]
                poly=[ports[a],(e[0],e[1],0.0),ports[b]]
            if pts: poly=poly[1:]
            pts.extend(poly)
        smoothed=_fourier_smooth_closed(pts,work_n=max(512,4*int(points_per_component)),sigma_fraction=sigma)
        comps.append(_resample_closed(smoothed,int(points_per_component)))

    allp=[p for c in comps for p in c]
    cen=tuple(sum(p[k] for p in allp)/len(allp) for k in range(3))
    comps=[[(p[0]-cen[0],p[1]-cen[1],p[2]-cen[2]) for p in c] for c in comps]
    lens=[sum(dist(c[i],c[(i+1)%len(c)]) for i in range(len(c))) for c in comps]
    scale=len(comps)/(sum(lens)+1e-15) # mean component length = 1
    return [[(p[0]*scale,p[1]*scale,p[2]*scale) for p in c] for c in comps]

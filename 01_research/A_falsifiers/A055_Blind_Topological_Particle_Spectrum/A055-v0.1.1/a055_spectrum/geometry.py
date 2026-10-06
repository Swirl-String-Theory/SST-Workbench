from __future__ import annotations
import math, random, hashlib, json
from .atlas import component_cycles
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
    # remove consecutive duplicates
    p=[points[0]]
    for q in points[1:]:
        if dist(q,p[-1])>1e-12: p.append(q)
    if dist(p[0],p[-1])<1e-12: p.pop()
    seg=[dist(p[i],p[(i+1)%len(p)]) for i in range(len(p))]
    total=sum(seg)
    if total<=0: raise ValueError("zero length")
    cum=[0.0]
    for s in seg: cum.append(cum[-1]+s)
    out=[]
    j=0
    for k in range(n):
        target=total*k/n
        while j+1 < len(cum) and cum[j+1] < target: j+=1
        i=j%len(p); s=seg[i]
        t=0.0 if s<=1e-15 else (target-cum[j])/s
        a=p[i]; b=p[(i+1)%len(p)]
        out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*(b[2]-a[2])))
    return out

def build_embedding(rec, points_per_component=64, public_seed="A055", replicate=0):
    rng=random.Random(_seed(rec,public_seed,replicate))
    pd=rec["pd"]; ncr=len(pd)
    slots=list(range(ncr)); rng.shuffle(slots)
    lane_labels=list(range(1,2*ncr+1)); rng.shuffle(lane_labels)
    lane_rank={lbl:i for i,lbl in enumerate(lane_labels)}
    centers={}; bases={}; nodepos={}
    R=1.0; eps=0.12; h=0.07
    for ci in range(ncr):
        theta=2*math.pi*slots[ci]/max(1,ncr)
        center=(R*math.cos(theta),R*math.sin(theta),0.0)
        phi=theta+rng.uniform(-0.65,0.65)
        ex=(math.cos(phi),math.sin(phi),0.0)
        ey=(-math.sin(phi),math.cos(phi),0.0)
        centers[ci]=center; bases[ci]=(ex,ey)
        offsets=[mul(ex,-eps),mul(ey,-eps),mul(ex,eps),mul(ey,eps)]
        zs=[h,-h,h,-h]
        for pi in range(4):
            q=add(center,offsets[pi]); nodepos[(ci,pi)]=(q[0],q[1],zs[pi])

    def radial(ci):
        c=centers[ci]; d=math.hypot(c[0],c[1]) or 1.0
        return (c[0]/d,c[1]/d,0.0)

    def cross_poly(a,b):
        za=nodepos[a][2]
        c=centers[a[0]]
        return [nodepos[a],(c[0],c[1],za),nodepos[b]]

    def edge_poly(a,b):
        lbl=pd[a[0]][a[1]]
        rank=lane_rank[lbl]
        zlane=(rank-(2*ncr-1)/2)*0.17
        rlane=1.55+0.025*rank
        ra=radial(a[0]); rb=radial(b[0])
        pa=nodepos[a]; pb=nodepos[b]
        q1=add(pa,mul(ra,0.22)); q4=add(pb,mul(rb,0.22))
        q2=(rlane*ra[0],rlane*ra[1],zlane)
        q3=(rlane*rb[0],rlane*rb[1],zlane)
        return [pa,q1,q2,q3,q4,pb]

    comps=[]
    for segs in component_cycles(rec):
        pts=[]
        for typ,a,b in segs:
            poly=cross_poly(a,b) if typ=="cross" else edge_poly(a,b)
            if pts: poly=poly[1:]
            pts.extend(poly)
        comps.append(_resample_closed(pts,points_per_component))

    # center and scale so mean component length is unity
    allp=[p for c in comps for p in c]
    cen=tuple(sum(p[k] for p in allp)/len(allp) for k in range(3))
    comps=[[(p[0]-cen[0],p[1]-cen[1],p[2]-cen[2]) for p in c] for c in comps]
    lens=[]
    for c in comps:
        lens.append(sum(dist(c[i],c[(i+1)%len(c)]) for i in range(len(c))))
    scale=(len(comps)/(sum(lens)+1e-15))
    comps=[[(p[0]*scale,p[1]*scale,p[2]*scale) for p in c] for c in comps]
    return comps

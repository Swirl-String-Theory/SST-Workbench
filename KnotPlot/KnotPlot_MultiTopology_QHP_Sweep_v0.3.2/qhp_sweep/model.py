from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,math,re
import numpy as np

KNOT_RE=re.compile(r"^\d+\.\d+$")
LINK_RE=re.compile(r"^\d+\.\d+\.\d+$")
TORUS_RE=re.compile(r"^(\d+)[.x,](\d+)$")

@dataclass(frozen=True)
class Topology:
    kind:str
    spec:str
    topo_id:str
    command:str
    components:int
    nbeads:int

def split_csv(s):
    if s is None:return []
    return [x.strip() for x in str(s).split(",") if x.strip()]

def parse_triplet(s,name):
    try:v=[float(x.strip()) for x in str(s).split(",")]
    except Exception as e:raise ValueError(f"{name} must be q,h,p; got {s!r}") from e
    if len(v)!=3 or not all(np.isfinite(v)):
        raise ValueError(f"{name} must contain exactly 3 finite numbers")
    return tuple(v)

def parse_steps(s):
    try:v=[int(x.strip()) for x in str(s).split(",")]
    except Exception as e:raise ValueError("--qhp-steps must be 3 positive integers") from e
    if len(v)!=3 or min(v)<1:raise ValueError("--qhp-steps must be 3 positive integers")
    return tuple(v)

def sanitize(s):
    return re.sub(r"[^A-Za-z0-9_-]+","p",s).strip("_")[:80]

def topology_list(knots,links,torus,beads_per_component,total_beads=None):
    out=[]
    for spec in split_csv(knots):
        if not KNOT_RE.match(spec):raise ValueError(f"Bad knot id {spec!r}; expected e.g. 3.1")
        c=1;n=int(total_beads or beads_per_component*c)
        out.append(Topology("knot",spec,f"KNOT_{sanitize(spec)}",f"load {spec}",c,n))
    for spec in split_csv(links):
        if not LINK_RE.match(spec):raise ValueError(f"Bad link id {spec!r}; expected e.g. 6.3.3")
        _,k,_=map(int,spec.split("."))
        c=max(2,k);n=int(total_beads or beads_per_component*c)
        out.append(Topology("link",spec,f"LINK_{sanitize(spec)}",f"load {spec}",c,n))
    for spec in split_csv(torus):
        m=TORUS_RE.match(spec)
        if not m:raise ValueError(f"Bad torus {spec!r}; expected p.q, e.g. 6.9")
        p,q=map(int,m.groups());c=math.gcd(p,q);n=int(total_beads or beads_per_component*c)
        out.append(Topology("torus",spec,f"TORUS_{p}x{q}",f"torus {p} {q} {n}",c,n))
    seen=set();unique=[]
    for t in out:
        k=(t.kind,t.spec)
        if k in seen:continue
        seen.add(k);unique.append(t)
    if not unique:raise ValueError("No topology supplied. Use --knots, --links and/or --torus.")
    return unique

def qhp_states(qmin,qmax,mode,points,steps):
    lo=np.asarray(qmin,float);hi=np.asarray(qmax,float)
    if np.any(hi<lo):raise ValueError("Every --qhp-max component must be >= --qhp-min")
    out=[]
    if mode=="line":
        if points<2:raise ValueError("--qhp-points must be >=2 in line mode")
        for i,a in enumerate(np.linspace(0,1,points)):
            v=lo+a*(hi-lo)
            out.append({"index":i,"line_alpha":float(a),"q":float(v[0]),"h":float(v[1]),"p":float(v[2]),
                        "grid_index":None})
    elif mode=="grid":
        nq,nh,np_=steps
        for iq,q in enumerate(np.linspace(lo[0],hi[0],nq)):
            for ih,h in enumerate(np.linspace(lo[1],hi[1],nh)):
                for ip,p in enumerate(np.linspace(lo[2],hi[2],np_)):
                    out.append({"index":len(out),"line_alpha":None,"q":float(q),"h":float(h),"p":float(p),
                                "grid_index":[iq,ih,ip]})
    else:raise ValueError(mode)
    return out

def auto_checkpoints(max_ago):
    if max_ago<100:raise ValueError("--max-ago must be >=100")
    base=[0,10,25,50,100,250,500,1000,2000,4000,6000,8000,10000]
    pts={x for x in base if x<=max_ago}
    for f in (.125,.15,.20,.25,.30,.40,.50,.60,.75,1.0):
        x=int(round(max_ago*f/100.0))*100
        if 0<x<=max_ago:pts.add(x)
    pts.add(max_ago);pts.add(0)
    return sorted(pts)

def parse_checkpoints(s,max_ago):
    if not s or str(s).lower()=="auto":return auto_checkpoints(max_ago)
    try:pts=sorted(set(int(x.strip()) for x in str(s).split(",") if x.strip()))
    except Exception as e:raise ValueError("--checkpoints must be auto or comma-separated integers") from e
    pts=[x for x in pts if 0<=x<=max_ago]
    if 0 not in pts:pts=[0]+pts
    if max_ago not in pts:pts.append(max_ago)
    return sorted(set(pts))

def campaign_hash(d):
    raw=json.dumps(d,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()[:12]


def clean_component(a):
    a=np.asarray(a,float)
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<3:
        raise ValueError("component must be Nx3 with at least 3 vertices")
    scale=max(float(np.ptp(a,axis=0).max()),1.0)
    if np.linalg.norm(a[0]-a[-1])<=1e-12*scale:
        a=a[:-1]
    return a

def closed_arclength(a):
    a=clean_component(a)
    return float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())

def parse_multicomponent_coords(path):
    text=Path(path).read_text(encoding="utf-8",errors="ignore")
    comps=[];cur=[]
    for raw in text.splitlines():
        s=raw.strip()
        if not s:
            if cur:
                comps.append(clean_component(np.asarray(cur,float)));cur=[]
            continue
        vals=[]
        for tok in s.replace(","," ").split():
            try:vals.append(float(tok))
            except Exception:pass
        if len(vals)>=3:cur.append(vals[:3])
    if cur:comps.append(clean_component(np.asarray(cur,float)))
    if not comps:raise ValueError(f"No components parsed from {path}")
    return comps

def allocate_beads_by_length(lengths,total,min_per_component=12):
    """Allocate an exact total bead budget by measured component arclength.

    Pure proportional allocation is used whenever every component naturally
    receives at least ``min_per_component`` beads.  The minimum is therefore
    only a safety floor, not an up-front reservation.  If a very short component
    would fall below the floor, it is clamped and the remaining budget is
    re-apportioned proportionally over the remaining components.
    """
    L=np.asarray(lengths,float)
    if len(L)<1 or np.any(~np.isfinite(L)) or np.any(L<=0):
        raise ValueError("component lengths must be positive finite values")
    total=int(total);m=int(min_per_component);c=len(L)
    if total<c*m:
        raise ValueError(f"total beads {total} is below {c}*min_per_component({m})={c*m}")

    alloc=np.zeros(c,dtype=int)
    active=list(range(c))
    remaining=total

    # Water-fill only components whose pure proportional share violates the floor.
    while active:
        denom=float(L[active].sum())
        ideal={i:remaining*float(L[i])/denom for i in active}
        small=[i for i in active if ideal[i] < m]
        if not small:
            break
        for i in sorted(small):
            alloc[i]=m
            remaining-=m
            active.remove(i)

    if active:
        denom=float(L[active].sum())
        ideals={i:remaining*float(L[i])/denom for i in active}
        for i in active:
            alloc[i]=int(np.floor(ideals[i]))
        left=total-int(alloc.sum())
        order=sorted(
            active,
            key=lambda i:(-(ideals[i]-np.floor(ideals[i])),-float(L[i]),i)
        )
        for i in order[:left]:
            alloc[i]+=1

    assert int(alloc.sum())==total
    assert np.all(alloc>=m)
    return alloc.tolist()

def resample_closed_component(a,n):
    a=clean_component(a);n=int(n)
    seg=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
    if np.any(seg<=0):raise ValueError("zero-length source segment")
    s=np.r_[0.0,np.cumsum(seg)]
    aa=np.vstack([a,a[0]])
    t=np.linspace(0,s[-1],n,endpoint=False)
    return np.column_stack([np.interp(t,s,aa[:,j]) for j in range(3)])

def write_multicomponent_coords(path,components):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    chunks=[]
    for a in components:
        chunks.append("\n".join(" ".join(f"{x:.17g}" for x in row) for row in np.asarray(a,float)))
    p.write_text("\n\n".join(chunks)+"\n",encoding="utf-8")

def prepare_components_from_coords(raw_path,prepared_path,total_beads,min_per_component=12):
    comps=parse_multicomponent_coords(raw_path)
    lengths=[closed_arclength(c) for c in comps]
    alloc=allocate_beads_by_length(lengths,total_beads,min_per_component)
    rr=[resample_closed_component(c,n) for c,n in zip(comps,alloc)]
    write_multicomponent_coords(prepared_path,rr)
    out={
        "raw_path":str(raw_path),"prepared_path":str(prepared_path),
        "component_count":len(comps),"total_beads":int(total_beads),
        "min_beads_per_component":int(min_per_component),
        "component_lengths":lengths,
        "length_fractions":[float(x/sum(lengths)) for x in lengths],
        "allocated_beads":alloc,
        "allocated_fractions":[float(x/total_beads) for x in alloc],
        "allocation_sum":sum(alloc),
        "method":"minimum-reserved Hamilton largest remainder on physical closed arclength",
    }
    return out


UNLINK_RE=re.compile(r"^0\.(\d+)\.1$")

def is_unlink_control(kind,spec):
    if kind!="link":
        return False
    z=UNLINK_RE.match(spec)
    return bool(z and int(z.group(1))>=2)

def synthesize_unlink_components(ncomp,total_beads,min_per_component=12,radius=1.0,spacing=3.25):
    """Deterministic 0.n.1 null control: n disjoint equal-radius planar circles."""
    ncomp=int(ncomp); total_beads=int(total_beads)
    if ncomp<2:
        raise ValueError("unlink control requires >=2 components")
    lengths=[2.0*math.pi*float(radius)]*ncomp
    alloc=allocate_beads_by_length(lengths,total_beads,min_per_component)
    comps=[]
    x0=-0.5*float(spacing)*(ncomp-1)
    for i,n in enumerate(alloc):
        u=np.linspace(0.0,2.0*np.pi,int(n),endpoint=False)
        comps.append(np.c_[x0+i*spacing+radius*np.cos(u),
                           radius*np.sin(u),
                           np.zeros_like(u)])
    return comps,{
        "component_count":ncomp,
        "total_beads":total_beads,
        "component_lengths":lengths,
        "length_fractions":[1.0/ncomp]*ncomp,
        "allocated_beads":alloc,
        "allocated_fractions":[float(x/total_beads) for x in alloc],
        "allocation_sum":sum(alloc),
        "method":"synthetic deterministic unlink: separated equal-radius planar circles",
        "radius":float(radius),
        "spacing":float(spacing)
    }

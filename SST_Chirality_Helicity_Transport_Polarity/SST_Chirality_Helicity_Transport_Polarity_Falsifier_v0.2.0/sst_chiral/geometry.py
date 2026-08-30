from __future__ import annotations
import math, re
from pathlib import Path
import numpy as np

_FLOAT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
SUPPORTED={".txt",".xyz",".dat",".csv",".vect",".npy",".npz"}


def _as_component(a: np.ndarray) -> np.ndarray:
    a=np.asarray(a,dtype=np.float64)
    if a.ndim!=2 or a.shape[1]!=3: raise ValueError(f"expected (N,3), got {a.shape}")
    if len(a)<8: raise ValueError("each component needs at least 8 vertices")
    if not np.isfinite(a).all(): raise ValueError("non-finite coordinates")
    scale=max(1.0,float(np.ptp(a,axis=0).max()))
    if np.linalg.norm(a[0]-a[-1])<=1e-12*scale: a=a[:-1]
    keep=np.ones(len(a),dtype=bool)
    d=np.linalg.norm(a[1:]-a[:-1],axis=1)
    keep[1:]=d>1e-14*scale
    a=a[keep]
    if len(a)<8: raise ValueError("too many duplicate vertices")
    return np.ascontiguousarray(a)


def pack_components(comps: list[np.ndarray]) -> tuple[np.ndarray,np.ndarray]:
    cc=[_as_component(c) for c in comps]
    offsets=[0]
    for c in cc: offsets.append(offsets[-1]+len(c))
    return np.ascontiguousarray(np.vstack(cc),dtype=np.float64), np.ascontiguousarray(np.array(offsets,dtype=np.int64))


def unpack_components(packed: np.ndarray, offsets: np.ndarray) -> list[np.ndarray]:
    x=np.asarray(packed,dtype=np.float64); o=np.asarray(offsets,dtype=np.int64)
    if o.ndim!=1 or len(o)<2 or o[0]!=0 or o[-1]!=len(x): raise ValueError("invalid offsets")
    return [_as_component(x[o[i]:o[i+1]]) for i in range(len(o)-1)]


def geometry_lengths(comps: list[np.ndarray]) -> np.ndarray:
    out=[]
    for c in comps:
        out.append(float(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum()))
    return np.array(out,float)


def total_length(comps: list[np.ndarray]) -> float:
    return float(geometry_lengths(comps).sum())


def normalize_geometry(comps: list[np.ndarray]) -> tuple[list[np.ndarray],dict]:
    cc=[_as_component(c).copy() for c in comps]
    packed=np.vstack(cc)
    centroid=packed.mean(axis=0)
    cc=[c-centroid for c in cc]
    L=total_length(cc)
    if not np.isfinite(L) or L<=0: raise ValueError("invalid total length")
    cc=[np.ascontiguousarray(c/L) for c in cc]
    return cc,{"input_centroid":centroid.tolist(),"input_total_length":L,"n_components":len(cc)}


def _resample_closed(c: np.ndarray,n:int)->np.ndarray:
    c=_as_component(c)
    if n<8: raise ValueError("component resolution must be >=8")
    nxt=np.roll(c,-1,axis=0); seg=np.linalg.norm(nxt-c,axis=1)
    if np.any(seg<=0): raise ValueError("zero segment")
    cum=np.concatenate([[0.0],np.cumsum(seg)]); L=cum[-1]
    targets=np.linspace(0,L,n,endpoint=False)
    idx=np.searchsorted(cum,targets,side="right")-1; idx=np.clip(idx,0,len(c)-1)
    f=(targets-cum[idx])/seg[idx]
    return np.ascontiguousarray(c[idx]+f[:,None]*(nxt[idx]-c[idx]))


def _allocate_points(lengths: np.ndarray,total_n:int,min_per:int)->list[int]:
    m=len(lengths); total_n=max(int(total_n),m*int(min_per)); base=np.full(m,int(min_per),dtype=int)
    remaining=total_n-int(base.sum())
    if remaining>0:
        w=lengths/max(float(lengths.sum()),1e-30); raw=w*remaining; add=np.floor(raw).astype(int); base+=add
        left=remaining-int(add.sum()); frac=raw-add
        for i in np.argsort(-frac)[:left]: base[i]+=1
    return base.tolist()


def resample_geometry(comps:list[np.ndarray],total_n:int,min_per_component:int=24)->list[np.ndarray]:
    lengths=geometry_lengths(comps); alloc=_allocate_points(lengths,total_n,min_per_component)
    return [_resample_closed(c,n) for c,n in zip(comps,alloc)]


def ds_cv_geometry(comps:list[np.ndarray])->float:
    vals=[]
    for c in comps:
        d=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); vals.extend(d.tolist())
    a=np.array(vals,float); return float(np.std(a)/max(np.mean(a),1e-30))


def min_segment_length(comps:list[np.ndarray])->float:
    return min(float(np.min(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1))) for c in comps)


def parity_mirror_physical(comps:list[np.ndarray],axis:int=0)->list[np.ndarray]:
    out=[]
    for c in comps:
        y=np.asarray(c,float).copy(); y[:,axis]*=-1.0
        y=np.concatenate([y[:1],y[:0:-1]],axis=0).copy(); out.append(y)
    packed=np.vstack(out); cen=packed.mean(axis=0); return [np.ascontiguousarray(c-cen) for c in out]


def time_reverse_geometry(comps:list[np.ndarray])->list[np.ndarray]:
    out=[]
    for c in comps:
        y=np.concatenate([c[:1],c[:0:-1]],axis=0).copy(); out.append(y)
    cen=np.vstack(out).mean(axis=0); return [np.ascontiguousarray(c-cen) for c in out]


def frames_component(c:np.ndarray)->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    c=np.asarray(c,float); dm=c-np.roll(c,1,axis=0); dp=np.roll(c,-1,axis=0)-c
    t=dm+dp; t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-30)
    dt=np.roll(t,-1,axis=0)-np.roll(t,1,axis=0); nrm=np.linalg.norm(dt,axis=1)
    n=np.zeros_like(c); good=nrm>1e-10; n[good]=dt[good]/nrm[good,None]
    for i in np.where(~good)[0]:
        ref=np.array([1.,0.,0.]);
        if abs(np.dot(ref,t[i]))>0.85: ref=np.array([0.,1.,0.])
        v=ref-np.dot(ref,t[i])*t[i]; n[i]=v/max(np.linalg.norm(v),1e-30)
    b=np.cross(t,n); b/=np.maximum(np.linalg.norm(b,axis=1)[:,None],1e-30)
    n=np.cross(b,t); n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30)
    seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); ds=0.5*(seg+np.roll(seg,1))
    curvature=np.linalg.norm(dt,axis=1)/np.maximum(np.linalg.norm(np.roll(c,-1,axis=0)-np.roll(c,1,axis=0),axis=1),1e-30)
    return np.ascontiguousarray(t),np.ascontiguousarray(n),np.ascontiguousarray(b),curvature


def frames_geometry(comps:list[np.ndarray])->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    ts=[];ns=[];bs=[];ks=[]
    for c in comps:
        t,n,b,k=frames_component(c); ts.append(t);ns.append(n);bs.append(b);ks.append(k)
    return np.vstack(ts),np.vstack(ns),np.vstack(bs),np.concatenate(ks)


def local_chirality_texture(c:np.ndarray)->np.ndarray:
    """Discrete version of t·(dt/ds × d²t/ds²), parity odd and local."""
    t,_,_,_=frames_component(c)
    seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); ds=float(np.mean(seg))
    dt=(np.roll(t,-1,axis=0)-np.roll(t,1,axis=0))/(2*ds)
    d2t=(np.roll(dt,-1,axis=0)-np.roll(dt,1,axis=0))/(2*ds)
    return np.einsum("ij,ij->i",t,np.cross(dt,d2t))


def _parse_vect(text:str)->list[np.ndarray]:
    lines=[]
    for line in text.splitlines():
        s=line.split("#",1)[0].strip()
        if s: lines.append(s)
    if not lines or lines[0].upper()!="VECT": raise ValueError("not VECT")
    nums=[]
    for line in lines[1:]: nums.extend(_FLOAT.findall(line))
    vals=[float(v) for v in nums]
    if len(vals)<3: raise ValueError("bad VECT header")
    npoly=int(vals[0]); nvert=int(vals[1]); pos=3
    if npoly<1 or nvert<8: raise ValueError("bad VECT counts")
    if len(vals)<pos+2*npoly: raise ValueError("truncated VECT counts")
    vcounts=[abs(int(vals[pos+i])) for i in range(npoly)]; pos+=npoly
    pos+=npoly # color counts
    if sum(vcounts)!=nvert: raise ValueError("VECT vertex count mismatch")
    need=3*nvert
    if len(vals)<pos+need: raise ValueError("truncated VECT vertices")
    arr=np.array(vals[pos:pos+need],float).reshape(nvert,3)
    out=[]; k=0
    for n in vcounts: out.append(_as_component(arr[k:k+n])); k+=n
    return out


def _plain_blocks(text:str)->list[np.ndarray]:
    blocks=[]; cur=[]
    def flush():
        nonlocal cur
        if len(cur)>=8: blocks.append(_as_component(np.array(cur,float)))
        cur=[]
    for line in text.splitlines():
        s=line.strip()
        if not s:
            flush(); continue
        vals=[float(x) for x in _FLOAT.findall(s)]
        if len(vals)==3: cur.append(vals)
        elif len(vals)==4 and abs(vals[0]-round(vals[0]))<1e-9: cur.append(vals[-3:])
        else: flush()
    flush(); return blocks


def _gap_split(c:np.ndarray,gap_factor:float)->list[np.ndarray]:
    c=_as_component(c); d=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1); med=float(np.median(d[d>0]))
    gaps=np.where(d>gap_factor*max(med,1e-30))[0]
    if len(gaps)<2: return [c]
    starts=[int((g+1)%len(c)) for g in gaps]; starts=sorted(starts)
    out=[]
    for i,s in enumerate(starts):
        e=starts[(i+1)%len(starts)]
        part=c[s:e] if e>s else np.vstack([c[s:],c[:e]])
        if len(part)>=8: out.append(_as_component(part))
    return out if len(out)>=2 else [c]


def infer_torus_component_count(name:str)->int|None:
    m=re.search(r"torus[^0-9]*(\d+)[._-](\d+)",Path(name).stem,re.I)
    if not m: return None
    return math.gcd(int(m.group(1)),int(m.group(2)))


def load_geometry(path:str|Path,gap_factor:float=6.0,allow_equal_torus_split:bool=True,reject_ambiguous_links:bool=True)->tuple[list[np.ndarray],dict]:
    path=Path(path); suf=path.suffix.lower(); provenance=""
    if suf==".npz":
        z=np.load(path,allow_pickle=False); comps=unpack_components(z["packed"],z["offsets"]); provenance="npz_offsets"
    elif suf==".npy":
        a=np.load(path,allow_pickle=False)
        if a.ndim==2: comps=[_as_component(a)]
        elif a.ndim==3 and a.shape[2]==3: comps=[_as_component(q) for q in a]
        else: raise ValueError(f"unsupported npy shape {a.shape}")
        provenance="npy"
    else:
        text=path.read_text(encoding="utf-8",errors="ignore")
        if text.lstrip().upper().startswith("VECT"):
            comps=_parse_vect(text); provenance="VECT_counts"
        else:
            comps=_plain_blocks(text); provenance="plain_blocks"
            if not comps: raise ValueError(f"could not parse XYZ components from {path}")
            if len(comps)==1:
                split=_gap_split(comps[0],gap_factor)
                if len(split)>1: comps=split; provenance="gap_split"
    expected=infer_torus_component_count(path.name)
    if expected and expected>1 and len(comps)==1 and allow_equal_torus_split:
        c=comps[0]
        if len(c)%expected==0 and len(c)//expected>=8:
            n=len(c)//expected; comps=[_as_component(c[i*n:(i+1)*n]) for i in range(expected)]; provenance="equal_split_torus_gcd"
    if expected and expected!=len(comps):
        raise ValueError(f"torus filename implies {expected} components but parser found {len(comps)}")
    if reject_ambiguous_links and re.search(r"(^|[_-])link([_.-]|$)",path.stem,re.I) and len(comps)==1:
        raise ValueError("generic link file parsed as one component; refusing ambiguous artificial connector")
    return [_as_component(c) for c in comps],{"component_parse":provenance,"n_components":len(comps),"torus_expected_components":expected}


def save_geometry_npz(path:str|Path,comps:list[np.ndarray])->None:
    packed,offsets=pack_components(comps); np.savez_compressed(path,packed=packed,offsets=offsets)


def load_geometry_npz(path:str|Path)->list[np.ndarray]:
    z=np.load(path,allow_pickle=False); return unpack_components(z["packed"],z["offsets"])


def discover_curves(root:str|Path)->list[Path]:
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(root)
    return sorted([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.lower().startswith("readme")],key=lambda p:str(p).lower())

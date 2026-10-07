from __future__ import annotations
import gzip, json, re
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from .workbench import rewrite_workbench_path
from .util import sha256_file

_AB_RE=re.compile(r'<AB\s+Id="(?P<id>[^"]+)"\s+Conway="(?P<conway>[^"]*)"\s+L="\s*(?P<L>[-+0-9.eE]+)"\s+D="\s*(?P<D>[-+0-9.eE]+)"[^>]*>(?P<body>.*?)</AB>',re.S)
_COEFF_RE=re.compile(r'<Coeff\s+I="\s*(\d+)"\s+A="\s*([^"]+)"\s+B="\s*([^"]+)"\s*/>')

@dataclass
class GilbertAB:
    knot_id:str; conway:str; L:float; D:float
    harmonics:np.ndarray; A:np.ndarray; B:np.ndarray

def _vec(s):
    x=[float(v.strip()) for v in s.split(",")]
    if len(x)!=3: raise ValueError("Expected 3-vector")
    return x

def read_text_maybe_gzip(path):
    p=Path(path)
    if p.suffix.lower()==".gz":
        with gzip.open(p,"rt",encoding="utf-8",errors="replace") as f: return f.read()
    return p.read_text(encoding="utf-8",errors="replace")

def parse_gilbert_ab(path,knot_id):
    text=read_text_maybe_gzip(path); selected=None
    for m in _AB_RE.finditer(text):
        if m.group("id")==knot_id: selected=m; break
    if selected is None: raise KeyError(f"Gilbert AB record {knot_id!r} not found")
    hs=[]; aa=[]; bb=[]
    for c in _COEFF_RE.finditer(selected.group("body")):
        hs.append(int(c.group(1))); aa.append(_vec(c.group(2))); bb.append(_vec(c.group(3)))
    return GilbertAB(knot_id,selected.group("conway"),float(selected.group("L")),float(selected.group("D")),
                     np.asarray(hs,int),np.asarray(aa,float),np.asarray(bb,float))

def sample_gilbert(model,n):
    t=np.linspace(0,2*np.pi,int(n),endpoint=False)
    p=np.zeros((len(t),3),float)
    for h,a,b in zip(model.harmonics,model.A,model.B):
        p += np.cos(h*t)[:,None]*a + np.sin(h*t)[:,None]*b
    return np.ascontiguousarray(p)

def _drop_duplicate_closure(p):
    p=np.asarray(p,float)
    if len(p)>1 and np.linalg.norm(p[0]-p[-1])<1e-12:
        p=p[:-1]
    if len(p)<3:
        raise ValueError("closed curve requires >=3 distinct samples")
    return np.ascontiguousarray(p)

def parse_xyz(path):
    """Read PKLSA/KnotPlot plain XYZ carriers.

    Accepts whitespace- or comma-separated rows, comments after '#', optional
    non-numeric header lines, and extra trailing columns.  The first three
    numeric columns are interpreted as X,Y,Z.  A duplicated closing point is
    removed before arclength resampling.
    """
    rows=[]
    for raw in Path(path).read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw.split("#",1)[0].strip()
        if not line:
            continue
        toks=line.replace(","," ").split()
        if len(toks)<3:
            continue
        try:
            rows.append([float(toks[0]),float(toks[1]),float(toks[2])])
        except ValueError:
            continue
    if len(rows)<3:
        raise ValueError(f"XYZ source has fewer than three numeric rows: {path}")
    return _drop_duplicate_closure(np.asarray(rows,float))

def parse_vect_components(path):
    text=Path(path).read_text(encoding="utf-8",errors="replace")
    lines=[]
    for ln in text.splitlines():
        ln=ln.split("#",1)[0].strip()
        if ln: lines.append(ln)
    toks=" ".join(lines).split()
    if not toks or toks[0].upper()!="VECT": raise ValueError(f"Not a VECT file: {path}")
    pos=1
    npoly,nvert,ncolor=map(int,toks[pos:pos+3]); pos+=3
    counts=[int(x) for x in toks[pos:pos+npoly]]; pos+=npoly
    _colors=[int(x) for x in toks[pos:pos+npoly]]; pos+=npoly
    need=3*nvert
    xyz=np.asarray([float(x) for x in toks[pos:pos+need]],float).reshape(nvert,3)
    comps=[]; k=0
    for cnt in counts:
        n=abs(cnt); c=xyz[k:k+n].copy(); k+=n
        comps.append(_drop_duplicate_closure(c))
    return comps

def resample_closed(points,n):
    p=np.asarray(points,float)
    seg=np.roll(p,-1,axis=0)-p; ds=np.linalg.norm(seg,axis=1)
    if np.any(ds<=0): raise ValueError("duplicate consecutive points")
    s=np.concatenate(([0.0],np.cumsum(ds))); L=float(s[-1])
    target=np.linspace(0,L,int(n),endpoint=False); ext=np.vstack((p,p[0]))
    idx=np.searchsorted(s,target,side="right")-1; idx=np.clip(idx,0,len(p)-1)
    u=(target-s[idx])/ds[idx]
    return np.ascontiguousarray((1-u)[:,None]*ext[idx]+u[:,None]*ext[idx+1])

def polygon_length(p):
    p=np.asarray(p,float)
    return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())

def load_seedset(path,topology_id):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    summary=obj.get("summary",{})
    if summary.get("topology_id")!=topology_id: raise RuntimeError("E011 topology mismatch")
    return obj

def select_provider_anchors(path,provider_groups,topology_id,require_static=True):
    """Return all available preregistered STATIC_READY anchors without crashing on missing providers."""
    obj=load_seedset(path,topology_id); summary=obj.get("summary",{})
    if require_static and not summary.get("static_ready",False):
        raise RuntimeError(f"E011 topology {topology_id} is not STATIC_READY")
    anchors=[]; missing=[]; duplicates={}
    for pg in provider_groups:
        xs=[a for a in obj.get("provider_anchors",[])
            if a.get("provider_group")==pg and a.get("static_ready",False)]
        if len(xs)==1:
            anchors.append(xs[0])
        elif len(xs)==0:
            missing.append(pg)
        else:
            duplicates[pg]=len(xs)
    if duplicates:
        raise RuntimeError("Ambiguous STATIC_READY provider anchors: "+
                           ", ".join(f"{k}={v}" for k,v in sorted(duplicates.items())))
    available=[a.get("provider_group") for a in anchors]
    if len(anchors)==len(tuple(provider_groups)):
        status="FULL_PROVIDER_SET"
    elif len(anchors)==1:
        status="SINGLE_PROVIDER_ONLY"
    elif len(anchors)==0:
        status="NO_PREREGISTERED_PROVIDER"
    else:
        status="PARTIAL_PROVIDER_SET"
    coverage={"status":status,"available_provider_groups":available,
              "missing_provider_groups":missing,"requested_provider_groups":list(provider_groups)}
    return anchors,summary,coverage

def _canonicalize_orientation(points,anchor,sign=1):
    wr=anchor.get("finest_metrics",{}).get("Wr")
    if not isinstance(wr,(int,float)) or wr==0: return points,False
    if (1 if wr>0 else -1)!=(1 if sign>=0 else -1):
        return np.ascontiguousarray(points[::-1]),True
    return points,False

def resolve_knot_provider(anchor,workbench,canonical_writhe_sign=1):
    loc=anchor.get("source_locator",{})
    source=rewrite_workbench_path(loc.get("source_path",""),workbench)
    if not source.exists(): raise FileNotFoundError(f"E011 source missing locally: {source}")
    rep=loc.get("representation")
    if rep=="gilbert_ab_record":
        model=parse_gilbert_ab(source,loc.get("reference_id") or loc.get("variant_id"))
        sampler=lambda n: sample_gilbert(model,n)
    elif rep=="vect":
        comps=parse_vect_components(source)
        if len(comps)!=1:
            raise RuntimeError(f"Knot dynamics requires one-component VECT, got {len(comps)}")
        sampler=lambda n: resample_closed(comps[0],n)
    elif rep=="xyz":
        points=parse_xyz(source)
        sampler=lambda n: resample_closed(points,n)
    else:
        raise RuntimeError(f"Unsupported provider representation: {rep!r}")
    rop=anchor.get("finest_metrics",{}).get("Rop")
    if not isinstance(rop,(int,float)) or rop<=0:
        raise RuntimeError("Provider lacks positive E011 Rop")
    def sample(n):
        p=np.ascontiguousarray(sampler(int(n)),float)
        p,rev=_canonicalize_orientation(p,anchor,int(canonical_writhe_sign))
        Lraw=polygon_length(p); Draw=Lraw/float(rop)
        if Draw<=0: raise RuntimeError("non-positive E011 scale")
        return np.ascontiguousarray(p/Draw),{
            "raw_polygon_length":Lraw,"D_eff_raw":Draw,
            "normalized_polygon_length":Lraw/Draw,"D_normalized":1.0,
            "e011_ropelength":float(rop),"orientation_reversed":bool(rev)
        }
    return {"anchor":anchor,"source_path":source,"source_sha256":sha256_file(source),
            "representation":rep,"sample":sample}

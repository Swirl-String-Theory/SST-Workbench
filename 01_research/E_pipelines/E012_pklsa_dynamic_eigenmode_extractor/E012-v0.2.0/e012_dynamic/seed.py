from __future__ import annotations
import gzip, json, re
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from .paths import rewrite_workbench_path
from .util import sha256_file, polygon_length

_AB_RE = re.compile(
    r'<AB\s+Id="(?P<id>[^"]+)"\s+Conway="(?P<conway>[^"]*)"\s+L="\s*(?P<L>[-+0-9.eE]+)"\s+D="\s*(?P<D>[-+0-9.eE]+)"[^>]*>(?P<body>.*?)</AB>',
    re.S,
)
_COEFF_RE = re.compile(r'<Coeff\s+I="\s*(\d+)"\s+A="\s*([^"]+)"\s+B="\s*([^"]+)"\s*/>')

@dataclass
class GilbertAB:
    knot_id: str
    conway: str
    L: float
    D: float
    harmonics: np.ndarray
    A: np.ndarray
    B: np.ndarray

def _vec(text: str):
    vals=[float(v.strip()) for v in text.split(',')]
    if len(vals)!=3:
        raise ValueError(f'Expected 3-vector, got {text!r}')
    return vals

def read_text_maybe_gzip(path: Path) -> str:
    if path.suffix.lower()=='.gz':
        with gzip.open(path,'rt',encoding='utf-8',errors='replace') as f:
            return f.read()
    return path.read_text(encoding='utf-8',errors='replace')

def parse_gilbert_ab(path: Path, knot_id: str) -> GilbertAB:
    text=read_text_maybe_gzip(path)
    selected=None
    for m in _AB_RE.finditer(text):
        if m.group('id')==knot_id:
            selected=m; break
    if selected is None:
        raise KeyError(f'Gilbert AB record {knot_id!r} not found in {path}')
    hs=[]; aa=[]; bb=[]
    for c in _COEFF_RE.finditer(selected.group('body')):
        hs.append(int(c.group(1))); aa.append(_vec(c.group(2))); bb.append(_vec(c.group(3)))
    if not hs:
        raise ValueError(f'No coefficients in AB record {knot_id!r}')
    return GilbertAB(knot_id=knot_id,conway=selected.group('conway'),L=float(selected.group('L')),
                     D=float(selected.group('D')),harmonics=np.asarray(hs,dtype=int),
                     A=np.asarray(aa,dtype=float),B=np.asarray(bb,dtype=float))

def sample_gilbert(model: GilbertAB, n: int) -> np.ndarray:
    if n < 16: raise ValueError('n must be >=16')
    t=np.linspace(0,2*np.pi,int(n),endpoint=False)
    p=np.zeros((len(t),3),dtype=float)
    for h,a,b in zip(model.harmonics,model.A,model.B):
        p += np.cos(h*t)[:,None]*a + np.sin(h*t)[:,None]*b
    return np.ascontiguousarray(p)

def parse_vect(path: Path) -> np.ndarray:
    """Parse a one-component Geomview VECT centerline.

    A negative component vertex count means closed. E012 accepts a one-component
    trefoil only; multi-component VECT files are rejected rather than silently
    choosing a component.
    """
    text=path.read_text(encoding='utf-8',errors='replace')
    lines=[]
    for ln in text.splitlines():
        ln=ln.split('#',1)[0].strip()
        if ln: lines.append(ln)
    toks=' '.join(lines).split()
    if not toks or toks[0].upper()!='VECT':
        raise ValueError(f'Not a VECT file: {path}')
    pos=1
    if len(toks)<4: raise ValueError('Truncated VECT header')
    npoly,nvert,ncolor=map(int,toks[pos:pos+3]); pos+=3
    counts=[int(x) for x in toks[pos:pos+npoly]]; pos+=npoly
    _color_counts=[int(x) for x in toks[pos:pos+npoly]]; pos+=npoly
    if npoly!=1:
        raise ValueError(f'E012-v0.2.0 trefoil provider must be one component, got {npoly}')
    nv=abs(counts[0])
    if nv!=nvert:
        raise ValueError(f'VECT vertex-count mismatch: component={nv}, total={nvert}')
    need=3*nvert
    if len(toks)<pos+need: raise ValueError('Truncated VECT coordinates')
    xyz=np.asarray([float(x) for x in toks[pos:pos+need]],dtype=float).reshape(nvert,3)
    if len(xyz)>1 and np.linalg.norm(xyz[0]-xyz[-1]) < 1e-12:
        xyz=xyz[:-1]
    return np.ascontiguousarray(xyz)

def resample_closed(points: np.ndarray, n: int) -> np.ndarray:
    p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<3: raise ValueError('points must be (N,3)')
    seg=np.roll(p,-1,axis=0)-p; ds=np.linalg.norm(seg,axis=1)
    if np.any(ds<=0): raise ValueError('duplicate consecutive points')
    s=np.concatenate(([0.0],np.cumsum(ds))); L=float(s[-1])
    target=np.linspace(0,L,int(n),endpoint=False); ext=np.vstack((p,p[0]))
    idx=np.searchsorted(s,target,side='right')-1; idx=np.clip(idx,0,len(p)-1)
    u=(target-s[idx])/ds[idx]
    return np.ascontiguousarray((1-u)[:,None]*ext[idx]+u[:,None]*ext[idx+1])

def load_seedset(seedset_path: Path, topology_id='3_1'):
    obj=json.loads(seedset_path.read_text(encoding='utf-8'))
    summary=obj.get('summary',{})
    if not summary.get('static_ready',False): raise RuntimeError(f'E011 topology {topology_id} is not STATIC_READY')
    if summary.get('topology_id')!=topology_id: raise RuntimeError('E011 topology mismatch')
    return obj

def select_provider_anchors(seedset_path: Path, provider_groups=('gilbert','knotplot'), topology_id='3_1'):
    obj=load_seedset(seedset_path,topology_id)
    anchors=[]
    for provider in provider_groups:
        xs=[a for a in obj.get('provider_anchors',[]) if a.get('provider_group')==provider and a.get('static_ready',False)]
        if len(xs)!=1:
            raise RuntimeError(f'Expected exactly one STATIC_READY provider anchor for {provider}, got {len(xs)}')
        anchors.append(xs[0])
    return anchors,obj.get('summary',{})

def _canonicalize_orientation(points: np.ndarray, anchor: dict, canonical_writhe_sign: int) -> tuple[np.ndarray,bool]:
    wr=anchor.get('finest_metrics',{}).get('Wr')
    if not isinstance(wr,(int,float)) or wr==0: return points,False
    if (1 if wr>0 else -1) != (1 if canonical_writhe_sign>=0 else -1):
        return np.ascontiguousarray(points[::-1]),True
    return points,False

def resolve_provider(anchor: dict, workbench: Path, *, canonical_writhe_sign=1):
    loc=anchor.get('source_locator',{})
    source=rewrite_workbench_path(loc.get('source_path',''),workbench)
    if not source.exists(): raise FileNotFoundError(f'E011 source locator does not resolve locally: {source}')
    rep=loc.get('representation')
    model=None; raw_points=None
    if rep=='gilbert_ab_record':
        ref=loc.get('reference_id') or loc.get('variant_id')
        model=parse_gilbert_ab(source,ref)
        sampler=lambda n: sample_gilbert(model,n)
    elif rep=='vect':
        raw_points=parse_vect(source)
        sampler=lambda n: resample_closed(raw_points,n)
    else:
        raise RuntimeError(f'Unsupported E011 provider representation for v0.2.0: {rep!r}')

    rop=anchor.get('finest_metrics',{}).get('Rop')
    if not isinstance(rop,(int,float)) or rop<=0:
        raise RuntimeError(f'Provider {anchor.get("provider_group")} lacks positive E011 Rop for scale-normalization')

    def sample_normalized(n: int):
        p=np.ascontiguousarray(sampler(int(n)),dtype=float)
        p,reversed_orientation=_canonicalize_orientation(p,anchor,int(canonical_writhe_sign))
        Lraw=polygon_length(p)
        # E011 certified Rop = L/D_eff. Scale every provider to D_eff=1.
        D_raw=Lraw/float(rop)
        if D_raw<=0: raise RuntimeError('Non-positive provider scale')
        return np.ascontiguousarray(p/D_raw), {
            'raw_polygon_length':float(Lraw), 'D_eff_raw':float(D_raw),
            'normalized_polygon_length':float(Lraw/D_raw), 'D_normalized':1.0,
            'e011_ropelength':float(rop), 'orientation_reversed':bool(reversed_orientation),
        }

    return {
        'anchor':anchor,'source_path':source,'source_sha256':sha256_file(source),
        'representation':rep,'model':model,'raw_points':raw_points,'sample':sample_normalized,
    }

# Backward-compatible helpers retained for v0.1.x consumers/tests.
def select_anchor(seedset_path: Path, provider_preferences=('gilbert',), topology_id='3_1'):
    anchors,summary=select_provider_anchors(seedset_path,provider_preferences,topology_id)
    return anchors[0],summary

def load_gilbert_anchor(seedset_path: Path, workbench: Path, provider_preferences=('gilbert',), expected_reference_id='3:1:1'):
    anchor,summary=select_anchor(seedset_path,provider_preferences,topology_id='3_1')
    r=resolve_provider(anchor,workbench,canonical_writhe_sign=-1 if anchor.get('finest_metrics',{}).get('Wr',1)<0 else 1)
    if r['representation']!='gilbert_ab_record': raise RuntimeError('Expected Gilbert AB provider')
    if r['model'].knot_id!=expected_reference_id: raise RuntimeError(f'Unexpected Gilbert reference: {r["model"].knot_id}')
    return {'anchor':anchor,'summary':summary,'source_path':r['source_path'],'source_sha256':r['source_sha256'],'model':r['model']}

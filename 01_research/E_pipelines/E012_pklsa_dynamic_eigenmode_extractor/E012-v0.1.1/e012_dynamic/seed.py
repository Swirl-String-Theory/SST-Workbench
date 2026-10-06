from __future__ import annotations
import gzip, json, re
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from .paths import rewrite_workbench_path
from .util import sha256_file

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
    vals=[float(v.strip()) for v in text.split(",")]
    if len(vals)!=3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return vals

def read_text_maybe_gzip(path: Path) -> str:
    if path.suffix.lower()==".gz":
        with gzip.open(path,"rt",encoding="utf-8",errors="replace") as f:
            return f.read()
    return path.read_text(encoding="utf-8",errors="replace")

def parse_gilbert_ab(path: Path, knot_id: str) -> GilbertAB:
    text=read_text_maybe_gzip(path)
    selected=None
    for m in _AB_RE.finditer(text):
        if m.group("id")==knot_id:
            selected=m; break
    if selected is None:
        raise KeyError(f"Gilbert AB record {knot_id!r} not found in {path}")
    hs=[]; aa=[]; bb=[]
    for c in _COEFF_RE.finditer(selected.group("body")):
        hs.append(int(c.group(1))); aa.append(_vec(c.group(2))); bb.append(_vec(c.group(3)))
    if not hs:
        raise ValueError(f"No coefficients in AB record {knot_id!r}")
    return GilbertAB(
        knot_id=knot_id,
        conway=selected.group("conway"),
        L=float(selected.group("L")),
        D=float(selected.group("D")),
        harmonics=np.asarray(hs,dtype=int),
        A=np.asarray(aa,dtype=float),
        B=np.asarray(bb,dtype=float),
    )

def sample_gilbert(model: GilbertAB, n: int) -> np.ndarray:
    if n < 16:
        raise ValueError("n must be >=16")
    t=np.linspace(0,2*np.pi,int(n),endpoint=False)
    p=np.zeros((len(t),3),dtype=float)
    for h,a,b in zip(model.harmonics,model.A,model.B):
        p += np.cos(h*t)[:,None]*a + np.sin(h*t)[:,None]*b
    return np.ascontiguousarray(p)

def select_anchor(seedset_path: Path, provider_preferences=("gilbert",), topology_id="3_1"):
    obj=json.loads(seedset_path.read_text(encoding="utf-8"))
    summary=obj.get("summary",{})
    if not summary.get("static_ready",False):
        raise RuntimeError(f"E011 topology {topology_id} is not STATIC_READY")
    if summary.get("topology_id") != topology_id:
        raise RuntimeError(f"E011 seedset topology mismatch: {summary.get('topology_id')}")
    anchors=obj.get("provider_anchors",[])
    for provider in provider_preferences:
        for a in anchors:
            if a.get("provider_group")==provider and a.get("static_ready",False):
                return a, summary
    raise RuntimeError(f"No STATIC_READY provider anchor found for preferences={provider_preferences}")

def load_gilbert_anchor(seedset_path: Path, workbench: Path, provider_preferences=("gilbert",),
                        expected_reference_id="3:1:1"):
    anchor,summary=select_anchor(seedset_path,provider_preferences,topology_id="3_1")
    loc=anchor.get("source_locator",{})
    if loc.get("representation")!="gilbert_ab_record":
        raise RuntimeError("E012-v0.1.0 supports the E011 Gilbert AB provider anchor only")
    ref=loc.get("reference_id") or expected_reference_id
    if ref != expected_reference_id:
        raise RuntimeError(f"Unexpected Gilbert reference: {ref}")
    source=rewrite_workbench_path(loc.get("source_path",""),workbench)
    if not source.exists():
        raise FileNotFoundError(f"E011 source locator does not resolve locally: {source}")
    model=parse_gilbert_ab(source,ref)
    return {
        "anchor":anchor,
        "summary":summary,
        "source_path":source,
        "source_sha256":sha256_file(source),
        "model":model,
    }

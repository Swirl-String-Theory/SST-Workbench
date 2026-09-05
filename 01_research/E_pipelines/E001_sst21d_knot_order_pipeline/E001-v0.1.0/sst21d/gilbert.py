from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET
import numpy as np

@dataclass(frozen=True)
class FourierComponent:
    indices: np.ndarray
    A: np.ndarray
    B: np.ndarray

@dataclass(frozen=True)
class GilbertEntry:
    catalog_id: str
    conway: str
    source_L: float | None
    source_D: float | None
    components: tuple[FourierComponent,...]
    entry_sha256: str
    raw_attributes: dict[str,str]

    @property
    def component_count(self)->int: return len(self.components)
    @property
    def coefficient_count(self)->int: return int(sum(len(c.indices) for c in self.components))
    @property
    def topology_key(self)->str:
        p=self.catalog_id.split(':')
        if len(p)>=3:
            crossing, comps, ordinal=p[0],p[1],p[2]
            return f"{crossing}_{ordinal}" if comps=='1' else f"{crossing}^{comps}_{ordinal}"
        return self.catalog_id.replace(':','_')
    @property
    def knotplot_key(self)->str: return self.catalog_id.replace(':','.')

def _vec(text: str | None)->np.ndarray:
    if text is None: return np.zeros(3)
    vals=[float(v.strip()) for v in text.split(',')]
    if len(vals)!=3: raise ValueError(f'expected 3-vector, got {text!r}')
    return np.asarray(vals,dtype=float)

def _component_from_parent(parent: ET.Element)->FourierComponent:
    rows=[]
    for c in parent.findall('Coeff'):
        rows.append((int(c.attrib.get('I','0').strip()),_vec(c.attrib.get('A')),_vec(c.attrib.get('B'))))
    if not rows: raise ValueError('component contains no Coeff rows')
    rows.sort(key=lambda x:x[0])
    return FourierComponent(np.asarray([r[0] for r in rows],dtype=int),np.vstack([r[1] for r in rows]),np.vstack([r[2] for r in rows]))

def parse_gilbert(path: str | Path)->list[GilbertEntry]:
    path=Path(path)
    root=ET.parse(path).getroot()
    out=[]
    for ab in root.findall('AB'):
        comps=ab.findall('Component')
        series=tuple(_component_from_parent(c) for c in comps) if comps else (_component_from_parent(ab),)
        raw=ET.tostring(ab,encoding='utf-8')
        def f(name):
            v=ab.attrib.get(name)
            return float(v.strip()) if v is not None and v.strip() else None
        out.append(GilbertEntry(
            catalog_id=ab.attrib.get('Id','UNKNOWN').strip(),
            conway=ab.attrib.get('Conway','').strip(),
            source_L=f('L'),source_D=f('D'),components=series,
            entry_sha256=hashlib.sha256(raw).hexdigest(),raw_attributes=dict(ab.attrib)))
    if not out: raise ValueError(f'{path}: no AB entries found')
    return out

def evaluate_component(c: FourierComponent,samples: int)->np.ndarray:
    t=np.linspace(0.0,2.0*np.pi,samples,endpoint=False)
    phase=np.outer(t,c.indices)
    return np.cos(phase)@c.A + np.sin(phase)@c.B

def uniform_resample_closed(points: np.ndarray,n: int)->np.ndarray:
    p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<3: raise ValueError('points must be (N,3), N>=3')
    q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1)
    s=np.concatenate([[0.0],np.cumsum(ds)])
    if s[-1]<=0: raise ValueError('zero-length curve')
    target=np.linspace(0.0,s[-1],n,endpoint=False)
    out=np.column_stack([np.interp(target,s,q[:,k]) for k in range(3)])
    return out

def sample_entry(entry: GilbertEntry,samples: int,oversample: int=4)->list[np.ndarray]:
    dense=max(samples*oversample,samples+8)
    return [uniform_resample_closed(evaluate_component(c,dense),samples) for c in entry.components]

from __future__ import annotations
from pathlib import Path
import re, numpy as np

EXTS={'.txt','.xyz','.csv','.dat','.vect'}
SIDE_SUFFIXES=('.phase.npy','.field.npz','.timeseries.npz','.probe_pair.npz','.repr.npz','.model.json')

def discover(root: Path):
    out=[]
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in EXTS and not any(p.name.endswith(s) for s in SIDE_SUFFIXES):
            out.append(p)
    return sorted(out)

def _floats(line):
    vals=[]
    for tok in re.split(r'[\s,;]+', line.strip()):
        try: vals.append(float(tok))
        except: pass
    return vals

def load_curve(path: Path):
    if path.suffix.lower()=='.vect':
        return load_vect(path)
    pts=[]
    for line in path.read_text(errors='ignore').splitlines():
        s=line.strip()
        if not s or s.startswith(('#','%','//')): continue
        v=_floats(s)
        if len(v)>=3: pts.append(v[:3])
    a=np.asarray(pts,dtype=float)
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<4:
        raise ValueError(f'No usable XYZ curve in {path}')
    return [a]

def load_vect(path: Path):
    lines=[ln.strip() for ln in path.read_text(errors='ignore').splitlines() if ln.strip() and not ln.lstrip().startswith('#')]
    if not lines: raise ValueError('empty VECT')
    # Minimal Geomview VECT reader. Fall back to generic numeric rows if header does not match.
    if lines[0].upper().startswith('VECT') and len(lines)>=3:
        hdr=[int(round(x)) for x in _floats(lines[1])[:3]]
        if len(hdr)>=3:
            npoly,nvert,_=hdr
            counts=[int(round(x)) for x in _floats(lines[2])]
            if len(counts)>=npoly:
                # colors count line follows; coordinates begin after it.
                idx=4
                coords=[]
                while idx<len(lines) and len(coords)<nvert:
                    v=_floats(lines[idx]); idx+=1
                    if len(v)>=3: coords.append(v[:3])
                coords=np.asarray(coords,float)
                comps=[]; off=0
                for c in counts[:npoly]:
                    n=abs(c); comp=coords[off:off+n]; off+=n
                    if len(comp)>=4: comps.append(comp)
                if comps: return comps
    pts=[]
    for ln in lines:
        v=_floats(ln)
        if len(v)>=3: pts.append(v[:3])
    a=np.asarray(pts,float)
    if len(a)<4: raise ValueError('No usable VECT coordinates')
    return [a]

def sidecars(path: Path):
    base=path.with_suffix('')
    d={}
    mapping={
        'phase':Path(str(base)+'.phase.npy'),
        'field':Path(str(base)+'.field.npz'),
        'timeseries':Path(str(base)+'.timeseries.npz'),
        'probe_pair':Path(str(base)+'.probe_pair.npz'),
        'repr':Path(str(base)+'.repr.npz'),
        'model':Path(str(base)+'.model.json'),
    }
    for k,p in mapping.items():
        if p.exists(): d[k]=p
    return d

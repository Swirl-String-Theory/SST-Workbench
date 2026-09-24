from __future__ import annotations
from pathlib import Path
import re, json, gzip, numpy as np
from .fseries import sample_fremlin_fseries

def _split_xyz_components(text):
    comps=[]; cur=[]
    for raw in text.splitlines():
        s=raw.strip()
        if not s:
            if cur: comps.append(np.asarray(cur,float)); cur=[]
            continue
        if s.lower().startswith(('component','curve','vect')) or s.startswith(('#','%','//')):
            if s.lower().startswith(('component','curve')) and cur:
                comps.append(np.asarray(cur,float)); cur=[]
            continue
        vals=s.replace(',',' ').split()
        if len(vals)>=3:
            try: xyz=[float(vals[0]),float(vals[1]),float(vals[2])]
            except ValueError: continue
            cur.append(xyz)
    if cur: comps.append(np.asarray(cur,float))
    comps=[c for c in comps if len(c)>=3 and np.isfinite(c).all()]
    if not comps: raise ValueError('no XYZ components found')
    return comps

def load_xyz(path):
    return _split_xyz_components(Path(path).read_text(encoding='utf-8',errors='replace'))

def load_vect(path):
    # Geomview VECT: comments are allowed; parser is intentionally strict about counts.
    lines=[]
    for raw in Path(path).read_text(encoding='utf-8',errors='replace').splitlines():
        s=raw.split('#',1)[0].strip()
        if s: lines.append(s)
    toks=' '.join(lines).split()
    if not toks or toks[0] not in ('VECT','4VECT'): raise ValueError('not VECT')
    i=1; ncomp=int(toks[i]); nvert=int(toks[i+1]); _ncolor=int(toks[i+2]); i+=3
    counts=[int(toks[i+j]) for j in range(ncomp)]; i+=ncomp
    i+=ncomp # color counts
    if sum(abs(x) for x in counts)!=nvert: raise ValueError('VECT vertex count mismatch')
    comps=[]
    for count in counts:
        m=abs(count); pts=[]
        for _ in range(m):
            pts.append([float(toks[i]),float(toks[i+1]),float(toks[i+2])]); i+=3
        a=np.asarray(pts,float)
        if count<0 and len(a)>1 and np.linalg.norm(a[0]-a[-1])<1e-14: a=a[:-1]
        comps.append(a)
    return comps

def _try_sst_knotlib(path):
    try:
        import sst_knotlib as sk
    except Exception:
        return None
    try:
        asset=sk.load_geometry(str(path))
        pts=getattr(asset,'points',None)
        if pts is None: return None
        if isinstance(pts,np.ndarray) and pts.ndim==2: return [np.asarray(pts,float)]
        return [np.asarray(x,float) for x in pts]
    except Exception:
        return None

def load_npz(path):
    p=Path(path)
    with np.load(p,allow_pickle=False) as z:
        comps=[]
        for key in sorted(z.files):
            a=np.asarray(z[key])
            if a.ndim==2 and a.shape[1]>=3 and len(a)>=3:
                a=np.asarray(a[:,:3],float)
                if np.isfinite(a).all(): comps.append(a)
        if comps: return comps
    raise ValueError('no Nx3 arrays in NPZ')


def load_geometry(path, representation=None, fseries_n=4096):
    p=Path(path)
    rep=(representation or p.suffix.lower().lstrip('.')).lower()
    if rep in ('fremlin_fseries','fseries') or p.suffix.lower()=='.fseries':
        return [sample_fremlin_fseries(p,n=fseries_n)]
    if p.suffix.lower()=='.vect': return load_vect(p)
    if p.suffix.lower()=='.npz': return load_npz(p)
    if p.suffix.lower()=='.npy':
        a=np.asarray(np.load(p,allow_pickle=False),float)
        if a.ndim==2 and a.shape[1]>=3: return [a[:,:3]]
        raise ValueError('NPY is not Nx3')
    if rep in ('qhp','knotplot_binary') or p.suffix.lower() in ('.qhp','.locd','.locf','.kp','.knot'):
        alt=_try_sst_knotlib(p)
        if alt is not None: return alt
        # Some QHP campaign exports are plain XYZ despite the extension/name.
        try: return load_xyz(p)
        except Exception: pass
        raise RuntimeError(f'{rep or p.suffix} geometry requires sst_knotlib or an XYZ-compatible export')
    if p.suffix.lower() in ('.xyz','.csv','.txt','.short','.dat') or rep in ('xyz','xyz_text','xyz_short','auto'):
        try: return load_xyz(p)
        except Exception:
            alt=_try_sst_knotlib(p)
            if alt is not None: return alt
            raise
    if p.suffix.lower()=='.gz':
        alt=_try_sst_knotlib(p)
        if alt is not None: return alt
        raise RuntimeError('gzip geometry requires sst_knotlib adapter; no silent format guess')
    alt=_try_sst_knotlib(p)
    if alt is not None: return alt
    raise ValueError(f'unsupported geometry format: {p}')

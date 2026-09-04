from __future__ import annotations
from pathlib import Path
import re
import numpy as np

EXTS={'.txt','.xyz','.csv','.dat','.vect'}
SIDE_SUFFIXES=('.phase.npy','.field.npz','.timeseries.npz','.probe_pair.npz','.repr.npz','.model.json')

# Conservative generic-text component recovery.  Explicit blank/component separators
# are preferred.  Jump segmentation is only accepted when every recovered segment
# is itself a well-closed curve, which prevents one bad edge in a single knot from
# being silently reinterpreted as a link.
TEXT_COMPONENT_JUMP_FACTOR = 5.0
TEXT_COMPONENT_MIN_POINTS = 16
TEXT_COMPONENT_CLOSURE_MAX = 0.05
_COMPONENT_MARKER = re.compile(r'^\s*(?:component|curve|strand|polyline|loop)\b', re.I)


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
        except Exception: pass
    return vals


def _closure_gap_ratio_local(p):
    p=np.asarray(p,float)
    if len(p)<2: return float('inf')
    seg=np.linalg.norm(np.diff(p,axis=0),axis=1)
    L=float(seg.sum())
    return float(np.linalg.norm(p[0]-p[-1])/max(L,1e-300))


def split_components_by_jumps(points, jump_factor=TEXT_COMPONENT_JUMP_FACTOR,
                               min_points=TEXT_COMPONENT_MIN_POINTS,
                               closure_max=TEXT_COMPONENT_CLOSURE_MAX):
    """Conservative fallback for concatenated closed link components.

    A split is accepted only when (i) one or more inter-row jumps exceed a robust
    multiple of the median step, (ii) every resulting segment has enough samples,
    and (iii) every segment is independently closed to ``closure_max``.  Otherwise
    the input remains a single component and G00 is allowed to reject it normally.
    """
    a=np.asarray(points,float)
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<2*min_points:
        return [a], {'method':'single','jump_indices':[],'jump_factor':jump_factor}
    d=np.linalg.norm(np.diff(a,axis=0),axis=1)
    positive=d[np.isfinite(d) & (d>1e-15)]
    if len(positive)<2:
        return [a], {'method':'single','jump_indices':[],'jump_factor':jump_factor}
    typical=float(np.median(positive))
    if not np.isfinite(typical) or typical<=0:
        return [a], {'method':'single','jump_indices':[],'jump_factor':jump_factor}
    cut_after=np.flatnonzero(d > jump_factor*typical)
    if len(cut_after)==0:
        return [a], {'method':'single','jump_indices':[],'jump_factor':jump_factor,'median_step':typical}
    cuts=(cut_after+1).tolist()
    bounds=[0,*cuts,len(a)]
    comps=[a[bounds[i]:bounds[i+1]] for i in range(len(bounds)-1)]
    if any(len(c)<min_points for c in comps):
        return [a], {'method':'single','jump_indices':cuts,'jump_factor':jump_factor,'median_step':typical,
                     'fallback_rejected':'short_component'}
    gaps=[_closure_gap_ratio_local(c) for c in comps]
    if max(gaps)>closure_max:
        return [a], {'method':'single','jump_indices':cuts,'jump_factor':jump_factor,'median_step':typical,
                     'fallback_rejected':'components_not_closed','candidate_closure_gap_ratios':gaps}
    return comps, {'method':'jump_fallback_validated','jump_indices':cuts,'jump_factor':jump_factor,
                   'median_step':typical,'component_closure_gap_ratios':gaps}


def _validate_explicit_groups(groups):
    comps=[np.asarray(g,float) for g in groups if len(g)>=4]
    if len(comps)<2:
        return None
    if any(c.ndim!=2 or c.shape[1]!=3 or len(c)<4 for c in comps):
        return None
    gaps=[_closure_gap_ratio_local(c) for c in comps]
    if max(gaps)>TEXT_COMPONENT_CLOSURE_MAX:
        return None
    return comps, gaps


def load_curve(path: Path, return_info=False):
    if path.suffix.lower()=='.vect':
        comps,info=load_vect(path,return_info=True)
        return (comps,info) if return_info else comps

    groups=[]; current=[]; numeric_all=[]; saw_separator=False
    def flush():
        nonlocal current
        if current:
            groups.append(current); current=[]

    for line in path.read_text(errors='ignore').splitlines():
        s=line.strip()
        if not s:
            if current: saw_separator=True
            flush(); continue
        if s.startswith(('#','%','//')):
            marker=s.lstrip('#%/ ').strip()
            if _COMPONENT_MARKER.match(marker):
                if current: saw_separator=True
                flush()
            continue
        if _COMPONENT_MARKER.match(s):
            if current: saw_separator=True
            flush(); continue
        v=_floats(s)
        if len(v)>=3:
            xyz=v[:3]; current.append(xyz); numeric_all.append(xyz)
    flush()
    a=np.asarray(numeric_all,dtype=float)
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<4:
        raise ValueError(f'No usable XYZ curve in {path}')

    if saw_separator:
        valid=_validate_explicit_groups(groups)
        if valid is not None:
            comps,gaps=valid
            info={'format':'text','method':'explicit_separators','n_components':len(comps),
                  'component_lengths':[len(c) for c in comps],
                  'component_closure_gap_ratios':gaps}
            return (comps,info) if return_info else comps

    comps,jinfo=split_components_by_jumps(a)
    info={'format':'text',**jinfo,'n_components':len(comps),'component_lengths':[len(c) for c in comps]}
    return (comps,info) if return_info else comps


def load_vect(path: Path, return_info=False):
    lines=[ln.strip() for ln in path.read_text(errors='ignore').splitlines() if ln.strip() and not ln.lstrip().startswith('#')]
    if not lines: raise ValueError('empty VECT')
    # Minimal Geomview VECT reader. Fall back to generic numeric rows if header does not match.
    if lines[0].upper().startswith('VECT') and len(lines)>=3:
        hdr=[int(round(x)) for x in _floats(lines[1])[:3]]
        if len(hdr)>=3:
            npoly,nvert,_=hdr
            counts=[int(round(x)) for x in _floats(lines[2])]
            if len(counts)>=npoly:
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
                if comps:
                    info={'format':'vect','method':'vect_header','n_components':len(comps),
                          'component_lengths':[len(c) for c in comps]}
                    return (comps,info) if return_info else comps
    pts=[]
    for ln in lines:
        v=_floats(ln)
        if len(v)>=3: pts.append(v[:3])
    a=np.asarray(pts,float)
    if len(a)<4: raise ValueError('No usable VECT coordinates')
    comps,jinfo=split_components_by_jumps(a)
    info={'format':'vect','method':'vect_numeric_'+jinfo['method'],'n_components':len(comps),
          'component_lengths':[len(c) for c in comps],**{k:v for k,v in jinfo.items() if k!='method'}}
    return (comps,info) if return_info else comps


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

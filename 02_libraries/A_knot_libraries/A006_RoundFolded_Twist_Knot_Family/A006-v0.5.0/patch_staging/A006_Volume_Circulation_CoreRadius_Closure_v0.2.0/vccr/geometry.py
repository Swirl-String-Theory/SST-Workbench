"""Geometry-only measurements. No certified thickness or knot-identity inference."""
from __future__ import annotations
import hashlib
import math
from pathlib import Path
import numpy as np


def read_xyz(path: str|Path) -> list[np.ndarray]:
    p=Path(path)
    b=p.read_bytes()
    if b.startswith(b'KnotPlot 1.0') or b'\x00' in b[:128]:
        raise ValueError(f'{p}: binary KnotPlot coords detected. Convert to ASCII XYZ first; do not relabel binary as text.')
    text=b.decode('utf-8-sig')
    parts=[]; current=[]
    def commit():
        nonlocal current
        if current:
            a=np.asarray(current,dtype=np.float64)
            if a.shape[0] < 4: raise ValueError('each closed component needs at least 4 points')
            if not np.isfinite(a).all(): raise ValueError('non-finite coordinates')
            parts.append(a)
            current=[]
    for lineno,line in enumerate(text.splitlines(),1):
        s=line.strip()
        if not s:
            commit();continue
        if s.startswith('#') or s.startswith('Component ') and s.endswith(':'):
            # KnotPlot coords output may contain explicit header lines.
            if s.startswith('Component '): commit()
            continue
        row=s.split()
        if len(row)!=3: raise ValueError(f'{p}:{lineno}: expected exactly x y z, got {s[:100]!r}')
        try: current.append([float(x) for x in row])
        except ValueError as e: raise ValueError(f'{p}:{lineno}: nonnumeric point') from e
    commit()
    if not parts: raise ValueError(f'{p}: no components')
    return parts


def sha256_file(path:str|Path)->str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def per_component(a:np.ndarray)->dict:
    # Input is polygon with implicit closure. If explicit duplicate endpoint, reject rather than count zero edge.
    edges=np.roll(a,-1,axis=0)-a
    ds=np.linalg.norm(edges,axis=1)
    if np.any(ds<=1e-13): raise ValueError('zero/near-zero adjacent edge: duplicate endpoint or collapsed bead')
    tangent=edges/ds[:,None]
    dots=np.sum(tangent*np.roll(tangent,1,axis=0),axis=1)
    turn=np.degrees(np.arccos(np.clip(dots,-1,1)))
    circumference=float(np.sum(ds))
    return dict(n_beads=len(a), length_coordinate=circumference,
                edge_min_coordinate=float(ds.min()), edge_max_coordinate=float(ds.max()),
                edge_ratio=float(ds.max()/ds.min()),
                turning_angle_max_deg=float(turn.max()),
                turning_angle_p99_deg=float(np.percentile(turn,99)),
                centroid_coordinate=[float(v) for v in a.mean(axis=0)])


def measurements(path:str|Path)->dict:
    comps=read_xyz(path)
    out=[per_component(a) for a in comps]
    return dict(path=str(path),sha256=sha256_file(path),
                n_components=len(comps), total_beads=sum(len(a) for a in comps),
                total_length_coordinate=sum(d['length_coordinate'] for d in out),components=out,
                source_units='UNKNOWN coordinate units; no automatic conversion to SI')


def material_pair(initial:str|Path, final:str|Path, radius_ref_m:float,
                  gamma_ref_m2_s:float, meters_per_coordinate_unit:float,
                  density_kg_m3:float=7.0e-7)->dict:
    """Local segment volume conservation ONLY when vertex indices trace the same material segments.
    Input coords may not be resampled, reindexed or permuted between states.
    """
    ia=read_xyz(initial); ib=read_xyz(final)
    if len(ia)!=len(ib): raise ValueError('different component count: material correspondence not proven')
    a0=radius_ref_m;b0=gamma_ref_m2_s;scale=meters_per_coordinate_unit
    from .core import finite_positive
    for name,val in [('radius_ref_m',a0),('gamma_ref_m2_s',b0),('meters_per_coordinate_unit',scale)]:finite_positive(val,name)
    out=[]
    for n,(p,q) in enumerate(zip(ia,ib)):
        if len(p)!=len(q): raise ValueError(f'component {n} changed vertex count; no material correspondence')
        l0=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)*scale
        l1=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)*scale
        if min(l0.min(),l1.min())<=0: raise ValueError('degenerate material segment')
        ratio=l1/l0
        a1=a0/np.sqrt(ratio)
        omega0=b0/(math.pi*a0*a0)
        omega1=omega0*ratio
        v0=math.pi*a0*a0*l0
        v1=math.pi*a1*a1*l1
        out.append(dict(component=n,n_segments=len(p),
                        initial_length_m=float(l0.sum()),final_length_m=float(l1.sum()),
                        length_ratio=float(l1.sum()/l0.sum()),
                        segment_stretch_min=float(ratio.min()),segment_stretch_max=float(ratio.max()),
                        radius_min_m=float(a1.min()),radius_max_m=float(a1.max()),
                        mean_vorticity_min_s1=float(omega1.min()),mean_vorticity_max_s1=float(omega1.max()),
                        material_volume_initial_m3=float(v0.sum()),material_volume_final_m3=float(v1.sum()),
                        volume_relative_residual=float(abs(v1.sum()-v0.sum())/v0.sum()),
                        max_segment_volume_relative_residual=float(np.max(np.abs(v1/v0-1))),
                        constant_gamma_m2_s=b0))
    return dict(initial=str(initial), final=str(final),
                material_correspondence='ASSERTED_BY_OPERATOR_NOT_VERIFIED',
                gates={'material_volume_bookkeeping':'PASS' if max(d['max_segment_volume_relative_residual'] for d in out)<1e-12 else 'FAIL',
                       'euler_derivation_from_xyz':'NOT_RUN',
                       'physical_core_measurement':'UNRESOLVED'}, components=out)

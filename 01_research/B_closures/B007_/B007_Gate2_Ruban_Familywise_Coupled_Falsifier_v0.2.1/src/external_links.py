"""Imported custom 3-component candidates (NOT certified Borromean isotopy).
Preserves original bytes and checks hashes before generation. Higher resolution is
polygonal arclength interpolation, *not* increased source information.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from .filaments import resample
from .geometry import ROOT
from .vendor.build_ruban_family_v036 import pushforward_affine_shear

REGISTRY=ROOT/'configs'/'external_borromean_registry.json'
DATADIR=ROOT/'data'/'external_borromean'

def get_registry():return json.loads(REGISTRY.read_text(encoding='utf-8'))['families']

def read_xyz(p):
    blocks=[];cur=[]
    for idx,line in enumerate(Path(p).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():
            if cur:blocks.append(np.asarray(cur,dtype=float));cur=[]
            continue
        vals=line.split()
        if len(vals)!=3:raise ValueError(f'{p}: line {idx}: expected exactly 3 coordinates')
        cur.append([float(v) for v in vals])
    if cur:blocks.append(np.asarray(cur,dtype=float))
    if len(blocks)!=3 or any(len(x)<8 or not np.isfinite(x).all() for x in blocks):
        raise ValueError(f'{p}: expected 3 nondegenerate finite curve components')
    return blocks

def verify_source(name):
    entry=get_registry()[name]
    for key in ('original','reference'):
        fname=entry.get(key)
        if fname:
            actual=hashlib.sha256((DATADIR/fname).read_bytes()).hexdigest()
            if actual!=entry[key+'_sha256']:raise RuntimeError(f'IMPORTED SOURCE HASH MISMATCH: {fname}')
    return entry

def normalized_parts(name,source_key='original'):
    entry=verify_source(name)
    parts=read_xyz(DATADIR/entry[source_key]);allpoints=np.concatenate(parts)
    centre=allpoints.mean(axis=0)
    scale=float(np.max(np.linalg.norm(allpoints-centre,axis=1)))
    if not np.isfinite(scale) or scale<=0:raise ValueError('Zero or invalid geometric scale')
    return [(x-centre)/scale for x in parts],{'centre':centre.tolist(),'R0_scale_original_units':scale,'original_counts':[len(x) for x in parts]}

def generate_imported(name,n,perturbed=False,reference=False):
    if n<16:raise ValueError('Need >=16 points per component')
    entry=verify_source(name)
    if reference and not entry.get('reference'):
        raise ValueError(f'{name} has no N1024 source reference; use --external-source original')
    key='reference' if reference else 'original'
    parts,normalization=normalized_parts(name,key)
    # Interpolate original closed polygon, retain three distinct components.
    parts=[resample(x,n) for x in parts]
    if perturbed:
        # One common orientation-preserving volume-preserving diffeomorphism.
        parts=[pushforward_affine_shear(x,1.0,0.01,0.005,1) for x in parts]
    return parts,dict(source_variant=key,source_sha256=entry[key+'_sha256'],
        source_points=normalization['original_counts'],
        interpolation_only=(n>min(normalization['original_counts'])),
        normalized_R0_original_units=normalization['R0_scale_original_units'],
        topological_certification='UNRESOLVED',milnor_mu123='UNRESOLVED',
        component_knot_labels=entry['component_knots'])

def gauss_midpoint(parts,n=128):
    """Approximate pairwise linking. Not a Milnor invariant / topology certificate."""
    p=[resample(c,n) for c in parts]
    def pair(a,b):
        aa=np.roll(a,-1,axis=0)-a;bb=np.roll(b,-1,axis=0)-b
        ma=.5*(a+np.roll(a,-1,axis=0));mb=.5*(b+np.roll(b,-1,axis=0))
        r=ma[:,None,:]-mb[None,:,:]
        dist=np.linalg.norm(r,axis=-1)
        if np.min(dist)<1e-12:return float('nan')
        return float(np.sum(np.einsum('ijk,ijk->ij',np.cross(aa[:,None,:],bb[None,:,:]),r)/dist**3)/(4*np.pi))
    return [pair(p[0],p[1]),pair(p[0],p[2]),pair(p[1],p[2])]

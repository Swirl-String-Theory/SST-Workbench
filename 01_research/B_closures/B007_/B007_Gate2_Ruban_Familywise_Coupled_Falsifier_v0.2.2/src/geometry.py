"""Reproducible analytic E010 v0.3.6 torus knots / multiple-component links.

The curve generator is copied from the E010 v0.3.6 source package under
src/vendor (not an external download dependency). No dynamical stability inferred.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json, math
import numpy as np
from scipy.spatial import cKDTree
from .vendor.build_ruban_family_v036 import components, pushforward_affine_shear, xyz

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'configs'/'E010_ruban_family_v036.json'
GENER=ROOT/'src'/'vendor'/'build_ruban_family_v036.py'

def fingerprint(fp:Path)->str:return hashlib.sha256(Path(fp).read_bytes()).hexdigest()

def get_config():return json.loads(CONFIG.read_text(encoding='utf-8'))

def families(config):return {f'T_{r["p"]}_{r["q"]}':r for r in config['families']}

def family_parts(name:str,config=None):
    config=config or get_config()
    if name in families(config):
        f=families(config)[name];return int(f['p']),int(f['q']),f
    raise ValueError('Unknown family '+name+'; use --list-families')

def generate(p:int,q:int,b:float,n:int=1024,perturbed=False,cfg=None):
    cfg=cfg or get_config()
    parts=components(p,q,b,n,float(cfg['geometry_R0']),float(cfg.get('theta0',0)))
    if perturbed:
        pol=cfg['perturbation_policy'];parts=[pushforward_affine_shear(x,float(cfg['geometry_R0']),float(pol['epsilon_xy']),float(pol['epsilon_z_shear']),p) for x in parts]
    return parts

def total_length(parts):
    return float(sum(np.linalg.norm(np.roll(P,-1,axis=0)-P,axis=1).sum() for P in parts))

def metrics(parts):
    lengths=[];max_turn=0.;max_gap=0.;min_edge=float('inf')
    for p in parts:
        edge=np.roll(p,-1,axis=0)-p
        ee=np.linalg.norm(edge,axis=1)
        if not np.all(np.isfinite(p)) or ee.min()<1e-14:raise ValueError('Degenerate or nonfinite polygon')
        tang=edge/ee[:,None]
        angle=np.arccos(np.clip(np.sum(tang*np.roll(tang,-1,axis=0),axis=1),-1,1))
        lengths.append(float(ee.sum()))
        max_turn=max(max_turn,float(angle.max()));max_gap=max(max_gap,float(ee.max()));min_edge=min(min_edge,float(ee.min()))
    sep=None
    if len(parts)>1:
        sep=float(min(cKDTree(a).query(b)[0].min() for i,a in enumerate(parts) for b in parts[i+1:]))
    return {'length_total':sum(lengths),'length_components':lengths,'point_count_each':len(parts[0]),'component_count':len(parts),
     'min_polygon_edge':min_edge,'max_polygon_edge':max_gap,'max_polygon_turn':max_turn,'minimum_sampled_intercomponent_distance':sep,
     'continuous_reach_certified':False,'material_vortex_tube_qualified':False,
     'length_scale':'R0=1, dimensionless'}

def export(parts:list[np.ndarray],out:Path,seed_id:str,kind:str):
    dest=out/'promoted_seeds'/kind;dest.mkdir(parents=True,exist_ok=True)
    records=[]
    for j,part in enumerate(parts):
        name=seed_id+(f'_C{j:02d}' if len(parts)>1 else '')+('_pert' if kind=='perturbed' else '')+'.xyz'
        b=xyz(part);f=dest/name
        f.write_bytes(b)
        records.append({'path':str(f.relative_to(out)).replace('\\','/'),'sha256':hashlib.sha256(b).hexdigest(),
         'component_index':j,'points':len(part),'bytes':len(b)})
    return records

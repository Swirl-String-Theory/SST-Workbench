from __future__ import annotations
from pathlib import Path
import json,hashlib
import pandas as pd
from .io import scan_geometries,stage_input
from .geometry import cpp_info
from .analysis import analyze_knot
from .blind import new_salt,blind_id,write_private_manifest

def _sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def run_measure(input_path:Path,run_dir:Path,cfg:dict):
    run_dir.mkdir(parents=True,exist_ok=True); (run_dir/'shells').mkdir(exist_ok=True)
    inp=stage_input(input_path,run_dir); info=cpp_info(); require_cpp=bool(cfg['runtime'].get('require_cpp',True))
    if require_cpp and not info['loaded']: raise RuntimeError('C++ backend required by preset but not loaded.')
    salt=new_salt();mapping={};rows=[]; geoms=scan_geometries(inp)
    for p,pts in geoms:
        bid=blind_id(p,salt,'K');mapping[bid]={'name':p.stem,'path':str(p.resolve()),'sha256':_sha256(p)}
        row={'blind_id':bid,'status':'OK','n_input':len(pts)}
        try:
            a=analyze_knot(pts,cfg,require_cpp=require_cpp)
            for k,v in a.items():
                if k in ('normalized_points','shells','thickness'):continue
                row[k]=v
            row['thickness_raw']=a['thickness_raw'];row['thickness_limiter']=a['thickness']['limiter'];row['thickness_local_raw']=a['thickness']['local_curvature_radius_min'];row['thickness_nonlocal_raw']=a['thickness']['nonlocal_half_distance_min']
            pd.DataFrame(a['shells']).to_csv(run_dir/'shells'/f'{bid}_shells.csv',index=False)
        except Exception as e:
            row['status']='ERROR';row['error']=repr(e)
        rows.append(row)
    write_private_manifest(run_dir/'blind_manifest_private.json',salt,mapping)
    df=pd.DataFrame(rows) if rows else pd.DataFrame(columns=['blind_id','status']);df.to_csv(run_dir/'measurements_blind.csv',index=False)
    (run_dir/'runtime.json').write_text(json.dumps({'cpp':info,'input_dir':str(inp.resolve()),'n_geometries':len(geoms)},indent=2),encoding='utf-8')
    return {'n_geometries':len(rows),'cpp':info}

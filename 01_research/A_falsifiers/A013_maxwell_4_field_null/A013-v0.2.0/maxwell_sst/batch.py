from __future__ import annotations
import csv, json, time
from datetime import datetime
from pathlib import Path
import numpy as np
from . import __version__, WORKBENCH_PREFIX
from .constants import GAMMA0
from .geometry import discover_final_curves, load_curve_set, resample_closed, curve_length
from .audits import audit_t01_swirl_tonic,audit_t02_holonomy,audit_t03_moving_loop,audit_t04_exterior_hodge,audit_t05_energy_helicity,audit_t06_cyclic_work,audit_t07_radial_flux
from .reporting import clean
from native_ext import backend_info, set_num_threads

PRESETS={
  'basic': {'resolutions':[240], 'n_probe':192, 'n_samples':48, 'n_pert':3, 'n_sphere':48},
  'extended': {'resolutions':[300,600,1200], 'n_probe':512, 'n_samples':96, 'n_pert':8, 'n_sphere':128},
}

def _geometry_record(cs):
    m=cs.metrics; comps=cs.components
    return {
      'id':cs.id,'file':str(cs.path),'component_count':len(comps),'vertices':[len(c) for c in comps],
      'lengths':[curve_length(c) for c in comps], 'metrics_component_count':m.get('component_count'),
      'vertices_per_component':m.get('vertices_per_component'),'ropelength':m.get('ropelength',m.get('rop')),
      'thickness':m.get('thickness'),'residual':m.get('residual'),'residual_converged':m.get('residual_converged'),
      'edge_length_ratio':m.get('edge_length_ratio'),'edge_length_cv':m.get('edge_length_cv'),
    }

def run_batch(input_dir, out_dir=None, preset='basic', native_threads=16, ids=None):
    cfg=PRESETS[preset]; set_num_threads(native_threads); input_dir=Path(input_dir)
    ts=datetime.now().strftime('%Y%m%d_%H%M%S'); out=Path(out_dir or f"4_outputs_{preset}_{ts}"); out.mkdir(parents=True,exist_ok=True)
    files=discover_final_curves(input_dir); ids_set=set(x.strip() for x in ids.split(',')) if isinstance(ids,str) and ids.strip() else None
    if ids_set: files=[p for p in files if (p.stem[:-6] if p.stem.endswith('_final') else p.stem) in ids_set]
    synthetic=[audit_t01_swirl_tonic(),audit_t03_moving_loop(),audit_t06_cyclic_work()]
    (out/'synthetic.json').write_text(json.dumps(clean(synthetic),indent=2),encoding='utf-8')
    rows=[]; details=[]; start=time.perf_counter()
    for fi,p in enumerate(files,1):
        cs=load_curve_set(p); geom=_geometry_record(cs); record={'geometry':geom,'resolutions':[]}; print(f"[4_SST] {fi}/{len(files)} {cs.id}: {len(cs.components)} component(s)",flush=True)
        for n in cfg['resolutions']:
            comps=[resample_closed(c,n) for c in cs.components]
            t0=time.perf_counter(); tests=[
                audit_t02_holonomy(comps,[GAMMA0]*len(comps),n_probe=cfg['n_probe']),
                audit_t04_exterior_hodge(comps,n_samples=cfg['n_samples']),
                audit_t07_radial_flux(comps,n_sphere=cfg['n_sphere']),
            ]
            # T05 is expensive. Run on each basic resolution, and only on the middle resolution for extended.
            if preset=='basic' or n==cfg['resolutions'][len(cfg['resolutions'])//2]:
                tests.append(audit_t05_energy_helicity(comps,n_pert=cfg['n_pert']))
            dt=time.perf_counter()-t0; record['resolutions'].append({'n_per_component':n,'elapsed_s':dt,'tests':clean(tests)})
            status={t['id']:t['status'] for t in tests}; rows.append({'id':cs.id,'components':len(comps),'resolution':n,'elapsed_s':dt,**status})
        details.append(record); (out/f"{cs.id}.json").write_text(json.dumps(clean(record),indent=2),encoding='utf-8')
    elapsed=time.perf_counter()-start
    meta={'suite':'4_SST Maxwell-Inspiration Falsifier','version':__version__,'prefix':WORKBENCH_PREFIX,'preset':preset,'input_dir':str(input_dir.resolve()),'files':len(files),'native_threads_requested':native_threads,'backend':backend_info(),'elapsed_s':elapsed,'resolutions':cfg['resolutions']}
    summary={'meta':clean(meta),'synthetic':clean(synthetic),'geometries':[d['geometry'] for d in details],'rows':clean(rows)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (out/'summary.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['id','components','resolution','elapsed_s','T02','T04','T05','T07']; w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader();
        for r in rows: w.writerow(r)
    return out/'summary.json'

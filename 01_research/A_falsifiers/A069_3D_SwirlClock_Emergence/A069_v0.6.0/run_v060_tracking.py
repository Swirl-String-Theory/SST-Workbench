"""A069 v0.6.0 experimental preflight. NO official FREEZE / science-gate execution."""
from __future__ import annotations
import argparse,sys,json,hashlib
from pathlib import Path
import numpy as np
from a069_v060.plaquette_graph import component_diagnostics,compare_snapshots

p=argparse.ArgumentParser()
p.add_argument('--v05-instance',type=Path,help='A069 v0.5.0 instance root containing experiment/knotted_gp3d.py')
p.add_argument('--kind',choices=['A','B'],default='A')
p.add_argument('--mirror',action='store_true')
p.add_argument('--n',type=int,default=32)
p.add_argument('--steps',type=int,default=24)
p.add_argument('--dt',type=float,default=0.004)
p.add_argument('--segments',type=int,default=96)
p.add_argument('--box',type=float,default=10.)
p.add_argument('--xi',type=float,default=.42)
p.add_argument('--output',type=Path,default=Path('results/tracking_v060_preflight.json'))
a=p.parse_args()
if a.v05_instance is None:
    L=2*np.pi;coord=L*np.arange(a.n)/a.n
    x,y,z=np.meshgrid(coord,coord,coord,indexing='ij')
    psi=np.sin(x+.13)+1j*np.sin(y+.27)
    before=component_diagnostics(psi)
    final=psi
    model='SYNTHETIC_STRAIGHT_LINES_NOT_KNOT'
else:
    root=a.v05_instance.resolve()
    if not (root/'experiment'/'knotted_gp3d.py').is_file():p.error('missing v0.5.0 experiment/knotted_gp3d.py')
    sys.path.insert(0,str(root))
    from experiment.knotted_gp3d import initialize, step
    psi,info=initialize(kind=a.kind,mirror=a.mirror,n=a.n,box=a.box,xi=a.xi,segments=a.segments)
    before=component_diagnostics(psi)
    initial_psi=psi.copy()
    for t in range(a.steps):psi=step(psi,a.box,a.dt)
    final=psi
    model='NORMALIZED_COMPRESSIBLE_3D_GP_KNOT_PREFLIGHT'
comparison=compare_snapshots(psi if a.v05_instance is None else initial_psi, final)
# Never interpret a provisional graph as validated physical knot topology.
out={"schema":"A069-V060-PREFLIGHT-1","status":"DEVELOPMENT_UNCERTIFIED",
     "model":model,"kind":a.kind,"mirror":a.mirror,"n":a.n,"steps":a.steps,"dt":a.dt,
     "initial_graph":before,"final_graph":component_diagnostics(final),"comparison":comparison,
     "3d_knot_eigenfrequency":None,"swirl_clock_claim":"UNRESOLVED"}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({"status":out['status'],"model":model,
   "initial_components":before['component_count'],"final_components":out['final_graph']['component_count'],
   "initial_defects":before['junction_or_orientation_defects'],"final_defects":out['final_graph']['junction_or_orientation_defects'],
   "eigenfrequency":None,"output":str(a.output)},indent=2))

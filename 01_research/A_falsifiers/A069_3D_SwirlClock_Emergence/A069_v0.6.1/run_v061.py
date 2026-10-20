"""A069 v0.6.1 diagnostic runner: no FREEZE/BASIC and no physical reveal."""
from __future__ import annotations
import argparse,sys,json,hashlib,datetime
from pathlib import Path
import numpy as np
from a069_v061.geometry_gate import geometry_screen,readiness
from a069_v061.subgrid import subgrid_filaments,compare_filaments,spectral_grid_shift

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--v05-instance',type=Path,required=True)
p.add_argument('--kind',choices=['A','B'],default='B')
p.add_argument('--mirror',action='store_true')
p.add_argument('--n',type=int,default=32)
p.add_argument('--segments',type=int,default=96)
p.add_argument('--box',type=float,default=10.)
p.add_argument('--xi',type=float,default=.42)
p.add_argument('--dt',type=float,default=.006)
p.add_argument('--steps',type=int,default=8)
p.add_argument('--output',type=Path,default=Path('results/v061_preflight.json'))
a=p.parse_args()
vr=a.v05_instance.resolve()
if not (vr/'experiment'/'knotted_gp3d.py').is_file():p.error('v0.5.0 GP solver absent')
sys.path.insert(0,str(vr))
from experiment.knotted_gp3d import _seed,initialize,step,conserved
poly,full=_seed(a.kind,a.mirror,nb=max(32,a.segments))
scan=geometry_screen(full)
pre=readiness(scan,xi=a.xi,n=a.n,box=a.box)
psi,initinfo=initialize(kind=a.kind,mirror=a.mirror,n=a.n,box=a.box,xi=a.xi,segments=a.segments)
before=subgrid_filaments(psi,a.box)
subcell_offsets=[(.37,.29,.41),(-.23,.19,-.31)]
def shifts_for_state(state):
    output=[]
    for offs in subcell_offsets:
        s0=subgrid_filaments(spectral_grid_shift(state,a.box,offs),a.box)
        output.append({'shift_cells':list(offs),'components':s0['components_count'],
                       'defects':s0['ambiguous_lattice_junctions'],
                       'boundary_degenerate_faces':s0['boundary_degenerate_faces'],
                       'subgrid_qualified':s0['subgrid_reconstruction_qualified']})
    return output
initial_shifts=shifts_for_state(psi)
m0,e0=conserved(psi,a.box)
for i in range(a.steps):psi=step(psi,a.box,a.dt)
after=subgrid_filaments(psi,a.box)
m1,e1=conserved(psi,a.box)
shifted=shifts_for_state(psi)
# User-facing JSON contains diagnostics but not thousands of polyline points.
def strip(d):
    t={k:v for k,v in d.items() if k!='components'}
    t['components']=[{k:v for k,v in c.items() if k!='subgrid_polyline'} for c in d['components']]
    return t
result={
    'schema':'A069-V061-PREFLIGHT-1','status':'DEVELOPMENT_NOT_FROZEN_NOT_CERTIFIED',
    'framework':'v1.0.9 IS TARGET ONLY (not executed)',
    'source_model':'3D_COMPRESSIBLE_GP_NOT_EULER','kind':a.kind,'mirror':a.mirror,
    'parameters':{'n':a.n,'segments':a.segments,'box':a.box,'xi':a.xi,'dt':a.dt,'steps':a.steps,'total_time':a.dt*a.steps},
    'geometry':scan,'readiness':pre,'v05_initialization':initinfo,
    'initial':strip(before),'final':strip(after),
    'comparison':compare_filaments(before,after),
    'initial_subcell_grid_offsets':initial_shifts,'post_state_subcell_grid_offsets':shifted,
    'mass_relative_change':float((m1-m0)/m0),
    'energy_relative_change':float((e1-e0)/e0),
    'numerically_qualified_knot_trajectory':False,
    'knot_type_preserved':None,'physical_reconnection':None,
    'intrinsic_eigenmode_frequency':None,'swirl_clock_frequency':None,
    'gate_status':{'G32_CORE_GEOMETRY_READINESS':'PASS_DIAGNOSTIC' if pre['qualified'] else 'FAIL_PRECONDITION',
                  'G33_SUBGRID_LOCALIZATION':'PASS_DIAGNOSTIC' if before['subgrid_reconstruction_qualified'] and after['subgrid_reconstruction_qualified'] else 'UNRESOLVED',
                  'G34_TOPOLOGY_CONTINUITY':'UNRESOLVED','G35_CLOCK_EIGENMODE':'UNRESOLVED'},
    'claim_guard':'Neither 3D GP topological stability nor a physical clock is certified.'
}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'output':str(a.output),'status':result['status'],
                  'core_grid_qualified':pre['qualified'],
                  'before_components':before['components_count'],
                  'after_components':after['components_count'],
                  'initial_subgrid_qualified':before['subgrid_reconstruction_qualified'],
                  'final_subgrid_qualified':after['subgrid_reconstruction_qualified'],
                  'intrinsic_mode':None},indent=2))

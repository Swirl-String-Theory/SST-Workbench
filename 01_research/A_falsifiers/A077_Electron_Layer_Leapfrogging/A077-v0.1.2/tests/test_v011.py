"""Numerical regression tests are restricted to the reduced model and pilot.
No test grants spinorial or independent physical Euler qualifications.
"""
import json
from pathlib import Path
import numpy as np
from science.diagnostics import precise_events,detailed_run,clearance_trace,hermite_event,compare_refinements
from science.euler_field import GalerkinEuler

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'configs'/'pilot.json').read_text())

def ring_data():
 s=CFG['initial_conditions_dimensionless']['same']
 return np.column_stack((s['radii'],s['z'])).ravel(),s['gamma_signs'],np.array(s['radii'])*CFG['core_ratio']

def test_crossing_cubic_root_linear_exact():
 assert abs(hermite_event(0,1,0.2,-0.8,-1,-1)-.2)<1e-13

def test_full_length_crossings_finite():
 y,g,a=ring_data()
 s,m,c=detailed_run(y,g,a,tf=5,steps=200,ntheta=48)
 assert len(s['t'])==201
 assert m['event_count']==3
 assert all(0<=v['t']<=5 for v in m['events'])
 assert m['minimum_surface_clearance']>0
 assert m['collision_free_sampled']

def test_refinement_endpoint_and_event_counts():
 results=compare_refinements(CFG,'same')
 for scan in results:
  assert len(scan['levels'])==3
  assert len(set(len(v['events']) for v in scan['levels']))==1
  assert scan['levels'][-2]['relative_endpoint_delta_to_next']<0.001
  assert scan['levels'][-2]['max_event_shift_to_next']<0.001

def test_field_initial_independent_components_and_projection():
 e=GalerkinEuler(16,8.)
 geom=[{'R':1.0,'z':0.,'a':.3,'sign':1}]
 u0,_=e.initial(geom,azimuthal=0)
 u1,_=e.initial(geom,azimuthal=.4)
 assert np.linalg.norm(e.ifft(u1-u0))>1e-6
 assert e.diagnostics(u1)['divergence_Linf']<1e-10
 assert abs(e.diagnostics(u0)['helicity'])<1e-8

def test_euler_energy_short_pilot():
 e=GalerkinEuler(16,8.)
 u,meta=e.initial([{'R':1.,'z':0.,'a':.3}],azimuthal=.3)
 _,trace=e.evolve(u,.01,.005)
 assert len(trace)>=2
 assert abs(trace[-1]['energy']/trace[0]['energy']-1)<1e-4
 assert trace[-1]['divergence_Linf']<1e-10

def test_gate_dependencies_do_not_make_parity_depend_on_spin():
 plan=json.loads((ROOT/'gate_plan.json').read_text())
 req={p['gate_id']:p['requires'] for p in plan['gates']}
 assert req['G5']==['G2']
 assert req['G10']==['G2']
 assert 'G3' in req['G8'] and 'G4' in req['G8']


def test_euler_spinorial_gate_fail_closed(tmp_path):
    from science.euler_field import execute
    cfg={'n':16,'box_length':8.0,'t_final':0.005,'dt':0.005,
         'rings':[{'R':1.,'z':0.,'a':.3,'sign':1}],
         'meridional_amplitude':1.,'toroidal_amplitude':.2}
    result=execute(cfg,tmp_path)
    assert result['spinorial_separate_gate']['status']=='UNRESOLVED'
    assert result['spinorial_separate_gate']['physical_state_bundle']=='NOT_DEFINED'

def test_refinement_split_axes():
    spatial=compare_refinements(CFG,'same',axis_filter='angular')
    temporal=compare_refinements(CFG,'same',axis_filter='temporal')
    assert len(spatial)==1 and spatial[0]['axis']=='angular'
    assert len(temporal)==1 and temporal[0]['axis']=='temporal'

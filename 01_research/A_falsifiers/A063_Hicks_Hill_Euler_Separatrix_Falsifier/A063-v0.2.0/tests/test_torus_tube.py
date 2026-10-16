"""Scientific regression checks for A063-v0.2.0; do not certify Euler stability."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import pytest
from hicks_hill.analytic import SphereVortex,root_families
from torus_tube import (line,project_crossings,alexander_poly,expected_torus_alexander,
                        tube_geometry,sample_tube_flux,poincare_shear)

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='session')
def field():return SphereVortex(lam=root_families(1)['lambda1'][0])

@pytest.fixture(scope='session')
def curve(field):return line(field,samples=1601)

@pytest.fixture(scope='session')
def projections(curve):
 return [project_crossings(curve['xyz'],v) for v in [[.27,.71,.67],[.32,.13,.94],[1,.2,.1],[.1,1,.2]]]

def test_parent_protocol_hash_is_not_current_hash():
 proto=json.loads((ROOT/'configs/protocol.json').read_text())
 assert proto['parent_protocol_sha256']=='838a73226435889fe3cfee63053ee12d6a4a06d7cde67bb74a7ad02296038b99'
 assert proto['version']=='v0.2.0'

def test_closed_orbit(field,curve):
 assert abs(curve['W']-0.75)<2e-7
 assert curve['closure']<2e-7

def test_euler_field_vortex_line(field,curve):
 for s,z in zip(curve['s'][::250],curve['z'][::250]):
  x=field.numerical_residual(float(s),float(z),h=4e-5)
  assert x['beltrami_norm']<1e-5

def test_four_projections_nondegenerate(projections):
 assert len(projections)==4
 assert all(8<=len(c)<=18 for c in projections)
 assert all(min(x['z_gap'] for x in c)>1e-4 for c in projections)

def test_alexander_invariance(projections):
 expected=expected_torus_alexander()
 for cr in projections:
  k=alexander_poly(cr)
  assert k['coefficients_ascending']==expected
  assert k['degree']==6
  assert k['determinant']==3

def test_independent_trefoil_control():
 t=np.linspace(0,2*math.pi,1201)
 R=1+0.24*np.cos(3*t)
 xyz=np.column_stack([R*np.cos(2*t),R*np.sin(2*t),0.24*np.sin(3*t)])
 a=alexander_poly(project_crossings(xyz,[.71,.35,.24]))
 assert a['coefficients_ascending']==[1,-1,1]

def test_geometry_not_rigorous_reach(curve):
 a=tube_geometry(curve['xyz'])
 assert a['radius_curvature_min']>.1
 assert a['nonlocal_distance_proxy_min']>.1
 assert not a['certified_reach']

def test_clearance_inside_sphere(curve):
 assert max(np.linalg.norm(curve['xyz'],axis=1))<.99

def test_zero_radius_flux_is_null(field,curve):
 z=sample_tube_flux(field,curve['xyz'],radii=(0,),n_core=30,n_angles=8)[0]
 assert z['normal_flow_rms_over_urms']<1e-12

def test_finite_radius_normal_flux_is_nonzero(field,curve):
 data=sample_tube_flux(field,curve['xyz'],radii=(.002,.004,.008),n_core=90,n_angles=16)
 assert all(x['normal_flow_rms_over_urms']>1e-3 for x in data)
 assert data[0]['normal_flow_rms_over_urms']<data[1]['normal_flow_rms_over_urms']<data[2]['normal_flow_rms_over_urms']

def test_flux_sampling_convergence(field,curve):
 coarse=sample_tube_flux(field,curve['xyz'],radii=(.002,),n_core=90,n_angles=16)[0]
 fine=sample_tube_flux(field,curve['xyz'],radii=(.002,),n_core=180,n_angles=24)[0]
 assert abs(coarse['normal_flow_rms_over_urms']-fine['normal_flow_rms_over_urms'])<3e-4

def test_neighbor_pitch_shear(field,curve):
 s=poincare_shear(field,curve['s0_over_a'])
 assert s['dW_d_s_over_a']<-.1
 assert s['samples'][0]['four_cycle_phase_slip_rad']>0
 assert s['samples'][-1]['four_cycle_phase_slip_rad']<0

def test_registered_gates_do_not_overclaim():
 proto=json.loads((ROOT/'configs/protocol.json').read_text())
 assert proto['acceptance']['max_material_normal_flow_rms_over_urms']==.0001
 assert '3D' in proto['hypothesis_lanes']['dynamics']

def test_existing_run_ledger_checksums_if_present():
 out=ROOT/'A063_Hicks_Hill_Torus_Tube_Falsifier_v0.2.0-outputs'
 if not (out/'RUN_SUMMARY.json').exists():pytest.skip('run before test')
 summary=json.loads((out/'RUN_SUMMARY.json').read_text())
 assert hashlib.sha256((out/'GATE_LEDGER.json').read_bytes()).hexdigest()==summary['gate_ledger_sha256']
 statuses={x['gate_id']:x['status'] for x in json.loads((out/'GATE_LEDGER.json').read_text())['records']}
 assert statuses['T5']=='FAIL' and statuses['T6']=='FAIL'
 assert statuses['T8']=='UNRESOLVED' and statuses['T9']=='UNRESOLVED'
 assert statuses['T10']=='UNRESOLVED'

def test_theoretical_alexander():
 assert expected_torus_alexander()==[1,-1,0,1,0,-1,1]

import pytest
from hicks_hill.analytic import SphereVortex, root_families
from torus_tube import line, advect_material_surface

@pytest.fixture(scope='module')
def flow():
 f=SphereVortex(lam=root_families(1)['lambda1'][0]);return f,line(f,samples=1601)

def test_advected_material_tube_deforms_but_does_not_claim_euler_instability(flow):
 f,c=flow
 d=advect_material_surface(f,c,radius=.004,core_samples=24,ring_samples=6,periods=(0,1,2,4))
 vals=[x['distance_to_core_rms_over_initial_radius'] for x in d['diagnostics']]
 assert vals[0]==pytest.approx(1.,abs=1e-7)
 assert vals[1]>vals[0]*3
 assert vals[-1]>vals[1]
 assert d['self_consistent_3d_euler'] is False

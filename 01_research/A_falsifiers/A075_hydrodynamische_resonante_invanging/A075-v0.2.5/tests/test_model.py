import numpy as np
from experiment.model import Case,initialize,velocities,hamiltonian_parts,impulse,run

def test_closed_geometry():
    x=initialize(24)
    assert x.shape==(2,24,3)
    assert np.all(np.isfinite(x))
    assert abs(np.linalg.norm(x[0,0,:2])-1.0)<1e-14

def test_velocity_finite():
    v=velocities(initialize(24),(1.,1.),0.22)
    assert v.shape==(2,24,3) and np.isfinite(v).all()

def test_energy_symmetric_cross_exchange():
    x=initialize(24)
    h=hamiltonian_parts(x,(1.,1.),0.22)
    h_swap=hamiltonian_parts(x[::-1],(1.,1.),0.22)
    assert np.isclose(h[0],h_swap[1]) and np.isclose(h[2],h_swap[2])

def test_far_pair_coupling_decreases():
    near=hamiltonian_parts(initialize(24,0.7),(1.,1.),0.22)
    far=hamiltonian_parts(initialize(24,12.),(1.,1.),0.22)
    assert abs(far[2])<abs(near[2])

def test_selfenergy_is_not_capture():
    result,_=run(Case(n=24,dt=.05,final_time=.2))
    assert result['scope']=='MIDPOINT_REGULARIZED_FILAMENT_NOT_EULER_CLOSURE'
    assert result['relative_energy_drift']<.02

def test_impulse_translation_invariant():
    x=initialize(24)
    assert np.allclose(impulse(x,(1.,1.)),impulse(x+np.array([0.2,0.1,3.2]),(1.,1.)),rtol=1e-12,atol=1e-12)

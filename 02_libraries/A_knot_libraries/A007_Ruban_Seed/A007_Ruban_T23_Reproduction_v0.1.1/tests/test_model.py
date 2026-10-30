import math
import numpy as np
from ruban_falsifier.model import RubanModel,torus_knot,ring,derivatives
from ruban_falsifier.metrics import length,shape_drift

def test_initial_t23():
    x=torus_knot(128,.154)
    r=np.sqrt(x[:,0]**2+x[:,1]**2)
    assert abs((r.max()-r.min())/2-.154)<2e-3
    assert np.isclose(x[0,2],.154)
    assert np.isfinite(x).all()

def test_derivatives_exact_fourier():
    x=ring(128);xp,xpp=derivatives(x)
    expected=np.stack([-x[:,1],x[:,0],np.zeros(128)],axis=1)
    assert np.max(abs(xp-expected))<1e-11
    assert np.max(abs(xpp+x))<1e-10

def test_ring_symmetry_and_direction():
    m=RubanModel();u=m.velocity(ring(96))
    assert np.std(u[:,2])<1e-11
    assert np.max(abs(u[:,:2]))<1e-11
    assert u[:,2].mean()>0

def test_energy_translation_invariance():
    m=RubanModel();x=torus_knot(64,.154)
    assert np.isclose(m.energy(x),m.energy(x+np.array([4,-8,6])),rtol=1e-12)

def test_single_step_conserves_energy_to_order():
    m=RubanModel();x=torus_knot(64,.154,perturbation=1e-4)
    e0=m.energy(x);y=m.rk4(x,1e-5)
    assert abs(m.energy(y)/e0-1)<1e-7

def test_shape_rigid_invariance():
    x=torus_knot(64,.154)
    a=.3;rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    assert shape_drift(x@rot+np.array([1,2,-5]),x)<2e-3

def test_original_input_sha():
    from pathlib import Path
    from ruban_falsifier.runner import hashfile
    f=Path(__file__).resolve().parents[1]/'inputs/user_3_1.xyz'
    assert hashfile(f)=='38d7ebfb37dc381da081bc13b0bc763b422775e78b4a8d90e4d727eedb161871'

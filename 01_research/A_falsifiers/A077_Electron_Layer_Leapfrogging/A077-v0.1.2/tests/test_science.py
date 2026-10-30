import numpy as np
from science.ring_model import ring_derivative,trajectory,axial_order_crossings

def test_velocity_is_odd_in_circulation():
 y=[1.,-.4,.8,.4];g=[1.,1.];v=[.01,.0064]
 a=ring_derivative(y,g,v,64)
 b=ring_derivative(y,[-x for x in g],v,64)
 np.testing.assert_allclose(a,-b,rtol=1e-13,atol=1e-13)

def test_translation_invariance():
 y=np.array([1.,-.4,.8,.4]); v=[.01,.0064]
 yp=y.copy();yp[1::2]+=4.321
 np.testing.assert_allclose(ring_derivative(yp,[1.,1.],v),ring_derivative(y,[1.,1.],v),rtol=1e-13,atol=1e-13)

def test_one_ring_self_speed():
 y=[1.0,0.];a=.1
 der=ring_derivative(y,[1.],[a*a],64)
 assert der[0]==0 and der[1]>0

def test_core_proxy_conservation():
 sim=trajectory([1.,0.,.8,.3],[1.,1.],[.1,.08],dt=.002,steps=10)
 assert np.isfinite(sim['y']).all()
 assert len(sim['t'])==11
 assert sim['gamma'].tolist()==[1.,1.]

def test_axial_rank_is_not_quantum_level():
 t=[0,1,2];y=np.array([[1,0,1,1],[1,.5,1,.5],[1,1,1,0]])
 assert len(axial_order_crossings(t,y))==1

def test_invalid_quadrature_is_rejected():
 import pytest
 with pytest.raises(ValueError):ring_derivative([1.,0.],[1.],[.01],17)

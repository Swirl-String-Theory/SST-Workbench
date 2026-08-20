import numpy as np
from sst_threaded_hole_falsifier.model import CurveSet
from sst_threaded_hole_falsifier.native import field_velocity,vortex_velocity,min_nonlocal_segment_distance
from sst_threaded_hole_falsifier.pressure import pressure_poisson_metrics

def ring(n=48,R=1.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return CurveSet.from_components([np.c_[R*np.cos(t),R*np.sin(t),np.zeros(n)]])

def test_field_velocity_finite():
    c=ring();u=field_velocity(np.array([[0.,0.,.5],[2.,0.,0.]]),c.points,c.offsets,np.array([1.]),.05);assert u.shape==(2,3);assert np.isfinite(u).all()

def test_vortex_velocity_finite():
    c=ring();u=vortex_velocity(c.points,c.offsets,np.array([1.]),.05);assert u.shape==c.points.shape;assert np.isfinite(u).all()

def test_pressure_metrics_finite():
    c=ring(32);p=pressure_poisson_metrics(c.points,c.offsets,np.array([1.]),.06,8,2.0);assert np.isfinite(p['pressure_center_minus_shell']);assert -1.1<=p['r2_1_over_r']<=1.1

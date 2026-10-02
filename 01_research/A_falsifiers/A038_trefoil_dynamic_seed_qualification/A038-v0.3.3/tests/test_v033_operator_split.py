import numpy as np
from sst_seed_falsifier.geometry import resample_closed
from sst_seed_falsifier.shape_ratio import trefoil_shape_ratio
from sst_seed_falsifier.operator_split import remap_event_times
from sst_seed_falsifier import __version__


def trefoil(n=2048,R=2.0,a=.6,b=.4):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(R+a*np.cos(3*t))*np.cos(2*t),(R+a*np.cos(3*t))*np.sin(2*t),b*np.sin(3*t)]


def test_version(): assert __version__=='0.3.3'

def test_remap_times_are_physical_and_endpoint_excluded():
    assert np.allclose(remap_event_times(1.2,.25),[.25,.5,.75,1.0])

def test_resample_preserves_first_marker():
    x=trefoil(128); y=resample_closed(x,128); assert np.allclose(x[0],y[0])

def test_shape_ratio_recovers_anisotropy():
    x=trefoil(a=.6,b=.4); q=trefoil_shape_ratio(x)
    assert abs(q['chi_eff']-1.5)<0.06

def test_shape_ratio_rigid_and_scale_invariant():
    x=trefoil(a=.6,b=.4); q0=trefoil_shape_ratio(x)['chi_eff']
    ang=.73; R=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1.]])
    y=3.7*(x@R.T)+np.array([7.,-2.,4.]); q1=trefoil_shape_ratio(y)['chi_eff']
    assert abs(q0-q1)<2e-3

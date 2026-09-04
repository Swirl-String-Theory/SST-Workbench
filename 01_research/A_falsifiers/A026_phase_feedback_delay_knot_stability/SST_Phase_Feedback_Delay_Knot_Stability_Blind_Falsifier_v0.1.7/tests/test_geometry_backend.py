import numpy as np
from sst_phase_delay_falsifier.geometry import resample_closed,length,modal_basis,kabsch_rms
from sst_phase_delay_falsifier.backend import biot_savart_velocity,min_gap

def trefoil(n=48):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]

def test_resample_and_basis():
    x=resample_closed(trefoil(),40); assert x.shape==(40,3); assert length(x)>0
    b=modal_basis(x,2); assert len(b)==4; assert all(np.isfinite(q).all() for q in b)

def test_velocity_finite():
    x=resample_closed(trefoil(),32); d=min_gap(x); v=biot_savart_velocity(x,1.0,0.08*d)
    assert np.isfinite(v).all() and np.linalg.norm(v)>0

def test_kabsch_rigid_invariant():
    x=resample_closed(trefoil(),32); a=.4
    R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1.]])
    y=x@R.T+np.array([1,2,3]); assert kabsch_rms(x,y)<1e-10

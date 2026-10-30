import numpy as np
from maxwell_sst_falsifier.native_ext import fallback

def test_circle_writhe_near_zero_python_fallback():
    t=np.linspace(0,2*np.pi,120,endpoint=False)
    p=np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])
    assert abs(fallback.writhe_midpoint(p,True)) < 1e-10

def test_biot_savart_finite():
    t=np.linspace(0,2*np.pi,64,endpoint=False)
    p=np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])
    e=np.array([[0.,0.,0.5],[0.,0.,1.]])
    v=fallback.biot_savart_velocity(p,e,1.0,0.05,True)
    assert v.shape==(2,3)
    assert np.isfinite(v).all()

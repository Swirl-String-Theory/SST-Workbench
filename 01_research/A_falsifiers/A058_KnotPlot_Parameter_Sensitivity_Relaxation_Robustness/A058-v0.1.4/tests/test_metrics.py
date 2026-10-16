import numpy as np
from experiment.metrics import curve_metrics,shape_distance

def test_circle_metrics_and_rigid_invariance():
    t=np.linspace(0,2*np.pi,128,endpoint=False); x=np.c_[np.cos(t),np.sin(t),0*t]
    m=curve_metrics(x); assert abs(m['rg']-1)<1e-12; assert m['edge_cv']<1e-12
    y=x@np.array([[0,-1,0],[1,0,0],[0,0,1]],float).T+np.array([3.,-4.,2.])
    assert shape_distance(x,y,m=64)<1e-10

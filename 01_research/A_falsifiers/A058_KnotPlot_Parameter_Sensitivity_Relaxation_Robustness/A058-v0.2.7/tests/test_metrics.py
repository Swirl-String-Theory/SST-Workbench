import numpy as np
from experiment.metrics import curve_metrics,shape_distance
def test_metrics_rigid_invariance():
    t=np.linspace(0,2*np.pi,128,endpoint=False);x=np.c_[np.cos(t),np.sin(t),0*t];y=x@np.array([[0,-1,0],[1,0,0],[0,0,1]]).T+np.array([2,3,4]);assert shape_distance(x,y,m=128)<1e-10;assert curve_metrics(x)['length']>0

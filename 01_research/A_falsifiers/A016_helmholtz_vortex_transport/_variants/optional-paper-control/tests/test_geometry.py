import numpy as np
from helmholtz_sst.geometry import resample_closed,closure_edge_ratio,thickness_proxy

def test_resample_uniform_circle():
    t=np.linspace(0,2*np.pi,50,endpoint=False);p=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];q=resample_closed(p,160);e=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1);assert e.std()/e.mean()<2e-3
def test_closure_edge_ratio_circle():
    t=np.linspace(0,2*np.pi,50,endpoint=False);p=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];assert closure_edge_ratio(p)<1.1


def test_gauss_linking_hopf():
    from native_ext import gauss_linking
    t=np.linspace(0,2*np.pi,256,endpoint=False);a=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];b=np.c_[0.5+np.cos(t),np.zeros_like(t),np.sin(t)];assert abs(abs(gauss_linking(a,b,0.0,0,force_python=True))-1.0)<2e-3


def test_thickness_proxy_circle_curvature_limited():
    t=np.linspace(0,2*np.pi,256,endpoint=False);p=np.c_[2*np.cos(t),2*np.sin(t),np.zeros_like(t)];tp=thickness_proxy([p],0);assert abs(tp['thickness_proxy']-2.0)<0.08

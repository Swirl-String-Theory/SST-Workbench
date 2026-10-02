import numpy as np
from sst_qhp_falsifier.geometry import best_cyclic_align,normal_component
from sst_qhp_falsifier.manifold import gram_projection

def test_alignment_rigid_cyclic():
    t=np.linspace(0,2*np.pi,64,endpoint=False); x=np.c_[np.cos(t),np.sin(t),.2*np.sin(3*t)]; R=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
    y=np.roll(x@R.T,9,axis=0); z,m=best_cyclic_align(y,x); assert m['mse']<1e-20

def test_projection_recovers_coefficients():
    t=np.linspace(0,2*np.pi,32,endpoint=False); x=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]; A=normal_component(np.c_[np.cos(t),np.sin(t),np.zeros_like(t)],x); B=normal_component(np.c_[np.cos(2*t),np.sin(2*t),np.zeros_like(t)],x); U=2*A-.3*B; c,f=gram_projection(U,{'q':A,'h':B,'p':None}); assert abs(c['q']-2)<1e-10 and abs(c['h']+.3)<1e-10

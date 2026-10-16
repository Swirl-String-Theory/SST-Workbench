import numpy as np
from a060.core import overlap_series,two_mode_observables
def test_overlap_initial_one():
 t=np.linspace(0,1,10); x=np.c_[np.cos(t),1j*np.sin(t)]
 assert abs(overlap_series(x)[0]-1)<1e-12
def test_two_mode_bounded():
 t=np.linspace(0,3,20); m=np.c_[np.ones(20),np.exp(1j*t)]
 o=two_mode_observables(m); assert 0<=o["R12"]<=1+1e-12

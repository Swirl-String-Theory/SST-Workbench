import numpy as np
from einstein_sst_gates.synthetic import circle
from einstein_sst_gates.geometry import velocity_gradient_py
from einstein_sst_gates.analysis import gradient_invariants

def test_pressure_poisson_identity():
    p=circle(128,4.0);q=np.array([[8.,1.,2.],[3.,0.,7.],[-6.,2.,5.]])
    v,g=velocity_gradient_py(p,q,1.0,1.0);Q,D,om,S,div=gradient_invariants(v,g)
    assert np.max(np.abs(Q-D))<1e-12
    assert np.max(np.abs(div))<1e-12

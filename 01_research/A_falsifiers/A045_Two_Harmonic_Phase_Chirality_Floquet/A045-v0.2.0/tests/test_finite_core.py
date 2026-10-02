import numpy as np
from sst_thpcf.geometry import torus_trefoil, rz
from sst_thpcf.dynamics import finite_core_velocity_python

def test_finite_core_rotational_covariance():
    X=torus_trefoil(48); R=rz(.731)
    v=finite_core_velocity_python(X,1.0,1.0,2)
    vr=finite_core_velocity_python(X@R.T,1.0,1.0,2)
    assert np.linalg.norm(vr-v@R.T)/(np.linalg.norm(v)+1e-30) < 1e-12

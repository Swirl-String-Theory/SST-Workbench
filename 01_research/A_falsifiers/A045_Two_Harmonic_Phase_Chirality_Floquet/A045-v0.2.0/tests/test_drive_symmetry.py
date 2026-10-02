import numpy as np
from sst_thpcf.drive import c3_dynamic_symmetry_residual, drive_vector
from sst_thpcf.geometry import rz

def test_cnr_has_c3_dynamic_symmetry():
    assert c3_dynamic_symmetry_residual(1.0,1.0,0.65,0.37,"CNR") < 1e-10

def test_cor_is_control():
    assert c3_dynamic_symmetry_residual(1.0,1.0,0.65,0.37,"COR") > 1e-2

def test_cnr_vector_covariance():
    T=2*np.pi; R=rz(2*np.pi/3); t=.271
    a=drive_vector(t,1,1,.65,.41,"CNR"); b=drive_vector(t+T/3,1,1,.65,.41,"CNR")
    assert np.linalg.norm(b-R@a) < 1e-12

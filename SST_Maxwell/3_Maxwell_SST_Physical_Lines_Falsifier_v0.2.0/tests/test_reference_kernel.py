import numpy as np
from sst_maxwell3_blind.native import python_biot_savart_velocity

def test_gamma_odd():
    s=np.array([[0.2,0.1,0.3],[0.3,-0.2,0.1]])
    a=np.array([[0.,0.,0.],[1.,0.,0.]])
    b=np.array([[1.,0.,0.],[1.,1.,0.]])
    vp=python_biot_savart_velocity(s,a,b,2.0,0.1)
    vm=python_biot_savart_velocity(s,a,b,-2.0,0.1)
    assert np.allclose(vp,-vm,rtol=1e-13,atol=1e-13)

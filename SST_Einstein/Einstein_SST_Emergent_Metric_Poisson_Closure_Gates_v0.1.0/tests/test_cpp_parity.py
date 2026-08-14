import numpy as np, pytest
from einstein_sst_gates.synthetic import circle
from einstein_sst_gates.geometry import HAVE_CPP,field_velocity_gradient,velocity_gradient_py
@pytest.mark.skipif(not HAVE_CPP,reason='C++ extension not built')
def test_cpp_python_field_parity():
    p=circle(128,4.0);q=np.array([[10.,1.,2.],[0.,0.,8.]])
    vc,gc=field_velocity_gradient(p,q,1.0,1.0,True);vp,gp=velocity_gradient_py(p,q,1.0,1.0)
    assert np.allclose(vc,vp,rtol=2e-12,atol=2e-13);assert np.allclose(gc,gp,rtol=2e-12,atol=2e-13)

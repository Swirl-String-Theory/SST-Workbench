import numpy as np, pytest
from einstein_sst_gates.synthetic import circle
from einstein_sst_gates.geometry import (
    HAVE_CPP,
    estimate_thickness,
    estimate_thickness_py,
    field_velocity_gradient,
    velocity_gradient_py,
)
@pytest.mark.skipif(not HAVE_CPP,reason='C++ extension not built')
def test_cpp_python_field_parity():
    p=circle(128,4.0);q=np.array([[10.,1.,2.],[0.,0.,8.]])
    vc,gc=field_velocity_gradient(p,q,1.0,1.0,True);vp,gp=velocity_gradient_py(p,q,1.0,1.0)
    assert np.allclose(vc,vp,rtol=2e-12,atol=2e-13);assert np.allclose(gc,gp,rtol=2e-12,atol=2e-13)

@pytest.mark.skipif(not HAVE_CPP,reason='C++ extension not built')
def test_cpp_python_thickness_parity():
    # n>256 hits the OpenMP branch of estimate_thickness (thread-local min merge).
    p=circle(300,4.0)
    dc=estimate_thickness(p,8,True)
    dp=estimate_thickness_py(p,8)
    assert dc["limiter"]==dp["limiter"]
    for key in ("thickness","local_curvature_radius_min","nonlocal_half_distance_min"):
        assert np.isclose(dc[key],dp[key],rtol=2e-12,atol=2e-13)

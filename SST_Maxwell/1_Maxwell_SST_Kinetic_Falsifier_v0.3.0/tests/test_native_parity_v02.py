import numpy as np
import pytest
from maxwell_sst_falsifier.native_ext import backend_info
from maxwell_sst_falsifier.native_ext import fallback
from maxwell_sst_falsifier.native_ext.core import biot_savart_velocity, writhe_midpoint, min_segment_distance


def _circle(n=72):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])


def test_cpp_python_parity_when_native_available():
    if not backend_info(verbose=False)["native"]:
        pytest.skip("native C++ backend unavailable in this environment")
    p=_circle(); q=p+np.array([3.0,0.2,0.1])
    e=p[:8]
    v_cpp=np.asarray(biot_savart_velocity(q,e,1.0,0.05,True))
    v_py=np.asarray(fallback.biot_savart_velocity(q,e,1.0,0.05,True))
    assert np.allclose(v_cpp,v_py,rtol=1e-11,atol=1e-12)
    assert abs(writhe_midpoint(p,True)-fallback.writhe_midpoint(p,True))<1e-11
    assert abs(min_segment_distance(p,q,True,True)-fallback.min_segment_distance(p,q,True,True))<1e-11

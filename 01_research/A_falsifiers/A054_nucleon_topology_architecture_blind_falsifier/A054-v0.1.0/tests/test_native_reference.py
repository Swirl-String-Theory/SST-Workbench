import numpy as np, pytest
from a054_ntaf.geometry import torus_link_3_3
from a054_ntaf.physics import _all_segments, induced_velocity

def test_native_reference_if_built():
    try:
        from a054_ntaf import _native
    except ImportError:
        pytest.skip('optional native extension not built')
    c=torus_link_3_3(48); g=np.ones(3)/3
    mids,dls,gs=_all_segments(c,g); targets=np.vstack(c)[:20]
    py=induced_velocity(targets,c,g,0.02)
    cpp=_native.induced_velocity(targets,mids,dls,gs,0.02)
    assert np.max(np.abs(py-cpp))<1e-11

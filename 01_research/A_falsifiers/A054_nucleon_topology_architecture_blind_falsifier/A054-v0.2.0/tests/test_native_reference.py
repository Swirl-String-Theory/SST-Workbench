import numpy as np, pytest
from a054_ntaf.geometry import torus_link_3_3
from a054_ntaf.physics import induced_velocity_numpy, induced_velocity_native


def test_native_reference_if_built():
    try:
        from a054_ntaf import _native  # noqa: F401
    except ImportError:
        pytest.skip('optional native extension not built')
    c=torus_link_3_3(48); g=np.ones(3)/3; targets=np.vstack(c)[:20]
    py=induced_velocity_numpy(targets,c,g,0.02)
    cpp=induced_velocity_native(targets,c,g,0.02)
    assert np.max(np.abs(py-cpp))<1e-11

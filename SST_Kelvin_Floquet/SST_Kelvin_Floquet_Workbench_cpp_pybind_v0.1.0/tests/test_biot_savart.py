import numpy as np
from sst_kelvin_workbench.backend import load_backend
from sst_kelvin_workbench import fallback
from sst_kelvin_workbench.kelvin import make_ring, ring_linear_mode


def test_biot_savart_python_reference_finite():
    q=make_ring(20,1.0)
    u=fallback.induced_velocity(q,q,1.0,0.05)
    assert u.shape==q.shape
    assert np.all(np.isfinite(u))


def test_ring_linear_mode_is_finite():
    r=ring_linear_mode(3,n=24,force_python=True,skip_build=True)
    assert np.isfinite(r['omega_hat'])
    assert r['omega_hat'] > 0

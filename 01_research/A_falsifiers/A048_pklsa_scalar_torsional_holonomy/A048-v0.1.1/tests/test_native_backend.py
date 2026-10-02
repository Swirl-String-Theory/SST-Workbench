import importlib.util
import numpy as np
import pytest

def test_native_parity_if_available():
    if importlib.util.find_spec('torsion_native') is None: pytest.skip('native extension not built')
    import torsion_native
    k=np.arange(1.0,11.0)
    assert np.max(np.abs(np.asarray(torsion_native.kelvin_omega(k,0.2))-0.2*k*k))<1e-12
    assert abs(torsion_native.loglog_slope(k,0.2*k*k)-2.0)<1e-12

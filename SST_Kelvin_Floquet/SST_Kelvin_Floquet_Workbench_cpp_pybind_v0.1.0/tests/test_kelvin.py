import math
import numpy as np
from sst_kelvin_workbench.backend import load_backend
from sst_kelvin_workbench import fallback
from sst_kelvin_workbench.kelvin import rankine_bending_branch


def test_longwave_native_python_parity():
    b,_=load_backend(force_python=True)
    xs=np.array([0.01,0.05,0.1,0.3])
    a=b.kelvin_long_wave_hat_array(xs)
    c=fallback.kelvin_long_wave_hat_array(xs)
    assert np.max(np.abs(a-c)) < 1e-14


def test_rankine_small_x_branch_matches_longwave_magnitude():
    rows=rankine_bending_branch([0.05,0.10],scan_points=1800)
    assert all(r['root_found'] for r in rows)
    for r in rows:
        rel=abs(r['abs_omega_over_Omega0']-r['long_wave_abs_over_Omega0'])/r['long_wave_abs_over_Omega0']
        assert rel < 0.12

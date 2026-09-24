import numpy as np
from sst_kelvin_workbench.backend import load_backend
from sst_kelvin_workbench.bridge import c006_hat_to_a029_time, k_closed, p_of_zero
from sst_kelvin_workbench.kelvin import make_ring
from sst_kelvin_workbench.measure import radial_grid


def test_time_map_independent_of_omega():
    t = c006_hat_to_a029_time(np.array([1.0]), R_eff=1.0, a_core=0.05)
    assert abs(float(t[0]) - 800.0) < 1e-9


def test_k_closed_embeds_holonomy():
    assert abs(k_closed(1, 1, 0.0, 2.0 * np.pi) - 1.0) < 1e-12


def test_p_of_zero_on_ring():
    backend, _ = load_backend(force_python=True, skip_build=True)
    ring = make_ring(16, 1.0)
    r = radial_grid(8, 5.0)
    rec = p_of_zero(ring, a=0.05, r=r, n_theta=4, gamma=1.0, eps=0.05, backend=backend)
    assert rec["ok"] is True

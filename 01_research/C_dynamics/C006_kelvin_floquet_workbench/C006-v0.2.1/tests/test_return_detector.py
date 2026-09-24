import numpy as np
from sst_kelvin_workbench.return_detector import (
    autocorrelation,
    first_qualified_local_max,
    fit_omega_td,
    unwrap_phase,
)


def test_first_local_max_not_global_argmax():
    tau = np.linspace(0.0, 2.0, 41)
    C = np.exp(-((tau - 0.3) ** 2) / 0.01) * 0.6
    C += np.exp(-((tau - 1.5) ** 2) / 0.01) * 1.0
    rec = first_qualified_local_max(tau, C, tau_min=0.05, tau_max=1.8, C_min=0.3)
    assert rec["found"] is True
    assert rec["tau_return"] < 0.6


def test_unwrap_and_omega_fit():
    t = np.linspace(0.0, 2.0, 40)
    omega = 1.7
    a = np.exp(1j * (0.2 + omega * t))
    unw = unwrap_phase(a, amplitude_floor=0.1)
    fit = fit_omega_td(t[unw["t_index"]], unw["phi"])
    assert abs(fit["omega_td"] - omega) < 1e-6


def test_autocorr_peak_at_zero():
    E = np.array([1.0, 0.4, 0.2, 0.1, 0.05])
    C = autocorrelation(E)
    assert C[0] == 1.0
    assert C[0] >= np.max(C[1:])

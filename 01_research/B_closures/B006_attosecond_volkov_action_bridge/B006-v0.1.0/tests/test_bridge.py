import numpy as np
import pytest

from sst_attosecond_bridge.bridge import (
    discrete_amplitudes,
    directional_residual,
    global_phase_null,
    phase_from_specific_action,
    temporal_relative_phase,
)


def toy_kernel(n_sample=4, n_time=301):
    t = np.linspace(-3.0, 3.0, n_time)
    w = np.gradient(t)
    rows = []
    for j in range(n_sample):
        env = np.exp(-0.5 * (t / (0.8 + 0.05*j))**2)
        rows.append(env * np.exp(1j * (0.35*j*t + 0.08*t*t)))
    return t, np.asarray(rows), w


def test_specific_action_phase_is_dimensionless_ratio():
    ds = np.array([1e-9, -2e-9])
    hs = 4e-8
    assert np.allclose(phase_from_specific_action(ds, hs), [0.025, -0.05])


def test_global_phase_is_unobservable_in_intensity():
    _, k, w = toy_kernel()
    q = global_phase_null(k, w)
    assert q["pass_1e_12"]


def test_time_varying_phase_changes_intensity_and_linear_limit():
    t, k, w = toy_kernel()
    ph = 2e-3 * np.tile(t, (k.shape[0], 1))
    r = discrete_amplitudes(k, w, ph)
    assert np.max(np.abs(r.delta_intensity_exact)) > 0
    scale = max(float(np.max(np.abs(r.delta_intensity_exact))), 1e-30)
    assert np.max(np.abs(r.delta_intensity_exact-r.delta_intensity_linear))/scale < 0.01


def test_relative_phase_removes_constant_component():
    _, k, w = toy_kernel()
    ph = np.ones(k.shape) * 0.4
    q = temporal_relative_phase(ph, w)
    assert q["max_relative_phase_rms_rad"] < 1e-14


def test_directional_residual_removes_orthodox_asymmetry():
    op = np.array([1.2, 2.0]); om = np.array([1.0, 1.5])
    # If data equal orthodox prediction, residual is exactly zero.
    assert np.allclose(directional_residual(op, om, op, om), 0.0)

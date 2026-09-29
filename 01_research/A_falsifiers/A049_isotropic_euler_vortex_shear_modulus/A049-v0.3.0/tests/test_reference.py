import math
import numpy as np
from sst_vortex_shear.sampling import paired_transverse_samples, shear_matrix, rotation_matrix
from sst_vortex_shear.reference import (
    energy_ratio_general,
    fit_even_energy_coefficient,
    isotropy_tensor,
    transverse_residual,
)


def test_transverse_sampling():
    n, w, n0, _, _ = paired_transverse_samples(1000)
    assert transverse_residual(n, w) < 1e-13
    assert np.linalg.norm(isotropy_tensor(n0) - np.eye(3)/3.0) < 6e-5


def test_affine_coefficient_recovers_two_over_fifteen():
    n, w, _, _, _ = paired_transverse_samples(4000)
    gs = np.array([0.005, 0.01, 0.02, 0.04, 0.08])
    rp = [energy_ratio_general(n, w, shear_matrix(g, "xy")) for g in gs]
    rm = [energy_ratio_general(n, w, shear_matrix(-g, "xy")) for g in gs]
    fit = fit_even_energy_coefficient(gs, rp, rm)
    assert abs(fit["A2"] - 2/15) / (2/15) < 6e-5


def test_objectivity():
    n, w, _, _, _ = paired_transverse_samples(800)
    f = shear_matrix(0.031, "xy")
    r0 = energy_ratio_general(n, w, f)
    q = rotation_matrix(19)
    r1 = energy_ratio_general(n @ q.T, w @ q.T, q @ f @ q.T)
    assert abs(r1-r0) < 1e-12


def test_inverse_cycle_returns_baseline():
    n, w, _, _, _ = paired_transverse_samples(800)
    f = shear_matrix(0.07, "yz")
    fc = np.linalg.inv(f) @ f
    assert abs(energy_ratio_general(n, w, fc) - 1.0) < 1e-12

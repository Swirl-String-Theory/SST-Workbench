import numpy as np
from scipy.linalg import eig
from sst_kelvin_workbench.measure import block_measure, cylindrical_weights, radial_grid, weighted_inner
from sst_kelvin_workbench.mode_recon import left_eigenvector, match_frozen_scalars, normalize_biorthogonal


def test_left_eigenvector_is_not_right_for_nonnormal():
    A = np.array([[1.0, 4.0], [0.0, 2.0]], dtype=complex)
    B = np.eye(2, dtype=complex)
    w, vr = eig(A, B)
    q = vr[:, 0]
    p = left_eigenvector(A, B, w[0], q)
    assert np.linalg.norm(p / p[0] - q / q[0]) > 1e-6


def test_normalize_biorthogonal_unit():
    r = radial_grid(8, 5.0)
    W = block_measure(cylindrical_weights(r, 5.0), 1)
    q = np.exp(-r)
    p, resid = normalize_biorthogonal(q, q, W, None)
    assert abs(resid) < 1e-12
    assert abs(weighted_inner(p, q, W) - 1.0) < 1e-12


def test_match_rejects_wrong_branch():
    frozen = {
        "lambda": {"real": 0.0, "imag": -1.0},
        "omega": 1.0,
        "omega_intrinsic": -0.2,
        "growth": 0.0,
        "core_localization": 0.9,
        "axial_energy_fraction": 0.5,
        "hybrid_score": 0.8,
        "residual": 1e-14,
    }
    mode = dict(frozen)
    mode["lambda"] = 0.0 - 1.0j
    mode["omega"] = 2.5
    thr = {
        "omega_rel_tol": 1e-4,
        "omega_intrinsic_rel_tol": 0.001,
        "growth_abs_tol": 1e-6,
        "lambda_real_abs_tol": 1e-6,
        "lambda_imag_rel_tol": 1e-4,
        "localization_abs_tol": 0.001,
        "axial_energy_abs_tol": 0.001,
        "hybrid_abs_tol": 0.001,
        "residual_max": 1e-7,
    }
    assert match_frozen_scalars(mode, frozen, thr)["ok"] is False


def test_reconstruct_frozen_carrier_same_branch():
    from sst_kelvin_workbench.mode_recon import reconstruct_mode

    sealed = reconstruct_mode()
    assert sealed["record"]["status"] == "RECONSTRUCTED_SAME_BRANCH"
    assert sealed["q"] is not None
    assert sealed["p"] is not None
    assert abs(sealed["record"]["m"]) == 1

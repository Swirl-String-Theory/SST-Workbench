import numpy as np
from sst_link_suite.symplectic import symplectic_kernel_quotient, quotient_linearized_spectrum


def test_symplectic_kernel_quotient_finds_known_kernel():
    omega = np.array([
        [0, 1, 0, 0],
        [-1, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=float)
    result = symplectic_kernel_quotient(omega, rank_tolerance=1e-10)
    assert result["rank"] == 2
    assert result["nullity"] == 2
    assert result["quotient_dimension"] == 2
    assert result["quotient_full_rank"]
    assert result["physical_quotient_established"] is False


def test_quotient_spectrum_runs_on_image_space():
    omega = np.array([
        [0, 1, 0, 0],
        [-1, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ], dtype=float)
    h = np.diag([1.0, 1.0, 2.0, 3.0])
    result = quotient_linearized_spectrum(omega, h, rank_tolerance=1e-10)
    assert result["quotient_dimension"] == 2
    assert result["unstable_mode_count"] == 0

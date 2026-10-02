import numpy as np

from sst_kelvin_workbench.darboux import (
    best_intertwiner,
    sector_intertwining_diagnostic,
    synthetic_darboux_selftest,
)


def test_synthetic_darboux_selftest_passes():
    r = synthetic_darboux_selftest(32)
    assert r["pass"]
    assert r["adjoint_defect"] < 1e-12
    assert r["isospectral_relative_max"] < 1e-10


def test_best_intertwiner_identical_matrices():
    A = np.diag([1.0, 2.0]).astype(complex)
    r = best_intertwiner(A, A)
    assert r["relative_residual"] < 1e-12


def test_sector_pretest_never_promotes_to_strict_darboux():
    G = np.diag([1j, 1j, -1j, -1j]).astype(complex)
    r = sector_intertwining_diagnostic(G)
    assert r["pretest_pass"]
    assert r["strict_darboux_status"] == "SKIP_NO_SCALAR_SECOND_ORDER_OPERATOR_PAIR"

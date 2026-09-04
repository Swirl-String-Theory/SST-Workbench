from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext import constants
from fermat_ext.certification import (
    estimate_reach_diagnostic,
    scan_stationary_candidates,
    symmetry_field_audit,
)
from fermat_ext.core import backend_biot_savart_with_jacobian
from fermat_ext.knot_catalog import sample_ideal_knot


def main() -> int:
    curve = sample_ideal_knot("0_1", 256)
    probes = np.asarray([[1.02, 0.0, 0.01], [0.0, 1.01, -0.02]])
    beta, jac, backend = backend_biot_savart_with_jacobian(
        curve.tolist(), probes.tolist(), epsilon=0.0019,
        force_python=True, auto_build=False,
    )
    beta = np.asarray(beta); jac = np.asarray(jac)
    assert backend["backend"] == "python"
    assert beta.shape == (2, 3)
    assert jac.shape == (2, 3, 3)

    # Independent finite-difference check of the Python analytic Jacobian.
    h = 1e-6
    for j in range(3):
        pp = probes.copy(); pm = probes.copy()
        pp[:, j] += h; pm[:, j] -= h
        bp, _, _ = backend_biot_savart_with_jacobian(
            curve.tolist(), pp.tolist(), epsilon=0.0019,
            force_python=True, auto_build=False,
        )
        bm, _, _ = backend_biot_savart_with_jacobian(
            curve.tolist(), pm.tolist(), epsilon=0.0019,
            force_python=True, auto_build=False,
        )
        fd = (np.asarray(bp) - np.asarray(bm)) / (2*h)
        assert float(np.max(np.abs(fd - jac[:, :, j]))) < 1e-7

    reach = estimate_reach_diagnostic(curve, max_pair_points=256)
    assert reach["rigorous_certificate"] is False
    assert abs(float(reach["reach_estimate_over_rc"]) - 1.0) < 0.01

    # A deliberately modest but sufficiently resolved circle scan must find
    # the Rosenhead stationary max/min pair in the horizon-free window.
    atlas = scan_stationary_candidates(
        "0_1", epsilon=0.0019, centerline_points=2048,
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01,
        bracket_samples=64, force_python=True, auto_build=False,
        reach_pair_points=256,
    )
    assert atlas["local_minimum_count"] >= 1
    assert atlas["invalid_clock_probe_count"] == 0
    assert atlas["global_closed_orbit_certified"] is False
    assert all(abs(float(r["stationary_residual_G"])) < 1e-7 for r in atlas["roots"])

    sym = symmetry_field_audit(
        "0_1", epsilon=0.0019, centerline_points=256,
        stations=1, angles=3, rho_values=(0.002,),
        force_python=True, auto_build=False,
    )
    assert sym["max_beta_vector_linf_error"] < 1e-11
    assert sym["max_jacobian_linf_error"] < 1e-9
    assert sym["max_scalar_G_linf_error"] < 1e-11

    assert constants.ROSENHEAD_HORIZON_THRESHOLD < constants.ROSENHEAD_CRITICAL_THRESHOLD
    print("v0.4 tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext.certification import approximate_reach_diagnostic, scan_stationary_candidates
from fermat_ext.core import backend_biot_savart_field_jacobian
from fermat_ext.knot_catalog import sample_ideal_knot


def main() -> int:
    curve = sample_ideal_knot("0_1", 512)
    probes = np.asarray([[1.0, 0.0, -0.0035], [0.5, 0.5, 0.004]], dtype=float)
    raw, _ = backend_biot_savart_field_jacobian(
        curve.tolist(), probes.tolist(), epsilon=0.0019,
        force_python=True, auto_build=False,
    )
    jac = np.asarray(raw["jacobian"], dtype=float)
    h = 1e-7
    fd = np.empty_like(jac)
    for axis in range(3):
        delta = np.zeros(3); delta[axis] = h
        plus, _ = backend_biot_savart_field_jacobian(
            curve.tolist(), (probes + delta).tolist(), epsilon=0.0019,
            force_python=True, auto_build=False,
        )
        minus, _ = backend_biot_savart_field_jacobian(
            curve.tolist(), (probes - delta).tolist(), epsilon=0.0019,
            force_python=True, auto_build=False,
        )
        fd[:, :, axis] = (
            np.asarray(plus["beta"], dtype=float) - np.asarray(minus["beta"], dtype=float)
        ) / (2.0 * h)
    assert float(np.max(np.abs(fd - jac))) < 1e-6

    regular = scan_stationary_candidates(
        "0_1", epsilon=0.0019, centerline_points=2048,
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01,
        bracket_samples=64, force_python=True, auto_build=False,
        reach_pair_points=512,
    )
    assert regular["local_minimum_count"] == 3
    assert regular["invalid_clock_probe_count"] == 0

    clock_crossing = scan_stationary_candidates(
        "0_1", epsilon=0.0010, centerline_points=2048,
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01,
        bracket_samples=64, force_python=True, auto_build=False,
        reach_pair_points=512,
    )
    assert clock_crossing["invalid_clock_probe_count"] > 0
    assert clock_crossing["clock_boundary_bracket_count"] > 0
    assert all(root["clock_valid"] for root in clock_crossing["roots"])

    reach = approximate_reach_diagnostic(sample_ideal_knot("0_1", 2048), pair_points=1024)
    assert reach["rigorous_certificate"] is False
    assert abs(reach["reach_estimate_over_rc"] - 1.0) < 0.01

    print("v0.4.2 tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

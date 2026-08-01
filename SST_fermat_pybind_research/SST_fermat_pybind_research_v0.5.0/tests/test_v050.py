from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.geodesic import compute_reduced_monodromy, integrate_ray, shoot_closed_orbit
from fermat_ext.knot_catalog import sample_ideal_knot


def constant_clock(point: np.ndarray):
    return 1.0, np.zeros(3), {
        "backend": {"backend": "analytic-test"},
        "beta": np.zeros(3),
        "S": 1.0,
    }


def main() -> int:
    straight = integrate_ray(
        [0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
        path_length=2.0, step_count=32, clock_evaluator=constant_clock,
        record_stride=32,
    )
    assert straight["status"] == "COMPLETED"
    assert np.linalg.norm(np.asarray(straight["final_position_over_rc"]) - np.asarray([2.0, 0.0, 0.0])) < 1e-12
    assert np.linalg.norm(np.asarray(straight["final_direction"]) - np.asarray([1.0, 0.0, 0.0])) < 1e-12
    assert abs(straight["optical_length_over_rc"] - 2.0) < 1e-12

    atlas = scan_stationary_candidates(
        "0_1", epsilon=0.0019, centerline_points=2048,
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01,
        bracket_samples=48, force_python=True, auto_build=False,
        reach_pair_points=128,
    )
    roots = [r for r in atlas["roots"] if r["classification"] == "RESOLVED_LOCAL_MINIMUM"]
    assert roots
    root = roots[0]
    seed = {
        **root,
        "directions": [root["azimuthal_seed_direction"], [-v for v in root["azimuthal_seed_direction"]]],
    }
    curve = sample_ideal_knot("0_1", 2048)
    shot = shoot_closed_orbit(
        curve, seed, epsilon=0.0019, step_count=32, max_iterations=0,
        force_python=True, auto_build=False,
        position_tolerance_over_rc=1e-6, direction_tolerance=1e-6,
    )
    assert shot["schema"] == "sst.fermat.closed-orbit-shot.v0.5.0"
    assert shot["global_closed_orbit_certified"] is False
    assert shot["qsm_certified"] is False
    assert "best" in shot

    monodromy = compute_reduced_monodromy(
        curve, shot, epsilon=0.0019,
        position_perturbation_fraction=1e-5,
        direction_perturbation=1e-5,
        force_python=True, auto_build=False,
    )
    matrix = np.asarray(monodromy["matrix"], dtype=float)
    assert matrix.shape == (4, 4)
    assert np.all(np.isfinite(matrix))
    assert monodromy["monodromy_certified"] is False
    assert monodromy["qsm_certified"] is False

    print("v0.5.0 tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

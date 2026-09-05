from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext.hole_bundle import (
    BundleGridDefinition,
    HoleBundleParameters,
    RigidMotionProjector,
    axis_direction_from_tilts,
    bundle_beta_and_jacobian,
    fourier_mode_projection,
)


def test_grid() -> None:
    grid = BundleGridDefinition()
    radii, gamma = grid.values()
    assert math.isclose(radii[0], 0.06125, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(radii[-1], 8.0, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(gamma[0], -8.0, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(gamma[-1], 8.0, rel_tol=0, abs_tol=1e-15)
    assert np.any(np.isclose(gamma, 0.0))
    assert np.all(np.diff(radii) > 0)
    assert np.all(np.diff(gamma) > 0)


def test_bundle_jacobian() -> None:
    params = HoleBundleParameters(0.7, 2.1, -1.3, axis_direction=axis_direction_from_tilts(3.0, -2.0))
    points = np.array([[0.3, 0.2, -0.1], [0.9, -0.25, 0.4], [2.5, 0.1, 0.0]], float)
    beta, jac = bundle_beta_and_jacobian(points, params)
    assert beta.shape == (3, 3)
    assert jac.shape == (3, 3, 3)
    assert np.all(np.isfinite(beta)) and np.all(np.isfinite(jac))
    h = 2e-6
    for i in range(len(points)):
        num = np.zeros((3, 3))
        for k in range(3):
            pp = points[[i]].copy()
            pm = points[[i]].copy()
            pp[0, k] += h
            pm[0, k] -= h
            bp, _ = bundle_beta_and_jacobian(pp, params)
            bm, _ = bundle_beta_and_jacobian(pm, params)
            num[:, k] = (bp[0] - bm[0]) / (2 * h)
        assert np.max(np.abs(num - jac[i])) < 2e-7


def test_rigid_projector() -> None:
    t = np.linspace(0, 2 * np.pi, 128, endpoint=False)
    points = np.column_stack([np.cos(t), np.sin(t), 0.2 * np.sin(2 * t)])
    U = np.array([0.2, -0.1, 0.05])
    omega = np.array([0.1, 0.3, -0.2])
    centered = points - points.mean(axis=0)
    velocities = U + np.cross(np.broadcast_to(omega, centered.shape), centered)
    fit = RigidMotionProjector(points).fit(velocities)
    assert fit["relative_shape_residual"] < 1e-12


def test_mode_projection() -> None:
    t = np.linspace(0, 2 * np.pi, 256, endpoint=False)
    base = np.column_stack([np.cos(3 * t), np.sin(3 * t), 0.2 * np.cos(5 * t)])
    bundled = 0.5 * base
    result = fourier_mode_projection(base, bundled, max_mode=8)
    modes = {row["mode"]: row for row in result["rows"]}
    assert abs(modes[3]["mode_energy_gain"] - 0.75) < 1e-12
    assert abs(modes[5]["mode_energy_gain"] - 0.75) < 1e-12


def main() -> int:
    test_grid()
    test_bundle_jacobian()
    test_rigid_projector()
    test_mode_projection()
    print("v0.6.1 tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

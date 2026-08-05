from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src" / "sst_dimensionless_ratios.py"
spec = importlib.util.spec_from_file_location("sst_dimensionless_ratios", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_ring_normalization_and_relative_equilibrium() -> None:
    points = mod.generate_ring(96)
    points = mod.normalize_curve(points, "fixed_length", target_length=2.0 * math.pi)
    protocol = mod.NumericalProtocol(resolution=96, epsilon=0.08)
    source = mod.CurveSource("ring", "ring", "generator", "ring")
    diag = mod.static_diagnostics(source, points, protocol)
    assert abs(diag.length - 2.0 * math.pi) < 5e-3
    assert diag.relative_motion["projected_residual"] < 0.02
    assert diag.sampled_reach > 0.8


def test_ideal_parser_and_mirror_energy_parity() -> None:
    text = (ROOT / "data" / "ideal_favorites.txt").read_text(encoding="utf-8")
    p = mod.reconstruct_ideal_ab(text, "3:1:1", 256, mirror=False)
    q = mod.reconstruct_ideal_ab(text, "3:1:1", 256, mirror=True)
    p = mod.uniform_arclength_resample(p, 96)
    q = mod.uniform_arclength_resample(q, 96)
    p = mod.normalize_curve(p, "fixed_length")
    q = mod.normalize_curve(q, "fixed_length")
    ep = mod.self_induction_energy_proxy(p, 0.08)
    eq = mod.self_induction_energy_proxy(q, 0.08)
    assert np.isclose(ep, eq, rtol=1e-12, atol=1e-12)


def test_three_kernels_are_finite() -> None:
    p = mod.normalize_curve(mod.generate_ring(64), "fixed_length")
    for kernel in ["rosenhead", "rankine", "winckelmans"]:
        u = mod.biot_savart_velocity(p, 0.08, kernel=kernel)
        assert np.isfinite(u).all()


def test_recurrence_identity() -> None:
    p = mod.generate_torus_trefoil(64)
    rec = mod.best_cyclic_recurrence(p, np.roll(p, 7, axis=0))
    assert rec["normalized_rmsd"] < 1e-12


def test_infinite_solid_body_background_velocity() -> None:
    points = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 1.0],
        [-1.0, 0.0, 1.0],
        [0.0, -1.0, 1.0],
    ])
    bg = mod.BackgroundFlowProtocol(
        kind="infinite_solid_body_vortex",
        dimensionless_vorticity=2.0,
    )
    u = mod.background_velocity(points, bg)
    # zeta=2 gives Omega=1 around +z: u=(-y,x,0).
    expected = np.column_stack([-points[:, 1], points[:, 0], np.zeros(len(points))])
    assert np.allclose(u, expected, rtol=0.0, atol=1e-14)


def test_solid_body_background_does_not_change_relative_residual() -> None:
    text = (ROOT / "data" / "ideal_favorites.txt").read_text(encoding="utf-8")
    p = mod.reconstruct_ideal_ab(text, "3:1:1", 256, mirror=False)
    p = mod.uniform_arclength_resample(p, 128)
    p = mod.normalize_curve(p, "fixed_length")
    source = mod.CurveSource("3:1:1", "trefoil", "ideal_ab")
    base = mod.NumericalProtocol(resolution=128, epsilon=0.08)
    bg = mod.NumericalProtocol(
        resolution=128,
        epsilon=0.08,
        background_flow=mod.BackgroundFlowProtocol(
            kind="infinite_solid_body_vortex",
            dimensionless_vorticity=1.0 / math.pi,
            provenance="sst_gamma0_over_pi",
        ),
    )
    d0 = mod.static_diagnostics(source, p, base)
    d1 = mod.static_diagnostics(source, p, bg)
    assert abs(
        d1.relative_motion["projected_residual_intrinsic"]
        - d0.relative_motion["projected_residual_intrinsic"]
    ) < 1e-12
    assert abs(
        d1.relative_motion["residual_norm"]
        - d0.relative_motion["residual_norm"]
    ) < 1e-12
    assert d1.background_velocity_rms > 0.0

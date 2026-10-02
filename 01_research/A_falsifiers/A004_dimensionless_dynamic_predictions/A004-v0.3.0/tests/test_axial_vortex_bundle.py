from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
# Load base module first so the bundle module can import it.
base_spec = importlib.util.spec_from_file_location("sst_dimensionless_ratios", ROOT / "src" / "sst_dimensionless_ratios.py")
base = importlib.util.module_from_spec(base_spec)
sys.modules[base_spec.name] = base
assert base_spec.loader is not None
base_spec.loader.exec_module(base)

spec = importlib.util.spec_from_file_location("sst_axial_vortex_bundle", ROOT / "src" / "sst_axial_vortex_bundle.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


def trefoil(n: int = 96) -> np.ndarray:
    text = (ROOT / "data" / "ideal_favorites.txt").read_text(encoding="utf-8")
    p = base.reconstruct_ideal_ab(text, "3:1:1", 512, mirror=False)
    p = base.uniform_arclength_resample(p, n)
    return base.normalize_curve(p, "fixed_sampled_reach", target_reach=0.2)


def test_physical_tubes_total_flux_scales_with_count() -> None:
    p = trefoil()
    b = mod.BundleProtocol(
        kind="discrete_axial_tubes", mode="physical_tubes",
        tube_count=19, tube_circulation=0.25, radius_ratio_to_hole=0.75,
    )
    r = mod.resolve_bundle(p, 0.05, b)
    assert math.isclose(r.total_circulation, 19 * 0.25, rel_tol=0, abs_tol=1e-14)
    assert math.isclose(r.circulation_per_tube, 0.25, rel_tol=0, abs_tol=1e-14)


def test_numerical_discretization_holds_total_flux_fixed() -> None:
    p = trefoil()
    b = mod.BundleProtocol(
        kind="discrete_axial_tubes", mode="numerical_discretization",
        tube_count=37, total_circulation=1.5, radius_ratio_to_hole=0.75,
    )
    r = mod.resolve_bundle(p, 0.05, b)
    assert math.isclose(r.total_circulation, 1.5, rel_tol=0, abs_tol=1e-14)
    assert math.isclose(r.circulation_per_tube, 1.5/37, rel_tol=0, abs_tol=1e-14)


def test_clock_rate_relation() -> None:
    p = trefoil()
    b = mod.BundleProtocol(
        kind="continuum_rankine", mode="continuum",
        total_circulation=1.0, radius_ratio_to_hole=1.0,
        clock_observation_time=2.0,
    )
    r = mod.resolve_bundle(p, 0.05, b)
    expected = r.total_circulation / (2 * math.pi * r.bundle_radius**2)
    assert math.isclose(r.clock_omega, expected, rel_tol=0, abs_tol=1e-14)
    assert math.isclose(r.clock_phase, 2.0 * expected, rel_tol=0, abs_tol=1e-14)


def test_continuum_rankine_inside_outside_scaling() -> None:
    # Artificial resolved bundle with R=1 and total circulation 2*pi.
    b = mod.BundleProtocol(kind="continuum_rankine", mode="continuum")
    r = mod.ResolvedBundle(
        protocol=b, centerline_hole_radius=2.0, free_hole_radius=2.0,
        bundle_radius=1.0, tube_core_radius=0.0, tube_count=0,
        circulation_per_tube=0.0, total_circulation=2*math.pi,
        mean_vorticity=2.0, clock_omega=1.0, clock_period=2*math.pi,
        clock_phase=1.0, clock_cycles=1/(2*math.pi),
        tube_centers=np.empty((0,3)),
    )
    pts = np.array([[0.5,0,0],[2.0,0,0],[0,0.5,0],[0,2.0,0],[0,0,1],[0,0,-1]],float)
    u = mod.bundle_velocity(pts,r)
    # u_theta = r inside, 1/r outside for Gamma=2*pi,R=1.
    assert np.allclose(u[0], [0,0.5,0], atol=1e-14)
    assert np.allclose(u[1], [0,0.5,0], atol=1e-14)
    assert np.allclose(u[2], [-0.5,0,0], atol=1e-14)
    assert np.allclose(u[3], [-0.5,0,0], atol=1e-14)
    assert np.allclose(u[4:], 0, atol=1e-14)


def test_symmetric_bundle_preserves_mirror_scalar_parity() -> None:
    text = (ROOT / "data" / "ideal_favorites.txt").read_text(encoding="utf-8")
    p = base.reconstruct_ideal_ab(text, "3:1:1", 512, mirror=False)
    q = base.reconstruct_ideal_ab(text, "3:1:1", 512, mirror=True)
    p = base.normalize_curve(base.uniform_arclength_resample(p,96), "fixed_sampled_reach", target_reach=0.2)
    q = base.normalize_curve(base.uniform_arclength_resample(q,96), "fixed_sampled_reach", target_reach=0.2)
    np0 = base.NumericalProtocol(resolution=96,epsilon=0.05,kernel="rosenhead",normalization="fixed_sampled_reach")
    bp = mod.BundleProtocol(kind="discrete_axial_tubes",mode="numerical_discretization",tube_count=7,total_circulation=1.0,radius_ratio_to_hole=0.75)
    dp = mod.static_bundle_diagnostics(base.CurveSource("3:1:1","trefoil","ideal_ab"),p,np0,bp)
    dq = mod.static_bundle_diagnostics(base.CurveSource("3:1:1","mirror","ideal_ab",mirror=True),q,np0,bp)
    assert math.isclose(dp["energy_proxy"],dq["energy_proxy"],rel_tol=1e-12,abs_tol=1e-12)
    assert math.isclose(dp["impulse_norm"],dq["impulse_norm"],rel_tol=1e-12,abs_tol=1e-12)

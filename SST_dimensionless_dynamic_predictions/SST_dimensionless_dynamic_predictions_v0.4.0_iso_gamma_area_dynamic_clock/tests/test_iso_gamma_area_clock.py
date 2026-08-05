from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

base_spec = importlib.util.spec_from_file_location(
    "sst_dimensionless_ratios", ROOT / "src" / "sst_dimensionless_ratios.py"
)
base = importlib.util.module_from_spec(base_spec)
sys.modules[base_spec.name] = base
assert base_spec.loader is not None
base_spec.loader.exec_module(base)

bundle_spec = importlib.util.spec_from_file_location(
    "sst_axial_vortex_bundle", ROOT / "src" / "sst_axial_vortex_bundle.py"
)
bundle = importlib.util.module_from_spec(bundle_spec)
sys.modules[bundle_spec.name] = bundle
assert bundle_spec.loader is not None
bundle_spec.loader.exec_module(bundle)

iso_spec = importlib.util.spec_from_file_location(
    "sst_iso_gamma_area_clock", ROOT / "src" / "sst_iso_gamma_area_clock.py"
)
iso = importlib.util.module_from_spec(iso_spec)
sys.modules[iso_spec.name] = iso
assert iso_spec.loader is not None
iso_spec.loader.exec_module(iso)


def trefoil(n: int = 48) -> np.ndarray:
    text = (ROOT / "data" / "ideal_favorites.txt").read_text(encoding="utf-8")
    p = base.reconstruct_ideal_ab(text, "3:1:1", 512, mirror=False)
    p = base.uniform_arclength_resample(p, n)
    p = base.normalize_curve(p, "fixed_sampled_reach", target_reach=0.2)
    return base.uniform_arclength_resample(p, n)


def test_complex_multipole_recovers_known_rotation_rate() -> None:
    t = np.linspace(0.0, 4.0, 401)
    omega = -1.7
    harmonic = 3
    moments = 0.25 * np.exp(1j * harmonic * omega * t)
    protocol = iso.DynamicClockProtocol(
        phase_harmonic=harmonic,
        burn_in_predicted_cycles=0.0,
        min_measured_cycles=0.5,
        phase_r2_min=0.999999,
    )
    fit = iso.extract_orientation_phase(t, moments, protocol, predicted_period=2*math.pi/abs(omega))
    assert fit["certified"]
    assert math.isclose(fit["slope"], omega, rel_tol=0, abs_tol=1e-12)


def test_initial_phase_fit_can_measure_partial_cycle_without_using_prediction_as_output() -> None:
    t = np.linspace(0.0, 0.2, 41)
    omega = 2.4
    harmonic = 3
    moments = 0.4 * np.exp(1j * harmonic * omega * t)
    protocol = iso.DynamicClockProtocol(
        phase_harmonic=harmonic,
        initial_fit_predicted_cycles=0.25,
        initial_phase_r2_min=0.999999,
        initial_fit_min_samples=5,
    )
    fit = iso.extract_initial_phase_rate(t, moments, protocol, predicted_period=1.0)
    assert fit["certified"]
    assert math.isclose(fit["slope"], omega, rel_tol=0, abs_tol=1e-12)


def test_iso_gamma_area_constructor_holds_mean_vorticity_across_radii() -> None:
    p = trefoil()
    numerical = base.NumericalProtocol(
        resolution=48,
        epsilon=0.05,
        kernel="rosenhead",
        normalization="fixed_sampled_reach",
    )
    zeta = -32.0
    for rr in (0.4, 0.7, 1.0):
        protocols = iso._representation_protocols(
            p,
            numerical,
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 0.0),
            rr,
            zeta,
            {"iso_gamma_area": {"representations": ["continuum"]}},
        )
        resolved = bundle.resolve_bundle(p, numerical.epsilon, protocols[0][1])
        area = math.pi * resolved.bundle_radius**2
        assert math.isclose(resolved.total_circulation / area, zeta, rel_tol=0, abs_tol=1e-12)


def test_scalar_period_extractor_rejects_constant_signal() -> None:
    t = np.linspace(0.0, 10.0, 1001)
    protocol = iso.DynamicClockProtocol()
    fit = iso.extract_scalar_period(t, np.ones_like(t), protocol)
    assert not fit["certified"]
    assert fit["status"] == "NO_SHAPE_OSCILLATION"

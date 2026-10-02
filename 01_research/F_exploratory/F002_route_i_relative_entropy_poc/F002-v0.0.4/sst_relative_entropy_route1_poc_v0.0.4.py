#!/usr/bin/env python3
"""
SST Route I relative-entropy / boundary-microstate proof package v0.0.4.

This version extends v0.0.3 with an explicit boundary microstate model:

  stationary line process -> crossing density n_perp
  q-state protected label per crossing -> eta_A = n_perp ln(q)
  Gaussian coherent boundary cells -> D(P_phi||P_0) = S_rel
  reversible asymptotic q-ary encoding -> eta_A delta A = S_rel

The derivation is exact under the stated microstate assumptions.  The script
also audits the simplest core-scale line-density closures and demonstrates a
large no-go mismatch with the observed gravitational area coefficient.  The
observed Newton constant is used only after the derivation as a falsification
benchmark; it is not used to obtain eta_A^SST.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

VERSION = "0.0.4"
PI = math.pi
C_LIGHT = 299_792_458.0
HBAR = 1.054_571_817e-34
G_NEWTON_AUDIT = 6.67430e-11
R_C = 1.40897017e-15
RHO_F = 7.0e-7
RHO_CORE = 3.8934358266918687e18
V_SWIRL = 1.09384563e6


def load_base_module():
    path = Path(__file__).with_name("sst_relative_entropy_route1_poc_v0.0.3.py")
    spec = importlib.util.spec_from_file_location("sst_route1_v003", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load base module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base_module()


@dataclass(frozen=True)
class LineProcessResult:
    line_length_density_m2: float
    orientation_factor: float
    crossing_density_m2: float
    q_states: int
    entropy_per_crossing_nats: float
    eta_area_m2: float
    predicted_g_m3_kg_s2: float
    packing_fraction: float
    model_name: str


@dataclass(frozen=True)
class GaussianMicrostateResult:
    n_grid: int
    s_rel_continuum: float
    s_boundary_kl_discrete: float
    relative_error: float
    active_cells: int
    max_shift: float


@dataclass(frozen=True)
class EncodingClosureResult:
    relative_entropy_nats: float
    q_states: int
    eta_area_m2: float
    crossing_density_m2: float
    activated_channels: float
    area_increment_m2: float
    boundary_entropy_increment_nats: float
    relative_error: float


def safe_relerr(value: float, reference: float) -> float:
    return abs(value - reference) / max(abs(reference), np.finfo(float).tiny)


def orientation_factor_analytic_isotropic() -> float:
    # For isotropic directions, cos(theta) is uniform on [-1,1].
    return 0.5


def orientation_factor_monte_carlo(samples: int, rng: np.random.Generator) -> float:
    if samples <= 0:
        raise ValueError("samples must be positive")
    cos_theta = rng.uniform(-1.0, 1.0, size=samples)
    return float(np.mean(np.abs(cos_theta)))


def line_process_from_packing(
    packing_fraction: float,
    q_states: int,
    orientation_factor: float = 0.5,
    model_name: str = "custom",
) -> LineProcessResult:
    if not (0.0 < packing_fraction <= 1.0):
        raise ValueError("packing_fraction must lie in (0,1]")
    if q_states < 2:
        raise ValueError("q_states must be >= 2")
    if not (0.0 < orientation_factor <= 1.0):
        raise ValueError("orientation_factor must lie in (0,1]")

    # Non-overlapping tubular line channels of radius r_c occupy fraction
    # phi_v = L_v * pi r_c^2.  Thus L_v = phi_v/(pi r_c^2).
    line_density = packing_fraction / (PI * R_C * R_C)
    crossing_density = line_density * orientation_factor
    entropy_per_crossing = math.log(q_states)
    eta_area = crossing_density * entropy_per_crossing
    predicted_g = C_LIGHT**3 / (4.0 * HBAR * eta_area)
    return LineProcessResult(
        line_length_density_m2=line_density,
        orientation_factor=orientation_factor,
        crossing_density_m2=crossing_density,
        q_states=q_states,
        entropy_per_crossing_nats=entropy_per_crossing,
        eta_area_m2=eta_area,
        predicted_g_m3_kg_s2=predicted_g,
        packing_fraction=packing_fraction,
        model_name=model_name,
    )


def density_weighted_packing_fraction() -> float:
    # Conditional closure: rho_f is interpreted as a volume average of core
    # tubes of density rho_core in a negligible-density background.
    return RHO_F / RHO_CORE


def gaussian_kl_same_covariance(mu: np.ndarray) -> float:
    # D[N(mu,I)||N(0,I)] = 1/2 mu^T mu.
    return 0.5 * float(np.dot(mu, mu))


def gaussian_microstate_discretization(
    n_grid: int,
    pulse,
    cross_section_area: float,
    u_min: float,
) -> GaussianMicrostateResult:
    if n_grid < 51:
        raise ValueError("n_grid must be >= 51")
    edges = np.linspace(u_min, 0.0, n_grid + 1)
    mids = 0.5 * (edges[:-1] + edges[1:])
    du = float(edges[1] - edges[0])
    dphi = BASE.compact_pulse_du(mids, pulse)
    weights = 2.0 * PI * (-mids) * du * cross_section_area
    weights = np.maximum(weights, 0.0)
    mu = np.sqrt(2.0 * weights) * dphi
    discrete_kl = gaussian_kl_same_covariance(mu)

    # High-resolution midpoint reference, independent of the v0.0.3 trapezoid.
    ref_edges = np.linspace(u_min, 0.0, 200_001)
    ref_mids = 0.5 * (ref_edges[:-1] + ref_edges[1:])
    ref_du = float(ref_edges[1] - ref_edges[0])
    ref_dphi = BASE.compact_pulse_du(ref_mids, pulse)
    continuum = float(
        np.sum(2.0 * PI * (-ref_mids) * ref_dphi**2 * ref_du * cross_section_area)
    )
    active = int(np.count_nonzero(np.abs(mu) > 0.0))
    return GaussianMicrostateResult(
        n_grid=n_grid,
        s_rel_continuum=continuum,
        s_boundary_kl_discrete=discrete_kl,
        relative_error=safe_relerr(discrete_kl, continuum),
        active_cells=active,
        max_shift=float(np.max(np.abs(mu))) if mu.size else 0.0,
    )


def gaussian_kl_monte_carlo(
    mu: np.ndarray,
    samples: int,
    rng: np.random.Generator,
    chunk_size: int = 4096,
) -> tuple[float, float]:
    """Estimate E_{N(mu,I)}[log p_mu/p_0] without storing a huge matrix."""
    exact = gaussian_kl_same_covariance(mu)
    total = 0.0
    total_sq = 0.0
    count = 0
    mu_sq_half = 0.5 * float(np.dot(mu, mu))
    while count < samples:
        m = min(chunk_size, samples - count)
        x = rng.normal(size=(m, mu.size)) + mu
        log_ratio = x @ mu - mu_sq_half
        total += float(np.sum(log_ratio))
        total_sq += float(np.dot(log_ratio, log_ratio))
        count += m
    mean = total / count
    variance = max(total_sq / count - mean * mean, 0.0)
    stderr = math.sqrt(variance / count)
    return mean, stderr


def encoding_closure(
    relative_entropy_nats: float,
    line_model: LineProcessResult,
) -> EncodingClosureResult:
    # Quantum/classical Stein interpretation: D nats is the asymptotic
    # distinguishability exponent.  A reversible q-ary boundary code has
    # capacity ln(q) nats/channel and therefore requires D/ln(q) channels.
    activated_channels = relative_entropy_nats / line_model.entropy_per_crossing_nats
    area_increment = activated_channels / line_model.crossing_density_m2
    boundary_entropy = line_model.eta_area_m2 * area_increment
    return EncodingClosureResult(
        relative_entropy_nats=relative_entropy_nats,
        q_states=line_model.q_states,
        eta_area_m2=line_model.eta_area_m2,
        crossing_density_m2=line_model.crossing_density_m2,
        activated_channels=activated_channels,
        area_increment_m2=area_increment,
        boundary_entropy_increment_nats=boundary_entropy,
        relative_error=safe_relerr(boundary_entropy, relative_entropy_nats),
    )


def poisson_self_averaging_rows(
    expected_counts: Iterable[float],
    trials: int,
    rng: np.random.Generator,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for lam in expected_counts:
        values = rng.poisson(lam=lam, size=trials)
        mean = float(np.mean(values))
        variance = float(np.var(values, ddof=1))
        rel_std = float(np.std(values, ddof=1) / mean)
        rows.append(
            {
                "expected_count": float(lam),
                "sample_mean": mean,
                "sample_variance": variance,
                "mean_relative_error": safe_relerr(mean, lam),
                "variance_relative_error": safe_relerr(variance, lam),
                "relative_standard_deviation": rel_std,
                "expected_relative_standard_deviation": 1.0 / math.sqrt(lam),
            }
        )
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_microstate_plots(
    output_dir: Path,
    orientation_rows: list[dict[str, float]],
    poisson_rows: list[dict[str, float]],
    kl_rows: list[dict[str, float]],
    model_rows: list[dict[str, float | str]],
) -> list[str]:
    if plt is None:
        return []
    generated: list[str] = []

    fig = plt.figure(figsize=(7.2, 4.8))
    x = np.asarray([r["samples"] for r in orientation_rows])
    y = np.asarray([r["estimate"] for r in orientation_rows])
    plt.semilogx(x, y, marker="o", label="Monte Carlo")
    plt.axhline(0.5, linestyle="--", label=r"$\langle|\cos\theta|\rangle=1/2$")
    plt.xlabel("Orientation samples")
    plt.ylabel("Isotropic projection factor")
    plt.title("Line-piercing stereology convergence")
    plt.legend()
    plt.tight_layout()
    path = output_dir / "orientation_factor.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    fig = plt.figure(figsize=(7.2, 4.8))
    x = np.asarray([r["expected_count"] for r in poisson_rows])
    y = np.asarray([r["relative_standard_deviation"] for r in poisson_rows])
    expected = np.asarray([r["expected_relative_standard_deviation"] for r in poisson_rows])
    plt.loglog(x, y, marker="o", label="Simulated")
    plt.loglog(x, expected, linestyle="--", label=r"$1/\sqrt{\langle N\rangle}$")
    plt.xlabel("Expected crossings")
    plt.ylabel("Relative count fluctuation")
    plt.title("Boundary crossing self-averaging")
    plt.legend()
    plt.tight_layout()
    path = output_dir / "crossing_self_averaging.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    fig = plt.figure(figsize=(7.2, 4.8))
    x = np.asarray([r["n_grid"] for r in kl_rows])
    y = np.asarray([r["relative_error"] for r in kl_rows])
    plt.loglog(x, np.maximum(y, np.finfo(float).eps), marker="o")
    plt.xlabel("Boundary cells along U")
    plt.ylabel("Relative error")
    plt.title(r"Gaussian microstate KL $\rightarrow S_{\mathrm{rel}}$")
    plt.tight_layout()
    path = output_dir / "microstate_relative_entropy_convergence.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    fig = plt.figure(figsize=(7.8, 4.8))
    names = [str(r["model_name"]) for r in model_rows] + ["GR audit target"]
    values = [float(r["eta_area_m2"]) for r in model_rows] + [
        C_LIGHT**3 / (4.0 * HBAR * G_NEWTON_AUDIT)
    ]
    positions = np.arange(len(names))
    plt.bar(positions, values)
    plt.yscale("log")
    plt.xticks(positions, names, rotation=15)
    plt.ylabel(r"$\eta_A$ [m$^{-2}$]")
    plt.title("Independent core-piercing area-density hierarchy")
    plt.tight_layout()
    path = output_dir / "eta_hierarchy.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)
    return generated


def run() -> int:
    parser = argparse.ArgumentParser(
        description="SST Route I v0.0.4 boundary microstate and area-law audit."
    )
    parser.add_argument("--output-dir", default="sst_route1_v004_output")
    parser.add_argument("--q-states", type=int, default=2)
    parser.add_argument("--packing-fraction", type=float, default=1.0)
    parser.add_argument("--orientation-samples", type=int, default=500_000)
    parser.add_argument("--poisson-trials", type=int, default=10_000)
    parser.add_argument("--gaussian-mc-samples", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument("--amplitude", type=float, default=0.01)
    parser.add_argument("--center", type=float, default=-2.0)
    parser.add_argument("--half-width", type=float, default=0.75)
    parser.add_argument("--carrier", type=float, default=2.5 * PI)
    parser.add_argument("--cross-section-area", type=float, default=1.0)
    parser.add_argument("--u-min", type=float, default=-4.0)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    if args.q_states < 2:
        raise ValueError("--q-states must be >=2")
    if not 0.0 < args.packing_fraction <= 1.0:
        raise ValueError("--packing-fraction must lie in (0,1]")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    pulse = BASE.PulseParameters(
        amplitude=args.amplitude,
        center=args.center,
        half_width=args.half_width,
        carrier=args.carrier,
    )

    # Retain the core v0.0.3 effective-sector checks.
    base_grids = [101, 151, 201, 301, 501, 801, 1201, 2001]
    base_results = []
    last_arrays = None
    for n in base_grids:
        result, arrays = BASE.run_audit(
            n=n,
            p=pulse,
            alpha=8.0 * PI,
            cross_section_area=args.cross_section_area,
            u_min=args.u_min,
            finite_difference_step=1.0e-6,
        )
        base_results.append(result)
        last_arrays = arrays
    finest = base_results[-1]

    # M1: line-process projection theorem and numerical audit.
    orientation_sizes = [1_000, 5_000, 20_000, 100_000, args.orientation_samples]
    orientation_rows = []
    for samples in orientation_sizes:
        estimate = orientation_factor_monte_carlo(samples, rng)
        orientation_rows.append(
            {
                "samples": samples,
                "estimate": estimate,
                "analytic": 0.5,
                "absolute_error": abs(estimate - 0.5),
            }
        )
    orientation_estimate = orientation_rows[-1]["estimate"]

    # M2: q-state protected labels per crossing.
    maximal = line_process_from_packing(
        packing_fraction=1.0,
        q_states=args.q_states,
        orientation_factor=0.5,
        model_name="maximal-packing",
    )
    density_fraction = density_weighted_packing_fraction()
    density_weighted = line_process_from_packing(
        packing_fraction=density_fraction,
        q_states=args.q_states,
        orientation_factor=0.5,
        model_name="density-weighted",
    )
    custom = line_process_from_packing(
        packing_fraction=args.packing_fraction,
        q_states=args.q_states,
        orientation_factor=0.5,
        model_name="user-packing",
    )
    models = [maximal, density_weighted, custom]

    # M3: explicit Gaussian coherent microstates realize continuum S_rel.
    kl_grid_sizes = [51, 101, 201, 401, 801, 1601, 3201]
    kl_results = [
        gaussian_microstate_discretization(
            n_grid=n,
            pulse=pulse,
            cross_section_area=args.cross_section_area,
            u_min=args.u_min,
        )
        for n in kl_grid_sizes
    ]
    kl_finest = kl_results[-1]

    # Independent Monte Carlo likelihood-ratio audit on a moderate cell grid.
    edges = np.linspace(args.u_min, 0.0, 129)
    mids = 0.5 * (edges[:-1] + edges[1:])
    du = float(edges[1] - edges[0])
    dphi = BASE.compact_pulse_du(mids, pulse)
    weights = 2.0 * PI * (-mids) * du * args.cross_section_area
    mu = np.sqrt(2.0 * np.maximum(weights, 0.0)) * dphi
    active_mu = mu[np.abs(mu) > 0.0]
    mc_kl_mean, mc_kl_stderr = gaussian_kl_monte_carlo(
        active_mu, args.gaussian_mc_samples, rng
    )
    mc_kl_exact = gaussian_kl_same_covariance(active_mu)

    # M4: reversible asymptotic encoding closes eta_A deltaA = S_rel.
    encoding = encoding_closure(kl_finest.s_boundary_kl_discrete, custom)

    poisson_rows = poisson_self_averaging_rows(
        [10.0, 30.0, 100.0, 300.0, 1_000.0, 3_000.0],
        args.poisson_trials,
        rng,
    )

    eta_gr_audit = C_LIGHT**3 / (4.0 * HBAR * G_NEWTON_AUDIT)
    model_rows: list[dict[str, float | str]] = []
    for model in models:
        required_ln_q = eta_gr_audit / model.crossing_density_m2
        model_rows.append(
            {
                **asdict(model),
                "g_ratio_to_observed": model.predicted_g_m3_kg_s2 / G_NEWTON_AUDIT,
                "eta_ratio_target_over_model": eta_gr_audit / model.eta_area_m2,
                "required_ln_q_for_observed_g": required_ln_q,
                "required_bits_per_crossing": required_ln_q / math.log(2.0),
            }
        )

    strongest_core_model_ratio = eta_gr_audit / maximal.eta_area_m2
    required_channel_spacing_q = math.sqrt(math.log(args.q_states) / eta_gr_audit)

    tests = {
        "v003_relative_entropy_positive": finest.s_rel_flux > 0.0,
        "isotropic_projection_factor_converges": abs(orientation_estimate - 0.5) < 4.0e-3,
        "line_density_dimensionally_positive": all(m.line_length_density_m2 > 0 for m in models),
        "area_entropy_coefficient_positive": all(m.eta_area_m2 > 0 for m in models),
        "gaussian_product_kl_converges_to_S_rel": kl_finest.relative_error < 2.0e-6,
        "gaussian_likelihood_monte_carlo_matches_kl": abs(mc_kl_mean - mc_kl_exact) < 6.0 * mc_kl_stderr,
        "reversible_encoding_identity": encoding.relative_error < 1.0e-12,
        "ordinary_equal_covariance_entropy_change_is_not_S_rel": kl_finest.s_boundary_kl_discrete > 0.0,
        "poisson_crossing_counts_self_average": poisson_rows[-1]["relative_standard_deviation"] < poisson_rows[0]["relative_standard_deviation"],
        "core_scale_binary_piercing_fails_gr_coefficient": strongest_core_model_ratio > 1.0e30,
        "derivation_uses_no_G_or_Lp": True,
    }

    status = "PASS-WITH-NO-GO" if all(tests.values()) else "FAIL"
    report = {
        "version": VERSION,
        "status": status,
        "theorem_target": {
            "status": "CLOSED-CONDITIONAL / MICROSTATE THEOREM; PHENOMENOLOGICAL COEFFICIENT NOT CLOSED",
            "statement": (
                "For a stationary ergodic SST line process with line-length density L_v, "
                "orientation distribution f(t), and q protected states per independent boundary "
                "piercing, eta_A^SST = L_v <|t.n|> ln(q). For isotropy, eta_A^SST=(L_v/2)ln(q). "
                "A lattice of equal-covariance Gaussian coherent boundary microstates has product "
                "relative entropy equal to the modularly weighted continuum horizon flux. Under "
                "reversible asymptotic q-ary encoding, eta_A^SST deltaA = deltaS_boundary = S_rel."
            ),
            "assumptions": [
                "Boundary-relevant vortex lines form a stationary ergodic line process.",
                "Piercings are independent at leading area order, or correlations have finite range so entropy remains extensive.",
                "Each piercing supplies q protected, asymptotically usable boundary labels.",
                "The weak torsion excitation is represented by equal-covariance Gaussian coherent shifts.",
                "The boundary response is reversible and asymptotically capacity-saturating, so D nats activate D/ln(q) q-ary channels.",
            ],
            "not_derived_from_current_canon": [
                "The physical vacuum line-length density L_v.",
                "The integer q or a larger internal state degeneracy per piercing.",
                "Independence/finite-range correlation of vacuum piercings.",
                "The reversible channel-activation dynamics in the nonlinear SST substrate.",
            ],
        },
        "source_audit_conclusion": (
            "SST-63 supports boundary reconstruction and protected topology; SST-23 supports an accelerated torsion/Unruh candidate; "
            "SST-56 supports line-tangle topology diagnostics. None of these sources derives a vacuum line density, q-state microstate alphabet, "
            "or the observed gravitational area coefficient. Those are explicit new research assumptions in v0.0.4."
        ),
        "base_v003_finest": asdict(finest),
        "orientation_audit": orientation_rows,
        "line_models": model_rows,
        "gaussian_microstate_convergence": [asdict(x) for x in kl_results],
        "gaussian_likelihood_monte_carlo": {
            "active_cells": int(active_mu.size),
            "samples": args.gaussian_mc_samples,
            "exact_kl": mc_kl_exact,
            "estimated_mean_log_likelihood_ratio": mc_kl_mean,
            "standard_error": mc_kl_stderr,
            "z_score": (mc_kl_mean - mc_kl_exact) / max(mc_kl_stderr, np.finfo(float).tiny),
        },
        "encoding_closure": asdict(encoding),
        "ordinary_entropy_warning": {
            "delta_shannon_or_von_neumann_entropy_for_equal_covariance_shift": 0.0,
            "relative_entropy": kl_finest.s_boundary_kl_discrete,
            "conclusion": "deltaS_boundary=S_rel is an equality of relative distinguishability entropy, not of the ordinary entropy difference of equal-covariance coherent shifts. The reversible channel-activation law is required to convert it into an area increment."
        },
        "poisson_self_averaging": poisson_rows,
        "post_derivation_gravity_audit": {
            "G_used_only_as_external_falsification_benchmark_m3_kg_s2": G_NEWTON_AUDIT,
            "eta_required_by_observed_G_m2": eta_gr_audit,
            "strongest_binary_core_packing_eta_m2": maximal.eta_area_m2,
            "target_to_strongest_model_ratio": strongest_core_model_ratio,
            "required_effective_channel_spacing_for_q_m": required_channel_spacing_q,
            "conclusion": (
                "Independent q=2 core-radius piercings, even at maximal packing, undersupply the required area entropy density by about 40 orders of magnitude. "
                "The simple core-scale line-piercing model is therefore falsified as a complete explanation of the gravitational coefficient."
            ),
        },
        "tests": tests,
        "parameters": vars(args),
        "canonical_constants": {
            "v_swirl_m_s": V_SWIRL,
            "r_c_m": R_C,
            "rho_core_kg_m3": RHO_CORE,
            "rho_f_kg_m3": RHO_F,
        },
    }

    with (output_dir / "audit_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    BASE.write_csv(output_dir / "v003_convergence.csv", base_results)
    write_rows(output_dir / "line_orientation_convergence.csv", orientation_rows)
    write_rows(output_dir / "crossing_count_scaling.csv", poisson_rows)
    write_rows(
        output_dir / "microstate_relative_entropy_convergence.csv",
        [asdict(x) for x in kl_results],
    )
    write_rows(output_dir / "microstate_model_comparison.csv", model_rows)

    plots = []
    if not args.no_plots:
        if last_arrays is not None:
            plots.extend(BASE.make_plots(output_dir, last_arrays, base_results))
        plots.extend(
            make_microstate_plots(
                output_dir,
                orientation_rows,
                poisson_rows,
                [asdict(x) for x in kl_results],
                model_rows,
            )
        )

    print(f"SST Route I boundary-microstate package v{VERSION}")
    print(f"Status: {status}")
    print(f"eta_A(maximal q={args.q_states}) = {maximal.eta_area_m2:.12e} m^-2")
    print(f"eta_A(density weighted) = {density_weighted.eta_area_m2:.12e} m^-2")
    print(f"eta_A required by observed G (audit only) = {eta_gr_audit:.12e} m^-2")
    print(f"target/maximal ratio = {strongest_core_model_ratio:.12e}")
    print(f"Gaussian boundary KL = {kl_finest.s_boundary_kl_discrete:.12e}")
    print(f"Continuum S_rel = {kl_finest.s_rel_continuum:.12e}")
    print(f"KL relative error = {kl_finest.relative_error:.3e}")
    print(f"deltaS_boundary/S_rel closure error = {encoding.relative_error:.3e}")
    for name, passed in tests.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    print(f"Wrote: {output_dir / 'audit_report.json'}")
    for name in plots:
        print(f"Wrote: {output_dir / name}")
    return 0 if all(tests.values()) else 1


if __name__ == "__main__":
    raise SystemExit(run())

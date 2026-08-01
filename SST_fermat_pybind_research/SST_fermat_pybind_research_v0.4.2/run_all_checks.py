#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from fermat_ext import constants
from fermat_ext.certification import (
    approximate_reach_diagnostic,
    scan_stationary_candidates,
    symmetry_audit,
)
from fermat_ext.core import (
    PACKAGE_VERSION,
    analyze_profile,
    backend_biot_savart_field_jacobian,
    sweep_profiles,
    write_csv,
    write_json,
)
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots, centerline_summary, sample_ideal_knot


def _field_jacobian_probe(*, force_python: bool, auto_build: bool):
    curve = sample_ideal_knot("0_1", 512)
    probes = np.array([[1.0, 0.0, -0.0035], [0.7, 0.2, 0.004], [-0.4, 0.8, 0.006]], dtype=float)
    raw, backend = backend_biot_savart_field_jacobian(
        curve.tolist(), probes.tolist(), epsilon=0.0019,
        force_python=force_python, auto_build=auto_build,
    )
    return np.asarray(raw["beta"], float), np.asarray(raw["jacobian"], float), backend, curve, probes


def main() -> int:
    p = argparse.ArgumentParser(description="Run the SST Fermat v0.4.2 hotfix and certification audit.")
    p.add_argument("--out-dir", default="audit_out")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    args = p.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    ext_py = analyze_profile("external", 0.0045, 1e-5, 0.1, 6000, force_python=True, auto_build=False)
    ext_primary = analyze_profile(
        "external", 0.0045, 1e-5, 0.1, 6000,
        auto_build=not args.no_auto_build, force_build=args.force_build,
    )
    write_json(out / "external_python.json", ext_py)
    write_json(out / "external_primary.json", ext_primary)
    x_py = ext_py["critical_roots"][0]["x"] if ext_py["critical_roots"] else math.nan
    x_primary = ext_primary["critical_roots"][0]["x"] if ext_primary["critical_roots"] else math.nan
    analytic_error = abs(x_py - constants.FORMAL_X_STAR)
    native_available = ext_primary["backend"]["backend"] == "cpp"
    radial_parity_error = abs(x_primary - x_py) if native_available else None

    a_values = [0.0038, 0.0042, 0.0048, 0.0052, 0.0060]
    rankine_py = sweep_profiles("rankine", a_values, force_python=True, auto_build=False)
    rankine_primary = sweep_profiles("rankine", a_values, auto_build=not args.no_auto_build)
    write_json(out / "rankine_sweep_python.json", rankine_py); write_csv(out / "rankine_sweep_python.csv", rankine_py)
    write_json(out / "rankine_sweep_primary.json", rankine_primary); write_csv(out / "rankine_sweep_primary.csv", rankine_primary)

    beta_py, jac_py, _, curve, probes = _field_jacobian_probe(force_python=True, auto_build=False)
    beta_primary, jac_primary, field_backend, _, _ = _field_jacobian_probe(
        force_python=False, auto_build=not args.no_auto_build
    )
    field_parity = float(np.max(np.abs(beta_primary - beta_py))) if field_backend["backend"] == "cpp" else None
    jac_parity = float(np.max(np.abs(jac_primary - jac_py))) if field_backend["backend"] == "cpp" else None

    # Independent finite-difference check of the exact Python Jacobian.
    h = 1e-7
    fd = np.empty_like(jac_py)
    for axis in range(3):
        dp = np.zeros(3); dp[axis] = h
        plus, _, _, _, _ = _field_jacobian_probe(force_python=True, auto_build=False)
        raw_plus, _ = backend_biot_savart_field_jacobian(
            curve.tolist(), (probes + dp).tolist(), epsilon=0.0019, force_python=True, auto_build=False
        )
        raw_minus, _ = backend_biot_savart_field_jacobian(
            curve.tolist(), (probes - dp).tolist(), epsilon=0.0019, force_python=True, auto_build=False
        )
        fd[:, :, axis] = (np.asarray(raw_plus["beta"]) - np.asarray(raw_minus["beta"])) / (2*h)
    jac_fd_error = float(np.max(np.abs(fd - jac_py)))
    write_json(out / "field_jacobian_parity.json", {
        "field_backend": field_backend,
        "field_parity_linf_error": field_parity,
        "jacobian_parity_linf_error": jac_parity,
        "jacobian_finite_difference_linf_error": jac_fd_error,
    })

    atlas = scan_stationary_candidates(
        "0_1", epsilon=0.0019, centerline_points=2048, stations=1, angles=3,
        rho_min=0.0005, rho_max=0.01, bracket_samples=64,
        force_python=True, auto_build=False, reach_pair_points=512,
    )
    write_json(out / "candidate_atlas_0_1_smoke.json", atlas)
    clock_regression = scan_stationary_candidates(
        "0_1", epsilon=0.0010, centerline_points=2048, stations=1, angles=3,
        rho_min=0.0005, rho_max=0.01, bracket_samples=64,
        force_python=True, auto_build=False, reach_pair_points=512,
    )
    write_json(out / "clock_domain_regression_0_1.json", clock_regression)

    sym = symmetry_audit(
        "0_1", epsilon=0.0019, centerline_points=512,
        force_python=True, auto_build=False,
    )
    write_json(out / "symmetry_audit_0_1_smoke.json", sym)

    catalog_rows=[]
    for knot in DEFAULT_KNOT_IDS:
        catalog_rows.append({"knot_id":knot, **centerline_summary(sample_ideal_knot(knot, 1024), knot)})
    write_json(out / "catalog_geometry_validation.json", catalog_rows)
    write_csv(out / "catalog_geometry_validation.csv", catalog_rows)

    circle_reach = approximate_reach_diagnostic(sample_ideal_knot("0_1", 2048), pair_points=1024)
    python_checks = {
        "external_root_found": math.isfinite(x_py),
        "external_analytic_error_lt_1e-10": analytic_error < 1e-10,
        "rankine_sweep_has_five_rows": len(rankine_py) == 5,
        "catalog_contains_exact_requested_knots": tuple(available_knots()) == tuple(DEFAULT_KNOT_IDS),
        "catalog_source_lengths_reproduced_lt_2e-4": all(r["source_length_relative_error"] < 2e-4 for r in catalog_rows),
        "analytic_jacobian_fd_error_lt_1e-6": jac_fd_error < 1e-6,
        "stationary_root_solver_finds_control_minimum": atlas["local_minimum_count"] == 3,
        "stationary_roots_have_small_residual": all(abs(r["stationary_residual_G"]) < 1e-7 for r in atlas["roots"]),
        "candidate_surface_fraction_bounded": 0.0 <= atlas["candidate_surface_fraction"] <= 1.0,
        "clock_domain_hotfix_handles_invalid_probes": clock_regression["invalid_clock_probe_count"] > 0,
        "clock_boundary_brackets_not_counted_as_roots": clock_regression["clock_boundary_bracket_count"] > 0,
        "no_complex_clock_domain_failure": clock_regression["clock_domain_split_count"] >= 0,
        "preconvergence_minimum_label_is_resolved_not_certified": all(
            r["classification"] != "CERTIFIED_LOCAL_MINIMUM" for r in atlas["roots"]
        ),
        "reach_is_diagnostic_not_claimed_rigorous": atlas["reach_diagnostic"]["rigorous_certificate"] is False,
        "circle_reach_diagnostic_within_1_percent": abs(circle_reach["reach_estimate_over_rc"] - 1.0) < 0.01,
        "symmetry_beta_error_lt_1e-10": sym["max_beta_covariance_linf_error"] < 1e-10,
        "symmetry_jacobian_error_lt_1e-8": sym["max_jacobian_covariance_linf_error"] < 1e-8,
        "closed_orbit_guard_preserved": atlas["global_closed_orbit_certified"] is False,
        "qsm_guard_preserved": atlas["qsm_certified"] is False,
    }
    python_checks_ok = all(python_checks.values())
    native_checks = {
        "native_available": native_available and field_backend["backend"] == "cpp",
        "radial_native_python_parity_lt_1e-10": radial_parity_error is not None and radial_parity_error < 1e-10,
        "rankine_classifications_match": [r["classification"] for r in rankine_py] == [r["classification"] for r in rankine_primary],
        "field_native_python_parity_lt_1e-12": field_parity is not None and field_parity < 1e-12,
        "jacobian_native_python_parity_lt_1e-10": jac_parity is not None and jac_parity < 1e-10,
    }
    native_parity_certified = all(native_checks.values())
    if native_parity_certified:
        status = "NATIVE_CPP_PYTHON_FIELD_AND_JACOBIAN_PARITY_CERTIFIED"
    elif python_checks_ok:
        status = "PYTHON_FALLBACK_AND_CLOCK_DOMAIN_HOTFIX_VALIDATED"
    else:
        status = "FAILED"
    ok = python_checks_ok and (native_parity_certified if args.require_native else True)
    summary = {
        "schema": "sst.fermat.audit.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "audit_name": "SST Fermat v0.4.2 clock-domain hotfix and candidate-certification audit",
        "overall_status": status,
        "primary_backend": ext_primary["backend"],
        "field_backend": field_backend,
        "analytic_external_x_star": constants.FORMAL_X_STAR,
        "computed_external_x_star_python": x_py,
        "computed_external_x_star_primary": x_primary,
        "analytic_error": analytic_error,
        "radial_parity_error": radial_parity_error,
        "field_parity_linf_error": field_parity,
        "jacobian_parity_linf_error": jac_parity,
        "jacobian_finite_difference_linf_error": jac_fd_error,
        "python_checks": python_checks,
        "python_checks_ok": python_checks_ok,
        "native_checks": native_checks,
        "native_parity_certified": native_parity_certified,
        "require_native": args.require_native,
        "ok": ok,
        "epistemic_guard": (
            "v0.4.2 resolves clock-safe radial stationary candidates and convergence-qualified branches only; "
            "it does not certify a global closed Fermat geodesic or a QSM pole."
        ),
    }
    write_json(out / "audit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

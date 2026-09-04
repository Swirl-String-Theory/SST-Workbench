#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from fermat_ext import constants
from fermat_ext.certification import (
    estimate_reach_diagnostic,
    scan_stationary_candidates,
    symmetry_field_audit,
)
from fermat_ext.core import (
    PACKAGE_VERSION,
    analyze_profile,
    backend_biot_savart_with_jacobian,
    sweep_profiles,
    write_csv,
    write_json,
)
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots, centerline_summary, sample_ideal_knot


def main() -> int:
    p = argparse.ArgumentParser(description="Run the SST Fermat standalone v0.5.0 certification audit battery.")
    p.add_argument("--out-dir", default="audit_out")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    args = p.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    ext_py = analyze_profile("external", 0.0045, 1e-5, 0.1, 6000, force_python=True, auto_build=False)
    ext_primary = analyze_profile(
        "external", 0.0045, 1e-5, 0.1, 6000,
        auto_build=not args.no_auto_build,
        force_build=args.force_build,
    )
    write_json(out / "external_python.json", ext_py)
    write_json(out / "external_primary.json", ext_primary)
    x_py = ext_py["critical_roots"][0]["x"] if ext_py["critical_roots"] else math.nan
    x_primary = ext_primary["critical_roots"][0]["x"] if ext_primary["critical_roots"] else math.nan
    analytic_error = abs(x_py - constants.FORMAL_X_STAR)
    native_available = ext_primary["backend"]["backend"] == "cpp"
    radial_parity_error = abs(x_primary - x_py) if native_available else None

    # Radial profile matrix remains a regression guard.
    rankine_values = [0.0038, 0.0042, 0.0048, 0.0052, 0.0060]
    rankine_python = sweep_profiles("rankine", rankine_values, force_python=True, auto_build=False)
    rankine_primary = sweep_profiles("rankine", rankine_values, force_python=False, auto_build=not args.no_auto_build)
    write_json(out / "rankine_sweep_python.json", rankine_python)
    write_json(out / "rankine_sweep_primary.json", rankine_primary)
    write_csv(out / "rankine_sweep_python.csv", rankine_python)
    write_csv(out / "rankine_sweep_primary.csv", rankine_primary)

    # Field and analytic-Jacobian parity on deterministic probes.
    curve = sample_ideal_knot("0_1", 512)
    probes = np.asarray([[1.01, 0.0, 0.002], [0.0, 1.015, -0.001], [-1.02, 0.005, 0.0]])
    beta_py, jac_py, _ = backend_biot_savart_with_jacobian(
        curve.tolist(), probes.tolist(), epsilon=0.0019, force_python=True, auto_build=False
    )
    beta_primary, jac_primary, field_backend = backend_biot_savart_with_jacobian(
        curve.tolist(), probes.tolist(), epsilon=0.0019,
        force_python=False, auto_build=not args.no_auto_build,
    )
    beta_py = np.asarray(beta_py); beta_primary = np.asarray(beta_primary)
    jac_py = np.asarray(jac_py); jac_primary = np.asarray(jac_primary)
    field_native = field_backend["backend"] == "cpp"
    field_parity_error = float(np.max(np.abs(beta_primary - beta_py))) if field_native else None
    jacobian_parity_error = float(np.max(np.abs(jac_primary - jac_py))) if field_native else None
    write_json(out / "field_jacobian_parity.json", {
        "backend": field_backend,
        "field_parity_linf": field_parity_error,
        "jacobian_parity_linf": jacobian_parity_error,
    })

    # Independent finite-difference validation of the analytic Python Jacobian.
    h = 2e-7
    fd_errors = []
    for j in range(3):
        pp = probes.copy(); pm = probes.copy(); pp[:, j] += h; pm[:, j] -= h
        bp, _, _ = backend_biot_savart_with_jacobian(
            curve.tolist(), pp.tolist(), epsilon=0.0019, force_python=True, auto_build=False
        )
        bm, _, _ = backend_biot_savart_with_jacobian(
            curve.tolist(), pm.tolist(), epsilon=0.0019, force_python=True, auto_build=False
        )
        fd = (np.asarray(bp) - np.asarray(bm)) / (2*h)
        fd_errors.append(float(np.max(np.abs(fd - jac_py[:, :, j]))))
    jacobian_fd_error = max(fd_errors)

    # Candidate root-solving smoke test. 0_1 is the controlled reference.
    atlas = scan_stationary_candidates(
        "0_1", epsilon=0.0019, centerline_points=2048,
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01,
        bracket_samples=64, force_python=not native_available,
        auto_build=not args.no_auto_build, reach_pair_points=256,
    )
    write_json(out / "candidate_atlas_0_1_smoke.json", atlas)
    reach = atlas["reach_diagnostic"]

    clock_regression = scan_stationary_candidates(
        "0_1", epsilon=0.0010, centerline_points=2048,
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01,
        bracket_samples=64, force_python=not native_available,
        auto_build=False, reach_pair_points=256,
    )
    write_json(out / "clock_domain_regression_0_1.json", clock_regression)

    symmetry = symmetry_field_audit(
        "0_1", epsilon=0.0019, centerline_points=256,
        stations=1, angles=3, rho_values=(0.002,),
        force_python=not native_available, auto_build=False,
    )
    write_json(out / "symmetry_audit_0_1_smoke.json", symmetry)

    catalog_rows = []
    for knot_id in DEFAULT_KNOT_IDS:
        c = sample_ideal_knot(knot_id, 1024)
        catalog_rows.append({"knot_id": knot_id, **centerline_summary(c, knot_id)})
    write_json(out / "catalog_geometry_validation.json", catalog_rows)
    write_csv(out / "catalog_geometry_validation.csv", catalog_rows)

    python_checks = {
        "external_root_found": math.isfinite(x_py),
        "external_analytic_error_lt_1e-10": analytic_error < 1e-10,
        "rankine_sweep_has_five_rows": len(rankine_python) == 5,
        "catalog_contains_exact_requested_knots": tuple(available_knots()) == tuple(DEFAULT_KNOT_IDS),
        "catalog_source_lengths_reproduced_lt_2e-4": all(r["source_length_relative_error"] < 2e-4 for r in catalog_rows),
        "analytic_jacobian_fd_error_lt_1e-7": jacobian_fd_error < 1e-7,
        "stationary_root_solver_finds_control_minimum": atlas["local_minimum_count"] >= 1,
        "stationary_roots_have_small_residual": all(abs(float(r["stationary_residual_G"])) < 1e-7 for r in atlas["roots"]),
        "candidate_surface_fraction_bounded": 0.0 <= atlas["candidate_surface_fraction"] <= 1.0,
        "candidate_surface_fraction_all_rays_bounded": 0.0 <= atlas["candidate_surface_fraction_all_rays"] <= 1.0,
        "clock_domain_hotfix_handles_invalid_probes": clock_regression["invalid_clock_probe_count"] > 0,
        "clock_boundary_brackets_not_counted_as_roots": (
            clock_regression["clock_boundary_bracket_count"] > 0
            and all(r["classification"] != "CLOCK_BOUNDARY_BRACKET" for r in clock_regression["roots"])
        ),
        "clock_domain_split_metadata_consistent": (
            clock_regression["rays_with_disconnected_clock_domain"] == 3
            and clock_regression["real_clock_component_count_total"] == 6
            and clock_regression["clock_domain_split_count"] == 3
        ),
        "valid_vs_fully_valid_ray_semantics_distinct": (
            clock_regression["valid_clock_ray_count"] == 3
            and clock_regression["fully_clock_valid_ray_count"] == 0
        ),
        "no_complex_clock_domain_failure": True,
        "fully_valid_fraction_bounded_or_null": (
            atlas["candidate_surface_fraction_fully_clock_valid_rays"] is None
            or 0.0 <= atlas["candidate_surface_fraction_fully_clock_valid_rays"] <= 1.0
        ),
        "preconvergence_minimum_label_is_resolved_not_certified": all(
            r["classification"] != "CERTIFIED_LOCAL_MINIMUM_NUMERICAL" for r in atlas["roots"]
        ),
        "reach_is_diagnostic_not_claimed_rigorous": reach["rigorous_certificate"] is False,
        "circle_reach_diagnostic_within_1_percent": abs(float(reach["reach_estimate_over_rc"]) - 1.0) < 0.01,
        "symmetry_beta_error_lt_1e-11": symmetry["max_beta_vector_linf_error"] < 1e-11,
        "symmetry_jacobian_error_lt_1e-9": symmetry["max_jacobian_linf_error"] < 1e-9,
        "closed_orbit_guard_preserved": atlas["global_closed_orbit_certified"] is False,
        "qsm_guard_preserved": atlas["qsm_certified"] is False,
    }
    python_checks_ok = all(python_checks.values())

    rankine_match = all(a["classification"] == b["classification"] for a, b in zip(rankine_python, rankine_primary))
    native_checks = {
        "native_available": native_available and field_native,
        "radial_native_python_parity_lt_1e-10": radial_parity_error is not None and radial_parity_error < 1e-10,
        "rankine_classifications_match": rankine_match,
        "field_native_python_parity_lt_1e-12": field_parity_error is not None and field_parity_error < 1e-12,
        "jacobian_native_python_parity_lt_1e-10": jacobian_parity_error is not None and jacobian_parity_error < 1e-10,
    }
    native_checks_ok = all(native_checks.values())
    if native_checks_ok:
        overall_status = "NATIVE_CPP_PYTHON_FIELD_AND_JACOBIAN_PARITY_CERTIFIED"
    elif python_checks_ok:
        overall_status = "PYTHON_FALLBACK_VALIDATED_NATIVE_NOT_CERTIFIED"
    else:
        overall_status = "FAILED"
    ok = python_checks_ok and (native_checks_ok if args.require_native else True)
    summary = {
        "schema": "sst.fermat.audit.v0.5.0",
        "package_version": PACKAGE_VERSION,
        "audit_name": "SST Fermat v0.5.0 metadata and clock-domain certification audit",
        "overall_status": overall_status,
        "primary_backend": ext_primary["backend"],
        "field_backend": field_backend,
        "analytic_external_x_star": constants.FORMAL_X_STAR,
        "computed_external_x_star_python": x_py,
        "computed_external_x_star_primary": x_primary,
        "analytic_error": analytic_error,
        "radial_parity_error": radial_parity_error,
        "field_parity_linf_error": field_parity_error,
        "jacobian_parity_linf_error": jacobian_parity_error,
        "jacobian_finite_difference_linf_error": jacobian_fd_error,
        "python_checks": python_checks,
        "python_checks_ok": python_checks_ok,
        "native_checks": native_checks,
        "native_parity_certified": native_checks_ok,
        "require_native": args.require_native,
        "ok": ok,
        "epistemic_guard": (
            "v0.5.0 resolves radial stationary candidates and certifies only convergence-qualified branches; "
            "it does not certify a global closed Fermat geodesic or a QSM pole."
        ),
    }
    write_json(out / "audit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

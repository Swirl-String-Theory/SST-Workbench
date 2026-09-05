#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from fermat_ext import constants
from fermat_ext.core import PACKAGE_VERSION, analyze_profile, sweep_profiles, write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots, centerline_summary, sample_ideal_knot
from fermat_ext.knot_scan import scan_catalog_matrix, scan_softening_matrix
from fermat_ext.resolution import resolution_plan


def main() -> int:
    p = argparse.ArgumentParser(description="Run the SST Fermat standalone v0.3 audit battery.")
    p.add_argument("--out-dir", default="audit_out")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--knot-preset", choices=("smoke", "medium"), default="smoke")
    args = p.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

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
    radial_native_parity_ok = native_available and radial_parity_error is not None and radial_parity_error < 1e-10

    a_values = [0.0038, 0.0042, 0.0048, 0.0052, 0.0060]
    rankine_python = sweep_profiles("rankine", a_values, force_python=True, auto_build=False)
    rankine_primary = sweep_profiles(
        "rankine", a_values, force_python=False, auto_build=not args.no_auto_build
    )
    write_json(out / "rankine_sweep_python.json", rankine_python)
    write_csv(out / "rankine_sweep_python.csv", rankine_python)
    write_json(out / "rankine_sweep_primary.json", rankine_primary)
    write_csv(out / "rankine_sweep_primary.csv", rankine_primary)

    rankine_parity_errors: list[float] = []
    rankine_classification_match = True
    for py_row, pr_row in zip(rankine_python, rankine_primary):
        rankine_classification_match &= py_row["classification"] == pr_row["classification"]
        x0, x1 = py_row["first_x_star"], pr_row["first_x_star"]
        if x0 is not None and x1 is not None:
            rankine_parity_errors.append(abs(float(x0) - float(x1)))
        elif x0 is not None or x1 is not None:
            rankine_parity_errors.append(math.inf)
    rankine_parity_linf = max(rankine_parity_errors, default=0.0) if native_available else None
    rankine_native_parity_ok = (
        native_available
        and rankine_classification_match
        and rankine_parity_linf is not None
        and rankine_parity_linf < 1e-10
    )

    rosenhead_critical = analyze_profile(
        "rosenhead", 0.0019, 1e-5, 0.05, 8000, force_python=True, auto_build=False
    )
    rosenhead_blocked = analyze_profile(
        "rosenhead", 0.0020, 1e-5, 0.05, 8000, force_python=True, auto_build=False
    )
    write_json(out / "rosenhead_0p0019_python.json", rosenhead_critical)
    write_json(out / "rosenhead_0p0020_python.json", rosenhead_blocked)

    knot_settings = (
        dict(centerline_points=128, stations=4, angles=8, radial_samples=48)
        if args.knot_preset == "smoke"
        else dict(centerline_points=256, stations=8, angles=12, radial_samples=80)
    )
    knot_matrix = scan_catalog_matrix(
        DEFAULT_KNOT_IDS,
        **knot_settings,
        scale_over_rc=1.0,
        rho_min=0.002,
        rho_max=0.05,
        epsilon=0.0045,
        auto_build=not args.no_auto_build,
    )
    write_json(out / "knot_matrix.json", knot_matrix)
    write_csv(out / "knot_matrix.csv", knot_matrix["rows"])
    for knot_id, pair in knot_matrix["results"].items():
        write_json(out / f"{knot_id}_primary.json", pair["primary"])
        write_json(out / f"{knot_id}_python.json", pair["python"])

    softening_smoke = scan_softening_matrix(
        DEFAULT_KNOT_IDS,
        epsilon_values=[0.0019, 0.0020, 0.0045],
        target_ds_over_epsilon=4.0,
        min_centerline_points=64,
        max_centerline_points=256,
        stations=1,
        angles=3,
        rho_min=0.0005,
        rho_max=0.02,
        radial_samples=12,
        parity_mode="none",
        auto_build=not args.no_auto_build,
    )
    write_json(out / "softening_matrix_smoke.json", softening_smoke)
    write_csv(out / "softening_matrix_smoke.csv", softening_smoke["rows"])

    catalog_rows = []
    plans = []
    for knot_id in DEFAULT_KNOT_IDS:
        curve = sample_ideal_knot(knot_id, n=1024, scale_over_rc=1.0)
        catalog_rows.append({"knot_id": knot_id, **centerline_summary(curve, knot_id)})
        plans.append(resolution_plan(knot_id, epsilon=0.0045, target_ds_over_epsilon=1.0, max_points=8192))
    write_json(out / "catalog_geometry_validation.json", catalog_rows)
    write_csv(out / "catalog_geometry_validation.csv", catalog_rows)
    write_json(out / "adaptive_resolution_plans.json", plans)

    catalog_ids_ok = tuple(available_knots()) == tuple(DEFAULT_KNOT_IDS)
    catalog_lengths_ok = all(row["source_length_relative_error"] < 2e-4 for row in catalog_rows)
    guards_ok = all(
        pair["primary"]["global_closed_orbit_certified"] is False
        and pair["primary"]["qsm_certified"] is False
        for pair in knot_matrix["results"].values()
    )
    python_checks = {
        "external_root_found": math.isfinite(x_py),
        "external_analytic_error_lt_1e-10": analytic_error < 1e-10,
        "rankine_sweep_has_five_rows": len(rankine_python) == 5,
        "rosenhead_0p0019_has_horizon_free_critical_root": (
            len(rosenhead_critical["critical_roots"]) >= 1
            and "WITH_EXTERNAL_CLOCK_DEGENERACY" not in rosenhead_critical["classification"]
        ),
        "rosenhead_0p0020_has_no_critical_root": len(rosenhead_blocked["critical_roots"]) == 0,
        "rosenhead_threshold_ordering": (
            constants.ROSENHEAD_HORIZON_THRESHOLD < constants.ROSENHEAD_CRITICAL_THRESHOLD
        ),
        "catalog_contains_exact_requested_knots": catalog_ids_ok,
        "catalog_source_lengths_reproduced_lt_2e-4": catalog_lengths_ok,
        "all_four_knot_guards_preserved": guards_ok,
        "all_four_knot_scans_completed": set(knot_matrix["knot_ids"]) == set(DEFAULT_KNOT_IDS),
        "adaptive_plans_cover_all_knots": len(plans) == 4 and all(p["selected_points"] >= 128 for p in plans),
        "softening_smoke_has_twelve_rows": len(softening_smoke["rows"]) == 12,
    }
    python_checks_ok = all(python_checks.values())
    native_checks = {
        "native_available": native_available,
        "radial_native_python_parity_lt_1e-10": radial_native_parity_ok,
        "rankine_native_python_parity_lt_1e-10": rankine_native_parity_ok,
        "all_four_knot_native_python_parity_lt_1e-10": knot_matrix[
            "native_python_parity_certified_for_all_knots"
        ],
    }
    native_parity_certified = all(native_checks.values())

    if native_parity_certified:
        overall_status = "NATIVE_CPP_PYTHON_PARITY_CERTIFIED"
    elif python_checks_ok:
        overall_status = "PYTHON_FALLBACK_VALIDATED_NATIVE_NOT_CERTIFIED"
    else:
        overall_status = "FAILED"

    ok = python_checks_ok and (native_parity_certified if args.require_native else True)
    summary = {
        "schema": "sst.fermat.audit.v0.3",
        "package_version": PACKAGE_VERSION,
        "audit_name": "SST Fermat Python+C++ audit battery with adaptive softening diagnostics",
        "overall_status": overall_status,
        "primary_backend": ext_primary["backend"],
        "analytic_external_x_star": constants.FORMAL_X_STAR,
        "computed_external_x_star_python": x_py,
        "computed_external_x_star_primary": x_primary,
        "analytic_error": analytic_error,
        "radial_parity_error": radial_parity_error,
        "rankine_parity_linf_error": rankine_parity_linf,
        "rosenhead_horizon_threshold_epsilon_over_rc": constants.ROSENHEAD_HORIZON_THRESHOLD,
        "rosenhead_critical_threshold_epsilon_over_rc": constants.ROSENHEAD_CRITICAL_THRESHOLD,
        "knot_ids": list(DEFAULT_KNOT_IDS),
        "python_checks": python_checks,
        "python_checks_ok": python_checks_ok,
        "native_checks": native_checks,
        "native_parity_certified": native_parity_certified,
        "require_native": args.require_native,
        "ok": ok,
        "epistemic_guard": (
            "The profile, softening, and four-knot scans certify numerical diagnostics only; "
            "they do not certify global closed Fermat geodesics or QSM poles."
        ),
    }
    write_json(out / "audit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

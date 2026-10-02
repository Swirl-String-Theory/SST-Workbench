#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from fermat_ext.core import backend_biot_savart_with_jacobian, write_csv, write_json
from fermat_ext.hole_bundle import (
    BundleGridDefinition,
    HoleBundleParameters,
    RigidMotionProjector,
    bundle_beta_and_jacobian,
    clock_chain,
    estimate_axial_hole_radius,
)
from fermat_ext.knot_catalog import sample_ideal_knot


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "v0.6.1 full-range divergence-free coaxial hole-bundle residual sweep. "
            "Default domain: R_b/R_hole in [0.06125,8], Gamma_h/Gamma_0 in [-8,8]."
        )
    )
    p.add_argument("--knot", default="3_1")
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-points", type=int, default=8192)

    p.add_argument("--radius-ratios", nargs="+", type=float, default=None,
                   help="Explicit radius ratios; overrides range generation.")
    p.add_argument("--radius-min", type=float, default=0.06125)
    p.add_argument("--radius-max", type=float, default=8.0)
    p.add_argument("--radius-count", type=int, default=33)
    p.add_argument("--radius-spacing", choices=["log", "linear"], default="log")
    p.add_argument("--radius-anchors", nargs="+", type=float,
                   default=[0.06125, 0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 4.0, 8.0])

    p.add_argument("--circulation-ratios", nargs="+", type=float, default=None,
                   help="Explicit circulation ratios; overrides range generation.")
    p.add_argument("--circulation-min", type=float, default=-8.0)
    p.add_argument("--circulation-max", type=float, default=8.0)
    p.add_argument("--circulation-step", type=float, default=0.25)
    p.add_argument("--circulation-anchors", nargs="+", type=float,
                   default=[-8, -4, -2, -1, -0.5, 0, 0.5, 1, 2, 4, 8])

    p.add_argument("--return-radius-factor", type=float, default=3.0)
    p.add_argument("--top-detail-count", type=int, default=64)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="v0.6.1_hole_bundle_sweep_output")
    return p


def generated_values(a: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, dict]:
    definition = BundleGridDefinition(
        radius_min=a.radius_min,
        radius_max=a.radius_max,
        radius_count=a.radius_count,
        radius_spacing=a.radius_spacing,
        circulation_min=a.circulation_min,
        circulation_max=a.circulation_max,
        circulation_step=a.circulation_step,
        radius_anchors=tuple(a.radius_anchors),
        circulation_anchors=tuple(a.circulation_anchors),
    )
    if a.radius_ratios is None and a.circulation_ratios is None:
        radii, gamma = definition.values()
        mode = "generated_full_range"
    else:
        if a.radius_ratios is None:
            radii, _ = definition.values()
        else:
            radii = np.unique(np.asarray(a.radius_ratios, float))
        if a.circulation_ratios is None:
            _, gamma = definition.values()
        else:
            gamma = np.unique(np.asarray(a.circulation_ratios, float))
            if np.min(gamma) <= 0 <= np.max(gamma):
                gamma = np.unique(np.append(gamma, 0.0))
        mode = "explicit_or_mixed"
    if len(radii) == 0 or np.any(radii <= 0) or not np.all(np.isfinite(radii)):
        raise ValueError("radius ratios must be finite and positive")
    if len(gamma) == 0 or not np.all(np.isfinite(gamma)):
        raise ValueError("circulation ratios must be finite")
    return radii, gamma, {
        "mode": mode,
        "definition": asdict(definition),
        "radius_values": radii.tolist(),
        "circulation_values": gamma.tolist(),
        "combination_count": int(len(radii) * len(gamma)),
    }


def main() -> int:
    a = parser().parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()

    radius_ratios, circulation_ratios, grid = generated_values(a)
    curve = sample_ideal_knot(a.knot, a.centerline_points)
    hole_radius = estimate_axial_hole_radius(curve)
    knot_beta_raw, _knot_jac_raw, backend = backend_biot_savart_with_jacobian(
        curve.tolist(),
        curve.tolist(),
        epsilon=a.epsilon,
        force_python=a.force_python,
        auto_build=not a.no_auto_build,
    )
    if a.require_native and backend.get("backend") != "cpp":
        raise SystemExit("native backend required")
    knot_beta = np.asarray(knot_beta_raw, float)
    projector = RigidMotionProjector(curve)
    baseline_fit = projector.fit(knot_beta)
    baseline = float(baseline_fit["relative_shape_residual"])
    baseline_residual_norm = float(baseline_fit["residual_norm"])
    baseline_velocity_norm = float(baseline_fit["velocity_norm"])
    field_cache_path = out / "baseline_field_cache.npz"
    np.savez_compressed(
        field_cache_path, curve=curve, knot_beta=knot_beta,
        hole_radius_over_rc=np.array([hole_radius]),
        epsilon_over_rc=np.array([a.epsilon]),
        centerline_points=np.array([a.centerline_points]),
    )

    rows: list[dict] = []
    candidate_details: list[tuple[float, str, dict]] = []
    zero_control_residuals: list[float] = []
    for rr in radius_ratios:
        rb = float(rr * hole_radius)
        return_radius = max(float(a.return_radius_factor * rb), rb + 1e-12)
        for gr in circulation_ratios:
            bundle = HoleBundleParameters(
                core_radius_over_rc=rb,
                return_radius_over_rc=return_radius,
                circulation_ratio=float(gr),
            )
            bg, _ = bundle_beta_and_jacobian(curve, bundle)
            total = knot_beta + bg
            fit = projector.fit(total)
            residual = float(fit["relative_shape_residual"])
            relative_gain = 1.0 - residual / baseline if baseline > 0 else None
            residual_norm = float(fit["residual_norm"])
            absolute_gain = 1.0 - residual_norm / baseline_residual_norm if baseline_residual_norm > 0 else None
            energy_gain = 1.0 - (residual_norm / baseline_residual_norm) ** 2 if baseline_residual_norm > 0 else None
            key = f"R{rr:.12g}_G{gr:.12g}"
            bundle_rms = float(np.sqrt(np.mean(np.sum(bg * bg, axis=1))))
            total_max = float(np.max(np.linalg.norm(total, axis=1)))
            boundary_radius = bool(
                math.isclose(rr, radius_ratios[0], rel_tol=0, abs_tol=1e-14)
                or math.isclose(rr, radius_ratios[-1], rel_tol=0, abs_tol=1e-14)
            )
            boundary_gamma = bool(
                math.isclose(gr, circulation_ratios[0], rel_tol=0, abs_tol=1e-14)
                or math.isclose(gr, circulation_ratios[-1], rel_tol=0, abs_tol=1e-14)
            )
            row = {
                "key": key,
                "radius_ratio_to_hole": float(rr),
                "bundle_radius_over_rc": rb,
                "return_radius_over_rc": return_radius,
                "circulation_ratio": float(gr),
                "shape_residual": residual,
                "baseline_residual": baseline,
                "shape_residual_norm": residual_norm,
                "shape_residual_norm_over_baseline_velocity": residual_norm / baseline_velocity_norm if baseline_velocity_norm > 0 else None,
                "bundle_gain": absolute_gain,
                "absolute_shape_gain": absolute_gain,
                "absolute_shape_energy_gain": energy_gain,
                "relative_bundle_gain": relative_gain,
                "stabilizing": bool(absolute_gain is not None and absolute_gain > 0),
                "relative_only_stabilizing": bool(relative_gain is not None and relative_gain > 0 and (absolute_gain is None or absolute_gain <= 0)),
                "neutral_control": bool(abs(gr) < 1e-15),
                "boundary_radius": boundary_radius,
                "boundary_circulation": boundary_gamma,
                "parameter_box_boundary": bool(boundary_radius or boundary_gamma),
                "bundle_beta_rms": bundle_rms,
                "total_beta_max": total_max,
                "clock_valid_on_centerline": bool(total_max < 1.0),
            }
            rows.append(row)
            detail = {
                "bundle": asdict(bundle),
                "fit": fit,
                "bundle_beta_rms": bundle_rms,
                "total_beta_max": total_max,
                "clock_chain": clock_chain(bundle),
            }
            candidate_details.append((residual, key, detail))
            if abs(gr) < 1e-15:
                zero_control_residuals.append(residual)

    rows.sort(key=lambda x: (not x["clock_valid_on_centerline"], x["shape_residual_norm"], abs(x["circulation_ratio"])))
    candidate_details.sort(key=lambda x: float(x[2]["fit"]["residual_norm"]))
    details = {key: detail for _, key, detail in candidate_details[: max(0, a.top_detail_count)]}
    best = rows[0] if rows else None
    positive = [r for r in rows if r["stabilizing"]]
    null_error = max((abs(x - baseline) for x in zero_control_residuals), default=0.0)
    elapsed = time.perf_counter() - start

    combined = {
        "schema": "sst.fermat.hole-bundle-sweep.v0.6.1",
        "status": "RESEARCH_TRACK_SWEEP_COMPLETED",
        "package_version": "0.6.1",
        "knot_id": a.knot,
        "epsilon_over_rc": a.epsilon,
        "centerline_points": a.centerline_points,
        "estimated_hole_radius_over_rc": hole_radius,
        "return_radius_factor": a.return_radius_factor,
        "grid": grid,
        "field_cache": str(field_cache_path),
        "baseline": {
            "backend": backend,
            "fit": baseline_fit,
            "primary_comparison_metric": "absolute residual norm after best rigid-motion subtraction",
            "knot_beta_rms": float(np.sqrt(np.mean(np.sum(knot_beta * knot_beta, axis=1)))),
        },
        "quality_controls": {
            "zero_circulation_control_count": len(zero_control_residuals),
            "zero_circulation_max_abs_residual_error": null_error,
            "zero_control_pass": bool(null_error <= 1e-12),
            "finite_rows": bool(all(math.isfinite(r["shape_residual"]) for r in rows)),
        },
        "summary": {
            "row_count": len(rows),
            "stabilizing_count": len(positive),
            "neutral_count": sum(1 for r in rows if abs(float(r["absolute_shape_gain"] or 0.0)) <= 1e-14),
            "destabilizing_count": sum(1 for r in rows if r["absolute_shape_gain"] is not None and r["absolute_shape_gain"] < -1e-14),
            "relative_only_stabilizing_count": sum(1 for r in rows if r["relative_only_stabilizing"]),
            "clock_invalid_on_centerline_count": sum(1 for r in rows if not r["clock_valid_on_centerline"]),
            "best_is_parameter_box_boundary": bool(best and best["parameter_box_boundary"]),
            "best_requires_range_extension": bool(best and best["parameter_box_boundary"]),
            "elapsed_seconds": elapsed,
        },
        "rows": rows,
        "best": best,
        "top_details": details,
        "bundle_model": "smooth coaxial central flux plus opposite return flux in a periodic axial cell",
        "physical_finite_closed_bundle_certified": False,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
        "epistemic_guard": (
            "The primary stabilization metric is reduction of the absolute residual norm after rigid-motion subtraction. "
            "A lower relative residual alone can be produced by adding a large rigid velocity and is reported separately. "
            "It is not a dynamically self-consistent relative equilibrium, a finite closed bundle, "
            "a global Fermat orbit, or a particle-mode certification."
        ),
    }
    write_json(out / "hole_bundle_sweep.json", combined)
    write_csv(out / "hole_bundle_sweep.csv", rows)
    write_json(out / "grid_definition.json", grid)
    print(json.dumps({"baseline": baseline, "best": best, "grid": {"radii": len(radius_ratios), "circulations": len(circulation_ratios), "rows": len(rows)}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

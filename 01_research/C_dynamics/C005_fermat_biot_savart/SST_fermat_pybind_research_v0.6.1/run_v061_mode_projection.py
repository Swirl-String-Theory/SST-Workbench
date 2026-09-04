#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from fermat_ext.core import backend_biot_savart_with_jacobian, write_csv, write_json
from fermat_ext.hole_bundle import (
    HoleBundleParameters,
    RigidMotionProjector,
    bundle_beta_and_jacobian,
    estimate_axial_hole_radius,
    fourier_mode_projection,
)
from fermat_ext.knot_catalog import sample_ideal_knot


def main() -> int:
    p = argparse.ArgumentParser(description="v0.6.1 Fourier diagnostic of which trefoil residual modes are reduced by the best bundle.")
    p.add_argument("--sweep-json", required=True)
    p.add_argument("--centerline-points", type=int, default=None)
    p.add_argument("--field-cache", default=None)
    p.add_argument("--max-mode", type=int, default=64)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="v0.6.1_mode_projection_output")
    a = p.parse_args()

    start = time.perf_counter()
    source_path = Path(a.sweep_json)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    best = source.get("best")
    if not best:
        raise SystemExit("sweep has no best candidate")
    knot_id = source["knot_id"]
    epsilon = float(source["epsilon_over_rc"])
    n = int(a.centerline_points or source["centerline_points"])
    return_factor = float(source.get("return_radius_factor", 3.0))

    if a.field_cache:
        cache = np.load(a.field_cache)
        if len(cache["curve"]) != n or abs(float(cache["epsilon_over_rc"][0]) - epsilon) > 1e-15:
            raise SystemExit("field cache does not match requested resolution/epsilon")
        curve = np.asarray(cache["curve"], float)
        knot = np.asarray(cache["knot_beta"], float)
        hole_radius = float(cache["hole_radius_over_rc"][0])
        backend = {"backend": "cached", "source": str(a.field_cache)}
    else:
        curve = sample_ideal_knot(knot_id, n)
        hole_radius = estimate_axial_hole_radius(curve)
        raw, _jac, backend = backend_biot_savart_with_jacobian(
            curve.tolist(), curve.tolist(), epsilon=epsilon,
            force_python=a.force_python, auto_build=not a.no_auto_build,
        )
        if a.require_native and backend.get("backend") != "cpp":
            raise SystemExit("native backend required")
        knot = np.asarray(raw, float)
    rr = float(best["radius_ratio_to_hole"])
    gr = float(best["circulation_ratio"])
    rb = rr * hole_radius
    bundle = HoleBundleParameters(rb, max(return_factor * rb, rb + 1e-12), gr)
    bg, _ = bundle_beta_and_jacobian(curve, bundle)
    projector = RigidMotionProjector(curve)
    base_res, _base_pred, _base_coeff = projector.residual_vectors(knot)
    bundle_res, _bundle_pred, _bundle_coeff = projector.residual_vectors(knot + bg)
    projection = fourier_mode_projection(base_res, bundle_res, max_mode=a.max_mode)
    base_norm = float(np.linalg.norm(base_res))
    bundle_norm = float(np.linalg.norm(bundle_res))
    projection.update({
        "status": "RESEARCH_TRACK_MODE_PROJECTION_COMPLETED",
        "source_sweep": str(source_path),
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "centerline_points": n,
        "estimated_hole_radius_over_rc": hole_radius,
        "tested_candidate": {"radius_ratio_to_hole": rr, "circulation_ratio": gr, "bundle_radius_over_rc": rb},
        "backend": backend,
        "baseline_shape_residual_norm": base_norm,
        "bundle_shape_residual_norm": bundle_norm,
        "total_residual_energy_gain": 1.0 - (bundle_norm * bundle_norm) / (base_norm * base_norm) if base_norm > 0 else None,
        "elapsed_seconds": time.perf_counter() - start,
        "physical_finite_closed_bundle_certified": False,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    })
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "mode_projection.json", projection)
    write_csv(out / "mode_projection_rows.csv", projection["rows"])
    print(json.dumps({
        "tested_candidate": projection["tested_candidate"],
        "total_residual_energy_gain": projection["total_residual_energy_gain"],
        "largest_reductions": projection["largest_absolute_reductions"][:5],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

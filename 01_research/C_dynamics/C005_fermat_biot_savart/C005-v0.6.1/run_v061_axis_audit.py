#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from fermat_ext.core import backend_biot_savart_with_jacobian, write_csv, write_json
from fermat_ext.hole_bundle import (
    HoleBundleParameters,
    RigidMotionProjector,
    axis_direction_from_tilts,
    bundle_beta_and_jacobian,
    estimate_axial_hole_radius,
)
from fermat_ext.knot_catalog import sample_ideal_knot


def main() -> int:
    p = argparse.ArgumentParser(description="v0.6.1 axis-offset and tilt robustness audit for the best hole-bundle candidate.")
    p.add_argument("--sweep-json", required=True)
    p.add_argument("--offset-fractions", nargs="+", type=float, default=[0.0, 0.025, 0.05, 0.1, 0.2])
    p.add_argument("--tilt-degrees", nargs="+", type=float, default=[0.0, 1.0, 2.0, 5.0, 10.0])
    p.add_argument("--centerline-points", type=int, default=None)
    p.add_argument("--field-cache", default=None)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="v0.6.1_axis_audit_output")
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
    projector = RigidMotionProjector(curve)
    baseline_fit = projector.fit(knot)
    baseline = float(baseline_fit["relative_shape_residual"])
    baseline_residual_norm = float(baseline_fit["residual_norm"])
    rr = float(best["radius_ratio_to_hole"])
    gr = float(best["circulation_ratio"])
    rb = rr * hole_radius
    ret = max(return_factor * rb, rb + 1e-12)

    cases: list[dict] = []
    seen: set[tuple] = set()

    def evaluate(label: str, origin: tuple[float, float, float], direction: tuple[float, float, float], family: str, magnitude: float) -> None:
        key = tuple(round(x, 14) for x in (*origin, *direction))
        if key in seen:
            return
        seen.add(key)
        params = HoleBundleParameters(rb, ret, gr, origin, direction)
        bg, _ = bundle_beta_and_jacobian(curve, params)
        fit = projector.fit(knot + bg)
        residual = float(fit["relative_shape_residual"])
        relative_gain = 1.0 - residual / baseline if baseline > 0 else None
        residual_norm = float(fit["residual_norm"])
        gain = 1.0 - residual_norm / baseline_residual_norm if baseline_residual_norm > 0 else None
        cases.append({
            "label": label,
            "family": family,
            "magnitude": magnitude,
            "axis_origin_over_rc": list(origin),
            "axis_direction": list(direction),
            "shape_residual": residual,
            "shape_residual_norm": residual_norm,
            "baseline_residual": baseline,
            "baseline_residual_norm": baseline_residual_norm,
            "bundle_gain": gain,
            "absolute_shape_gain": gain,
            "relative_bundle_gain": relative_gain,
            "stabilizing": bool(gain is not None and gain > 0),
        })

    evaluate("nominal", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "nominal", 0.0)
    for frac in sorted(set(abs(float(x)) for x in a.offset_fractions)):
        if frac == 0:
            continue
        d = frac * hole_radius
        for axis, vec in [("x", (d, 0.0, 0.0)), ("y", (0.0, d, 0.0))]:
            for sign in (-1.0, 1.0):
                origin = tuple(sign * x for x in vec)
                evaluate(f"offset_{axis}_{sign:+g}_{frac:g}Rhole", origin, (0.0, 0.0, 1.0), "offset", frac)
    for deg in sorted(set(abs(float(x)) for x in a.tilt_degrees)):
        if deg == 0:
            continue
        for axis in ("x", "y"):
            for sign in (-1.0, 1.0):
                tx = sign * deg if axis == "x" else 0.0
                ty = sign * deg if axis == "y" else 0.0
                direction = axis_direction_from_tilts(tx, ty)
                evaluate(f"tilt_{axis}_{sign:+g}_{deg:g}deg", (0.0, 0.0, 0.0), direction, "tilt", deg)

    cases.sort(key=lambda r: r["shape_residual_norm"])
    nominal = next(r for r in cases if r["label"] == "nominal")
    positive_cases = [r for r in cases if r["stabilizing"]]
    report = {
        "schema": "sst.fermat.hole-bundle-axis-robustness.v0.6.1",
        "status": "RESEARCH_TRACK_AXIS_AUDIT_COMPLETED",
        "source_sweep": str(source_path),
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "centerline_points": n,
        "estimated_hole_radius_over_rc": hole_radius,
        "tested_candidate": {"radius_ratio_to_hole": rr, "circulation_ratio": gr, "bundle_radius_over_rc": rb},
        "backend": backend,
        "nominal": nominal,
        "best_case": cases[0],
        "worst_case": cases[-1],
        "case_count": len(cases),
        "stabilizing_case_count": len(positive_cases),
        "all_tested_perturbations_remain_stabilizing": bool(all(r["stabilizing"] for r in cases)),
        "cases": cases,
        "elapsed_seconds": time.perf_counter() - start,
        "physical_finite_closed_bundle_certified": False,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "axis_robustness_audit.json", report)
    write_csv(out / "axis_robustness_rows.csv", cases)
    print(json.dumps({"nominal": nominal, "best_case": cases[0], "worst_case": cases[-1]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

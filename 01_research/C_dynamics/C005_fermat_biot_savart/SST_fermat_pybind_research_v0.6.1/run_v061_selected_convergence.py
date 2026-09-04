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
    bundle_beta_and_jacobian,
    estimate_axial_hole_radius,
)
from fermat_ext.knot_catalog import sample_ideal_knot


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def select_rows(rows: list[dict], count: int) -> list[dict]:
    stabilizing = [r for r in rows if r.get("stabilizing")]
    pool = stabilizing if stabilizing else rows
    selected: list[dict] = []
    for row in pool:
        if len(selected) >= count:
            break
        lr = math.log(float(row["radius_ratio_to_hole"]))
        g = float(row["circulation_ratio"])
        # Avoid spending every convergence slot on a single very narrow grid lobe.
        if any(abs(lr - math.log(float(s["radius_ratio_to_hole"]))) < 0.045 and abs(g - float(s["circulation_ratio"])) < 0.20 for s in selected):
            continue
        selected.append(row)
    return selected


def main() -> int:
    p = argparse.ArgumentParser(description="v0.6.1 selected-candidate centerline convergence audit.")
    p.add_argument("--sweep-json", required=True)
    p.add_argument("--centerline-levels", nargs="+", type=int, default=[2048, 4096, 8192])
    p.add_argument("--candidate-count", type=int, default=12)
    p.add_argument("--field-cache", default=None, help="Optional NPZ cache from the sweep for the matching finest level.")
    p.add_argument("--gain-abs-tolerance", type=float, default=0.005)
    p.add_argument("--return-radius-factor", type=float, default=None)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="v0.6.1_selected_convergence_output")
    a = p.parse_args()

    start = time.perf_counter()
    source_path = Path(a.sweep_json)
    source = load_json(source_path)
    rows = source.get("rows", [])
    selected = select_rows(rows, a.candidate_count)
    if not selected:
        raise SystemExit("no candidate rows found in sweep")
    knot_id = source["knot_id"]
    epsilon = float(source["epsilon_over_rc"])
    return_factor = float(a.return_radius_factor if a.return_radius_factor is not None else source.get("return_radius_factor", 3.0))
    levels = sorted(set(int(n) for n in a.centerline_levels))
    if any(n < 64 for n in levels):
        raise SystemExit("centerline levels must be >=64")

    cache = None
    if a.field_cache:
        cache = np.load(a.field_cache)

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    level_reports: list[dict] = []
    flat_rows: list[dict] = []
    backend_records: list[dict] = []

    for n in levels:
        used_cache = False
        if cache is not None and len(cache["curve"]) == n and abs(float(cache["epsilon_over_rc"][0]) - epsilon) <= 1e-15:
            curve = np.asarray(cache["curve"], float)
            knot = np.asarray(cache["knot_beta"], float)
            hole_radius = float(cache["hole_radius_over_rc"][0])
            backend = {"backend": "cached", "source": str(a.field_cache)}
            used_cache = True
        else:
            curve = sample_ideal_knot(knot_id, n)
            hole_radius = estimate_axial_hole_radius(curve)
            raw, _jac, backend = backend_biot_savart_with_jacobian(
                curve.tolist(), curve.tolist(), epsilon=epsilon,
                force_python=a.force_python, auto_build=not a.no_auto_build,
            )
            if a.require_native and backend.get("backend") != "cpp":
                raise SystemExit(f"native backend required at N={n}")
            knot = np.asarray(raw, float)
        backend_records.append({"centerline_points": n, "backend": backend, "used_cache": used_cache})
        projector = RigidMotionProjector(curve)
        baseline_fit = projector.fit(knot)
        baseline = float(baseline_fit["relative_shape_residual"])
        baseline_residual_norm = float(baseline_fit["residual_norm"])
        level_candidates = []
        for candidate in selected:
            rr = float(candidate["radius_ratio_to_hole"])
            gr = float(candidate["circulation_ratio"])
            rb = rr * hole_radius
            params = HoleBundleParameters(
                core_radius_over_rc=rb,
                return_radius_over_rc=max(return_factor * rb, rb + 1e-12),
                circulation_ratio=gr,
            )
            bg, _ = bundle_beta_and_jacobian(curve, params)
            fit = projector.fit(knot + bg)
            residual = float(fit["relative_shape_residual"])
            relative_gain = 1.0 - residual / baseline if baseline > 0 else None
            residual_norm = float(fit["residual_norm"])
            gain = 1.0 - residual_norm / baseline_residual_norm if baseline_residual_norm > 0 else None
            row = {
                "centerline_points": n,
                "radius_ratio_to_hole": rr,
                "circulation_ratio": gr,
                "hole_radius_over_rc": hole_radius,
                "bundle_radius_over_rc": rb,
                "baseline_residual": baseline,
            "baseline_residual_norm": baseline_residual_norm,
                "shape_residual": residual,
                "shape_residual_norm": residual_norm,
                "baseline_residual_norm": baseline_residual_norm,
                "bundle_gain": gain,
                "absolute_shape_gain": gain,
                "relative_bundle_gain": relative_gain,
            }
            flat_rows.append(row)
            level_candidates.append(row)
        level_candidates.sort(key=lambda r: r["shape_residual_norm"])
        level_reports.append({
            "centerline_points": n,
            "estimated_hole_radius_over_rc": hole_radius,
            "baseline_residual": baseline,
            "baseline_residual_norm": baseline_residual_norm,
            "ranked_candidates": level_candidates,
            "best": level_candidates[0],
        })

    identities = [(float(r["radius_ratio_to_hole"]), float(r["circulation_ratio"])) for r in selected]
    candidate_convergence = []
    for rr, gr in identities:
        seq = [r for r in flat_rows if math.isclose(r["radius_ratio_to_hole"], rr) and math.isclose(r["circulation_ratio"], gr)]
        seq.sort(key=lambda r: r["centerline_points"])
        gains = [float(r["bundle_gain"]) for r in seq if r["bundle_gain"] is not None]
        spread = max(gains) - min(gains) if gains else math.inf
        last_delta = abs(gains[-1] - gains[-2]) if len(gains) >= 2 else math.inf
        candidate_convergence.append({
            "radius_ratio_to_hole": rr,
            "circulation_ratio": gr,
            "levels": seq,
            "gain_range": spread,
            "last_gain_delta": last_delta,
            "gain_sign_stable": bool(gains and all(g > 0 for g in gains)),
            "numerically_converged_bundle_gain": bool(len(gains) >= 3 and last_delta <= a.gain_abs_tolerance),
        })
    candidate_convergence.sort(key=lambda r: r["levels"][-1]["shape_residual_norm"])
    best_finest = level_reports[-1]["best"]
    best_identity = (best_finest["radius_ratio_to_hole"], best_finest["circulation_ratio"])
    same_best_last_two = False
    if len(level_reports) >= 2:
        prev = level_reports[-2]["best"]
        same_best_last_two = (
            math.isclose(prev["radius_ratio_to_hole"], best_identity[0])
            and math.isclose(prev["circulation_ratio"], best_identity[1])
        )

    report = {
        "schema": "sst.fermat.hole-bundle-selected-convergence.v0.6.1",
        "status": "RESEARCH_TRACK_CONVERGENCE_AUDIT_COMPLETED",
        "source_sweep": str(source_path),
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "return_radius_factor": return_factor,
        "centerline_levels": levels,
        "candidate_count": len(selected),
        "selected_candidates": selected,
        "level_reports": level_reports,
        "candidate_convergence": candidate_convergence,
        "best_finest": best_finest,
        "same_best_identity_last_two_levels": same_best_last_two,
        "any_gain_converged": any(x["numerically_converged_bundle_gain"] for x in candidate_convergence),
        "backend_records": backend_records,
        "elapsed_seconds": time.perf_counter() - start,
        "physical_finite_closed_bundle_certified": False,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    write_json(out / "selected_convergence.json", report)
    write_csv(out / "selected_convergence_rows.csv", flat_rows)
    print(json.dumps({"best_finest": best_finest, "same_best_last_two": same_best_last_two, "any_gain_converged": report["any_gain_converged"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

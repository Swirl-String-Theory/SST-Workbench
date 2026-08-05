#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_json
from fermat_ext.geodesic import certify_global_closed_orbit
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS


def main() -> int:
    p = argparse.ArgumentParser(description="Two-axis global Fermat closed-orbit convergence gate.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-point-counts", nargs="+", type=int, default=[2048, 4096, 8192])
    p.add_argument("--step-counts", nargs="+", type=int, default=[256, 512, 1024])
    p.add_argument("--candidate-angles", type=int, default=8)
    p.add_argument("--angle-index", type=int, default=0)
    p.add_argument("--max-iterations", type=int, default=10)
    p.add_argument("--centerline-relative-tol", type=float, default=2e-3)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="orbit_convergence")
    a = p.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    results = {}; rows = []
    for i, knot_id in enumerate(a.knots):
        result = certify_global_closed_orbit(
            knot_id, epsilon=a.epsilon,
            centerline_point_counts=a.centerline_point_counts,
            step_counts=a.step_counts,
            candidate_angles=a.candidate_angles,
            candidate_angle_index=a.angle_index,
            max_iterations=a.max_iterations,
            centerline_relative_tolerance=a.centerline_relative_tol,
            force_python=a.force_python,
            auto_build=(not a.no_auto_build) if i == 0 else False,
        )
        if a.require_native:
            backends = []
            for level in result["levels"]:
                integ = level.get("integration_convergence")
                if not integ:
                    continue
                for shot in integ["levels"]:
                    backend = shot.get("best", {}).get("integration", {}).get("backend", {}).get("backend")
                    if backend:
                        backends.append(backend)
            if not backends or any(v != "cpp" for v in backends):
                raise SystemExit("native backend required but at least one orbit level was not C++")
        results[knot_id] = result
        write_json(out / f"{knot_id}.json", result)
        rows.append({
            "knot_id": knot_id,
            "status": result["status"],
            "global_closed_orbit_certified": result["global_closed_orbit_certified"],
            "period_relative_drift": result["last_two_period_relative_drift"],
            "seed_rho_relative_drift": result["last_two_seed_rho_relative_drift"],
            "start_position_relative_drift": result["last_two_start_position_relative_drift"],
        })
    combined = {
        "schema": "sst.fermat.global-closed-orbit-matrix.v0.6.1",
        "rows": rows,
        "results": results,
        "all_requested_knots_certified": all(r["global_closed_orbit_certified"] for r in results.values()),
        "qsm_certified": False,
    }
    write_json(out / "orbit_convergence.json", combined)
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

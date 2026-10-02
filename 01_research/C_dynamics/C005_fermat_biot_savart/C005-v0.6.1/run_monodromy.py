#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_json
from fermat_ext.geodesic import certify_global_closed_orbit, certify_monodromy_convergence
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, sample_ideal_knot


def main() -> int:
    p = argparse.ArgumentParser(description="Global-orbit-gated reduced monodromy convergence scan.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-point-counts", nargs="+", type=int, default=[2048, 4096, 8192])
    p.add_argument("--step-counts", nargs="+", type=int, default=[256, 512, 1024])
    p.add_argument("--perturbation-scales", nargs="+", type=float, default=[4e-5, 2e-5, 1e-5])
    p.add_argument("--candidate-angles", type=int, default=8)
    p.add_argument("--angle-index", type=int, default=0)
    p.add_argument("--max-iterations", type=int, default=10)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="monodromy")
    a = p.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    results = {}; rows = []
    for i, knot_id in enumerate(a.knots):
        orbit = certify_global_closed_orbit(
            knot_id, epsilon=a.epsilon,
            centerline_point_counts=a.centerline_point_counts,
            step_counts=a.step_counts,
            candidate_angles=a.candidate_angles,
            candidate_angle_index=a.angle_index,
            max_iterations=a.max_iterations,
            force_python=a.force_python,
            auto_build=(not a.no_auto_build) if i == 0 else False,
        )
        shot = orbit.get("highest_resolution_shot")
        if shot is None:
            monodromy = None
        else:
            curve = sample_ideal_knot(knot_id, max(a.centerline_point_counts))
            monodromy = certify_monodromy_convergence(
                curve, shot, epsilon=a.epsilon,
                perturbation_scales=a.perturbation_scales,
                force_python=a.force_python, auto_build=False,
            )
        if a.require_native and shot is not None:
            backend = shot.get("best", {}).get("integration", {}).get("backend", {}).get("backend")
            if backend != "cpp":
                raise SystemExit("native backend required")
        result = {"orbit": orbit, "monodromy": monodromy}
        results[knot_id] = result
        write_json(out / f"{knot_id}.json", result)
        rows.append({
            "knot_id": knot_id,
            "orbit_status": orbit["status"],
            "global_closed_orbit_certified": orbit["global_closed_orbit_certified"],
            "monodromy_status": monodromy["status"] if monodromy else None,
            "monodromy_certified": monodromy["monodromy_certified"] if monodromy else False,
            "spectral_radius": monodromy["levels"][-1]["spectral_radius"] if monodromy else None,
        })
    combined = {
        "schema": "sst.fermat.monodromy-convergence-matrix.v0.6.1",
        "rows": rows,
        "results": results,
        "all_requested_monodromies_certified": all(
            r["monodromy"] is not None and r["monodromy"]["monodromy_certified"] for r in results.values()
        ),
        "qsm_certified": False,
    }
    write_json(out / "monodromy.json", combined)
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

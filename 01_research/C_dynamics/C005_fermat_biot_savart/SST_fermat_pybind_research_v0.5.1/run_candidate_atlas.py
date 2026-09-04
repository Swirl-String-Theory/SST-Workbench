#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS


def main() -> int:
    p = argparse.ArgumentParser(description="Solve radial Fermat stationary roots for the four-knot matrix.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-points", type=int, default=8192)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--stations", type=int, default=8)
    p.add_argument("--angles", type=int, default=16)
    p.add_argument("--rho-min", type=float, default=0.0005)
    p.add_argument("--rho-max", type=float, default=0.03)
    p.add_argument("--bracket-samples", type=int, default=96)
    p.add_argument("--reach-pair-points", type=int, default=2048)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="candidate_atlas")
    args = p.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    results = {}
    for i, knot_id in enumerate(args.knots):
        result = scan_stationary_candidates(
            knot_id,
            epsilon=args.epsilon,
            centerline_points=args.centerline_points,
            scale_over_rc=args.scale_over_rc,
            stations=args.stations,
            angles=args.angles,
            rho_min=args.rho_min,
            rho_max=args.rho_max,
            bracket_samples=args.bracket_samples,
            force_python=args.force_python,
            auto_build=(not args.no_auto_build) if i == 0 else False,
            reach_pair_points=args.reach_pair_points,
        )
        if args.require_native and result["backend"]["backend"] != "cpp":
            raise SystemExit(f"native backend required but unavailable for {knot_id}")
        write_json(out / f"{knot_id}.json", result)
        results[knot_id] = result
        rows.append({
            "knot_id": knot_id,
            "backend": result["backend"]["backend"],
            "epsilon_over_rc": args.epsilon,
            "centerline_points": args.centerline_points,
            "scale_over_rc": args.scale_over_rc,
            "ray_count": result["ray_count"],
            "local_minimum_count": result["local_minimum_count"],
            "rays_with_local_minimum_count": result["rays_with_local_minimum_count"],
            "candidate_surface_fraction": result["candidate_surface_fraction"],
            "candidate_surface_fraction_all_rays": result["candidate_surface_fraction_all_rays"],
            "candidate_surface_fraction_fully_clock_valid_rays": result["candidate_surface_fraction_fully_clock_valid_rays"],
            "fully_clock_valid_ray_count": result["fully_clock_valid_ray_count"],
            "invalid_clock_probe_count": result["invalid_clock_probe_count"],
            "reach_estimate_over_rc": result["reach_diagnostic"]["reach_estimate_over_rc"],
        })
    combined = {
        "schema": "sst.fermat.candidate-atlas-matrix.v0.5.1",
        "settings": vars(args),
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    write_json(out / "candidate_atlas.json", combined)
    write_csv(out / "candidate_atlas.csv", rows)
    print(json.dumps({"out_dir": str(out), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

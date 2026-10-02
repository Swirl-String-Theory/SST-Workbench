#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.resolution import resolution_plan


def main() -> int:
    p = argparse.ArgumentParser(
        description="Separate ideal-knot scale from softening while controlling centerline resolution."
    )
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--scales", nargs="+", type=float, default=[0.5, 1.0, 2.0, 4.0])
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--resolution-mode", choices=("fixed", "adaptive"), default="adaptive")
    p.add_argument("--centerline-points", type=int, default=8192,
                   help="Used only when --resolution-mode fixed.")
    p.add_argument("--target-ds-over-epsilon", type=float, default=1.0)
    p.add_argument("--min-centerline-points", type=int, default=4096)
    p.add_argument("--max-centerline-points", type=int, default=65536)
    p.add_argument("--round-centerline-points-to", type=int, default=1024)
    p.add_argument("--stations", type=int, default=8)
    p.add_argument("--angles", type=int, default=16)
    p.add_argument("--rho-min", type=float, default=0.0005)
    p.add_argument("--rho-max", type=float, default=0.03)
    p.add_argument("--bracket-samples", type=int, default=96)
    p.add_argument("--reach-pair-points", type=int, default=1024)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="scale_sweep")
    args = p.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    results: dict[str, dict] = {}
    plans: dict[str, dict] = {}
    first = True

    for scale in args.scales:
        scale_key = f"{scale:.10g}"
        results[scale_key] = {}
        plans[scale_key] = {}
        for knot_id in args.knots:
            if args.resolution_mode == "adaptive":
                plan = resolution_plan(
                    knot_id,
                    epsilon=args.epsilon,
                    scale_over_rc=scale,
                    target_ds_over_epsilon=args.target_ds_over_epsilon,
                    min_points=args.min_centerline_points,
                    max_points=args.max_centerline_points,
                    round_to=args.round_centerline_points_to,
                )
                n_points = int(plan["selected_points"])
                plan["mode"] = "adaptive_length_and_scale_aware"
            else:
                n_points = int(args.centerline_points)
                plan = {
                    "knot_id": knot_id,
                    "mode": "fixed",
                    "selected_points": n_points,
                    "scale_over_rc": scale,
                    "epsilon_over_rc": args.epsilon,
                }
            plans[scale_key][knot_id] = plan

            result = scan_stationary_candidates(
                knot_id,
                epsilon=args.epsilon,
                centerline_points=n_points,
                scale_over_rc=scale,
                stations=args.stations,
                angles=args.angles,
                rho_min=args.rho_min,
                rho_max=args.rho_max,
                bracket_samples=args.bracket_samples,
                force_python=args.force_python,
                auto_build=(not args.no_auto_build) if first else False,
                reach_pair_points=args.reach_pair_points,
            )
            first = False
            if args.require_native and result["backend"]["backend"] != "cpp":
                raise SystemExit("native backend required")
            results[scale_key][knot_id] = result
            actual_ratio = result["centerline"]["edge_length_mean_over_rc"] / args.epsilon
            rows.append({
                "scale_over_rc": scale,
                "epsilon_over_rc": args.epsilon,
                "knot_id": knot_id,
                "resolution_mode": args.resolution_mode,
                "centerline_points": n_points,
                "actual_mean_ds_over_epsilon": actual_ratio,
                "resolution_target_met": actual_ratio <= args.target_ds_over_epsilon if args.resolution_mode == "adaptive" else None,
                "local_minimum_count": result["local_minimum_count"],
                "candidate_surface_fraction": result["candidate_surface_fraction"],
                "candidate_surface_fraction_all_rays": result["candidate_surface_fraction_all_rays"],
                "candidate_surface_fraction_fully_clock_valid_rays": result["candidate_surface_fraction_fully_clock_valid_rays"],
                "invalid_clock_probe_count": result["invalid_clock_probe_count"],
                "reach_estimate_over_rc": result["reach_diagnostic"]["reach_estimate_over_rc"],
            })

    combined = {
        "schema": "sst.fermat.scale-sweep.v0.4.3",
        "settings": vars(args),
        "resolution_plans": plans,
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    write_json(out / "resolution_plan.json", plans)
    write_json(out / "scale_sweep.json", combined)
    write_csv(out / "scale_sweep.csv", rows)
    print(json.dumps({"out_dir": str(out), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

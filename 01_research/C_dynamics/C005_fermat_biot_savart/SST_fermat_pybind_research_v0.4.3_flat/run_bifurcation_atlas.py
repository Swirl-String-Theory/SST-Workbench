#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fermat_ext.certification import build_bifurcation_atlas
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.resolution import resolution_plan


def _point_plan(args: argparse.Namespace, eps: list[float]) -> tuple[dict[str, int], dict[str, dict]]:
    if args.resolution_mode == "fixed":
        point_map = {k: int(args.centerline_points) for k in args.knots}
        plans = {
            k: {
                "knot_id": k,
                "mode": "fixed",
                "selected_points": int(args.centerline_points),
                "minimum_epsilon_over_rc": min(eps),
            }
            for k in args.knots
        }
        return point_map, plans

    plans: dict[str, dict] = {}
    point_map: dict[str, int] = {}
    minimum_epsilon = min(eps)
    for knot_id in args.knots:
        plan = resolution_plan(
            knot_id,
            epsilon=minimum_epsilon,
            scale_over_rc=args.scale_over_rc,
            target_ds_over_epsilon=args.target_ds_over_epsilon,
            min_points=args.min_centerline_points,
            max_points=args.max_centerline_points,
            round_to=args.round_centerline_points_to,
        )
        plan["mode"] = "adaptive_conservative_at_minimum_epsilon"
        plans[knot_id] = plan
        point_map[knot_id] = int(plan["selected_points"])
    return point_map, plans


def main() -> int:
    p = argparse.ArgumentParser(
        description="Track Fermat candidate branches across softening with fixed or convergence-aware resolution."
    )
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon-values", nargs="+", type=float)
    p.add_argument("--epsilon-start", type=float, default=0.00180)
    p.add_argument("--epsilon-stop", type=float, default=0.00210)
    p.add_argument("--epsilon-step", type=float, default=0.000025)
    p.add_argument("--resolution-mode", choices=("fixed", "adaptive"), default="adaptive")
    p.add_argument("--centerline-points", type=int, default=8192,
                   help="Used only when --resolution-mode fixed.")
    p.add_argument("--target-ds-over-epsilon", type=float, default=0.5)
    p.add_argument("--min-centerline-points", type=int, default=32768)
    p.add_argument("--max-centerline-points", type=int, default=65536)
    p.add_argument("--round-centerline-points-to", type=int, default=1024)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--stations", type=int, default=8)
    p.add_argument("--angles", type=int, default=16)
    p.add_argument("--rho-min", type=float, default=0.0005)
    p.add_argument("--rho-max", type=float, default=0.03)
    p.add_argument("--bracket-samples", type=int, default=96)
    p.add_argument("--reach-pair-points", type=int, default=1024)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="bifurcation_atlas")
    args = p.parse_args()

    eps = args.epsilon_values
    if eps is None:
        count = int(round((args.epsilon_stop - args.epsilon_start) / args.epsilon_step)) + 1
        eps = np.linspace(args.epsilon_start, args.epsilon_stop, count).tolist()
    eps = sorted(set(float(v) for v in eps))

    point_map, plans = _point_plan(args, eps)
    result = build_bifurcation_atlas(
        args.knots,
        epsilon_values=eps,
        centerline_points=point_map,
        scale_over_rc=args.scale_over_rc,
        stations=args.stations,
        angles=args.angles,
        rho_min=args.rho_min,
        rho_max=args.rho_max,
        bracket_samples=args.bracket_samples,
        force_python=args.force_python,
        auto_build=not args.no_auto_build,
        reach_pair_points=args.reach_pair_points,
    )
    result["resolution_mode"] = args.resolution_mode
    result["resolution_plans"] = plans

    if args.require_native:
        for knot_scans in result["scans"].values():
            if any(scan["backend"]["backend"] != "cpp" for scan in knot_scans.values()):
                raise SystemExit("native backend required but at least one scan used Python")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "resolution_plan.json", {
        "resolution_mode": args.resolution_mode,
        "centerline_points_by_knot": point_map,
        "plans": plans,
    })
    write_json(out / "bifurcation_atlas.json", result)
    write_csv(out / "bifurcation_rows.csv", result["rows"])
    write_csv(out / "bifurcation_summary.csv", result["branch_summaries"])
    print(json.dumps({
        "out_dir": str(out),
        "resolution_mode": args.resolution_mode,
        "centerline_points_by_knot": point_map,
        "branch_summaries": result["branch_summaries"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

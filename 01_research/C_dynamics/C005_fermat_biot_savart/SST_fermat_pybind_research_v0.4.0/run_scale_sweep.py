#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.certification import scan_stationary_candidates
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS


def main() -> int:
    p = argparse.ArgumentParser(description="Separate ideal-knot scale from the vortex softening scale.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--scales", nargs="+", type=float, default=[0.5, 1.0, 2.0, 4.0])
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-points", type=int, default=8192)
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
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    rows = []; results = {}; first = True
    for scale in args.scales:
        results[str(scale)] = {}
        for knot_id in args.knots:
            result = scan_stationary_candidates(
                knot_id,
                epsilon=args.epsilon,
                centerline_points=args.centerline_points,
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
            results[str(scale)][knot_id] = result
            rows.append({
                "scale_over_rc": scale,
                "epsilon_over_rc": args.epsilon,
                "knot_id": knot_id,
                "local_minimum_count": result["local_minimum_count"],
                "candidate_surface_fraction": result["candidate_surface_fraction"],
                "invalid_clock_probe_count": result["invalid_clock_probe_count"],
                "reach_estimate_over_rc": result["reach_diagnostic"]["reach_estimate_over_rc"],
            })
    combined = {
        "schema": "sst.fermat.scale-sweep.v0.4",
        "settings": vars(args),
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
    }
    write_json(out / "scale_sweep.json", combined)
    write_csv(out / "scale_sweep.csv", rows)
    print(json.dumps({"out_dir": str(out), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

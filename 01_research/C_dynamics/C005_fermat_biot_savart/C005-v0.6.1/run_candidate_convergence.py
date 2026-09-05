#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.certification import certify_candidate_convergence
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS


def main() -> int:
    p = argparse.ArgumentParser(description="Certify Fermat candidate convergence at N, 2N, and 4N.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--point-counts", nargs="+", type=int, default=[4096, 8192, 16384])
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--stations", type=int, default=8)
    p.add_argument("--angles", type=int, default=16)
    p.add_argument("--rho-min", type=float, default=0.0005)
    p.add_argument("--rho-max", type=float, default=0.03)
    p.add_argument("--bracket-samples", type=int, default=96)
    p.add_argument("--relative-tolerance", type=float, default=1e-3)
    p.add_argument("--strong-relative-tolerance", type=float, default=1e-4)
    p.add_argument("--reach-pair-points", type=int, default=2048)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="convergence_report")
    args = p.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    results = {}; rows = []
    for i, knot_id in enumerate(args.knots):
        result = certify_candidate_convergence(
            knot_id,
            epsilon=args.epsilon,
            point_counts=args.point_counts,
            scale_over_rc=args.scale_over_rc,
            stations=args.stations,
            angles=args.angles,
            rho_min=args.rho_min,
            rho_max=args.rho_max,
            bracket_samples=args.bracket_samples,
            relative_tolerance=args.relative_tolerance,
            strong_relative_tolerance=args.strong_relative_tolerance,
            force_python=args.force_python,
            auto_build=(not args.no_auto_build) if i == 0 else False,
            reach_pair_points=args.reach_pair_points,
        )
        highest = result["levels"][max(result["levels"])]
        if args.require_native and highest["backend"]["backend"] != "cpp":
            raise SystemExit(f"native backend required but unavailable for {knot_id}")
        results[knot_id] = result
        write_json(out / f"{knot_id}.json", result)
        rows.append({
            "knot_id": knot_id,
            "epsilon_over_rc": args.epsilon,
            "point_counts": ";".join(map(str, args.point_counts)),
            "branch_count": len(result["branches"]),
            "weakly_certified_branch_count": result["weakly_certified_branch_count"],
            "strongly_certified_branch_count": result["strongly_certified_branch_count"],
            "highest_backend": highest["backend"]["backend"],
        })
    combined = {
        "schema": "sst.fermat.convergence-matrix.v0.6.1",
        "settings": vars(args),
        "rows": rows,
        "results": results,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    write_json(out / "convergence_report.json", combined)
    write_csv(out / "convergence_report.csv", rows)
    print(json.dumps({"out_dir": str(out), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

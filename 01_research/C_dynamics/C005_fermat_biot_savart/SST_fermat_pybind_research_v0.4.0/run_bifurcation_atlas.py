#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fermat_ext.certification import build_bifurcation_atlas
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS


def main() -> int:
    p = argparse.ArgumentParser(description="Track Fermat candidate branches across the softening parameter.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon-values", nargs="+", type=float)
    p.add_argument("--epsilon-start", type=float, default=0.00180)
    p.add_argument("--epsilon-stop", type=float, default=0.00210)
    p.add_argument("--epsilon-step", type=float, default=0.000025)
    p.add_argument("--centerline-points", type=int, default=8192)
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
    result = build_bifurcation_atlas(
        args.knots,
        epsilon_values=eps,
        centerline_points=args.centerline_points,
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
    if args.require_native:
        for knot_scans in result["scans"].values():
            if any(scan["backend"]["backend"] != "cpp" for scan in knot_scans.values()):
                raise SystemExit("native backend required but at least one scan used Python")
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    write_json(out / "bifurcation_atlas.json", result)
    write_csv(out / "bifurcation_rows.csv", result["rows"])
    write_csv(out / "bifurcation_summary.csv", result["branch_summaries"])
    print(json.dumps({"out_dir": str(out), "branch_summaries": result["branch_summaries"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

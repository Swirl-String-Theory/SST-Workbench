#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from fermat_ext.core import write_json
from fermat_ext.knot_scan import scan_torus_knot


def main() -> int:
    p = argparse.ArgumentParser(description="Local transverse Fermat scan around a generated torus knot.")
    p.add_argument("--p", type=int, default=2)
    p.add_argument("--q", type=int, default=3)
    p.add_argument("--centerline-points", type=int, default=240)
    p.add_argument("--major-radius", type=float, default=1.0)
    p.add_argument("--minor-radius", type=float, default=0.35)
    p.add_argument("--stations", type=int, default=12)
    p.add_argument("--angles", type=int, default=16)
    p.add_argument("--rho-min", type=float, default=0.002)
    p.add_argument("--rho-max", type=float, default=0.05)
    p.add_argument("--radial-samples", type=int, default=120)
    p.add_argument("--epsilon", type=float, default=0.0045)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--out", default="trefoil_local_fermat_scan.json")
    p.add_argument("--summary-only", action="store_true")
    args = p.parse_args()
    result = scan_torus_knot(
        p=args.p, q=args.q, centerline_points=args.centerline_points,
        major_radius=args.major_radius, minor_radius=args.minor_radius,
        stations=args.stations, angles=args.angles,
        rho_min=args.rho_min, rho_max=args.rho_max,
        radial_samples=args.radial_samples, epsilon=args.epsilon,
        force_python=args.force_python, auto_build=not args.no_auto_build,
    )
    write_json(args.out, result)
    if args.summary_only:
        print(f"[LOCAL_SCAN] backend={result['backend']['backend']} candidates={result['candidate_count']} invalid_clock={result['invalid_clock_probe_count']}")
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

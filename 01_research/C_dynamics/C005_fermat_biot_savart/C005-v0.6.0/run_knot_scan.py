#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from fermat_ext.core import write_json
from fermat_ext.knot_catalog import available_knots
from fermat_ext.knot_scan import KERNEL_MODELS, scan_catalog_knot, scan_torus_knot
from fermat_ext.resolution import resolution_plan


def main() -> int:
    p = argparse.ArgumentParser(description="Local transverse Fermat scan around an ideal knot or generated torus knot.")
    p.add_argument("--knot-id", choices=available_knots(), default="3_1")
    p.add_argument("--generated-torus", action="store_true")
    p.add_argument("--p", type=int, default=2)
    p.add_argument("--q", type=int, default=3)
    p.add_argument("--centerline-points", type=int, default=512)
    p.add_argument("--adaptive-resolution", action="store_true")
    p.add_argument("--target-ds-over-epsilon", type=float, default=1.0)
    p.add_argument("--max-centerline-points", type=int, default=8192)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--major-radius", type=float, default=1.0)
    p.add_argument("--minor-radius", type=float, default=0.35)
    p.add_argument("--stations", type=int, default=16)
    p.add_argument("--angles", type=int, default=24)
    p.add_argument("--rho-min", type=float, default=0.002)
    p.add_argument("--rho-max", type=float, default=0.05)
    p.add_argument("--radial-samples", type=int, default=160)
    p.add_argument("--epsilon", type=float, default=0.0045)
    p.add_argument("--kernel-model", choices=KERNEL_MODELS, default="rosenhead_midpoint")
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--out", default=None)
    p.add_argument("--summary-only", action="store_true")
    args = p.parse_args()

    n_points = args.centerline_points
    if args.adaptive_resolution and not args.generated_torus:
        plan = resolution_plan(
            args.knot_id,
            epsilon=args.epsilon,
            scale_over_rc=args.scale_over_rc,
            target_ds_over_epsilon=args.target_ds_over_epsilon,
            max_points=args.max_centerline_points,
        )
        n_points = int(plan["selected_points"])

    if args.generated_torus:
        result = scan_torus_knot(
            p=args.p,
            q=args.q,
            centerline_points=n_points,
            major_radius=args.major_radius,
            minor_radius=args.minor_radius,
            stations=args.stations,
            angles=args.angles,
            rho_min=args.rho_min,
            rho_max=args.rho_max,
            radial_samples=args.radial_samples,
            epsilon=args.epsilon,
            kernel_model=args.kernel_model,
            force_python=args.force_python,
            auto_build=not args.no_auto_build,
        )
        default_name = f"torus_{args.p}_{args.q}_local_fermat_scan.json"
    else:
        result = scan_catalog_knot(
            knot_id=args.knot_id,
            centerline_points=n_points,
            scale_over_rc=args.scale_over_rc,
            stations=args.stations,
            angles=args.angles,
            rho_min=args.rho_min,
            rho_max=args.rho_max,
            radial_samples=args.radial_samples,
            epsilon=args.epsilon,
            kernel_model=args.kernel_model,
            resolution_target=args.target_ds_over_epsilon if args.adaptive_resolution else None,
            force_python=args.force_python,
            auto_build=not args.no_auto_build,
        )
        default_name = f"{args.knot_id}_local_fermat_scan.json"

    out = args.out or default_name
    write_json(out, result)
    if args.summary_only:
        print(
            f"[LOCAL_SCAN] knot={result['knot']['knot_id']} backend={result['backend']['backend']} "
            f"N={result['input']['centerline_points']} ds/eps={result['centerline_resolution']['mean_ds_over_epsilon']:.6g} "
            f"candidates={result['candidate_count']} invalid_clock={result['invalid_clock_probe_count']} "
            f"probes={result['probe_count']}"
        )
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

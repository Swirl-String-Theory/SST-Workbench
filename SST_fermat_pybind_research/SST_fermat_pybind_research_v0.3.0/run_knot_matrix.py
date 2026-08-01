#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots
from fermat_ext.knot_scan import KERNEL_MODELS, scan_catalog_matrix

PRESETS = {
    "smoke": dict(centerline_points=128, stations=4, angles=8, radial_samples=48),
    "standard": dict(centerline_points=512, stations=16, angles=24, radial_samples=160),
    "high": dict(centerline_points=1024, stations=32, angles=48, radial_samples=320),
}


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run the 0_1, 3_1, 4_1, 5_2 Fermat matrix with optional adaptive centerline resolution."
    )
    p.add_argument("--knot-ids", nargs="+", choices=available_knots(), default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--preset", choices=PRESETS, default="standard")
    p.add_argument("--centerline-points", type=int)
    p.add_argument("--adaptive-resolution", action="store_true")
    p.add_argument("--target-ds-over-epsilon", type=float, default=1.0)
    p.add_argument("--min-centerline-points", type=int, default=128)
    p.add_argument("--max-centerline-points", type=int, default=8192)
    p.add_argument("--stations", type=int)
    p.add_argument("--angles", type=int)
    p.add_argument("--radial-samples", type=int)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--rho-min", type=float, default=0.002)
    p.add_argument("--rho-max", type=float, default=0.05)
    p.add_argument("--epsilon", type=float, default=0.0045)
    p.add_argument("--kernel-model", choices=KERNEL_MODELS, default="rosenhead_midpoint")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="knot_matrix_out")
    args = p.parse_args()

    settings = dict(PRESETS[args.preset])
    for name in ("centerline_points", "stations", "angles", "radial_samples"):
        value = getattr(args, name)
        if value is not None:
            settings[name] = value

    result = scan_catalog_matrix(
        args.knot_ids,
        centerline_points=settings["centerline_points"],
        adaptive_resolution=args.adaptive_resolution,
        target_ds_over_epsilon=args.target_ds_over_epsilon,
        min_centerline_points=args.min_centerline_points,
        max_centerline_points=args.max_centerline_points,
        stations=settings["stations"],
        angles=settings["angles"],
        radial_samples=settings["radial_samples"],
        scale_over_rc=args.scale_over_rc,
        rho_min=args.rho_min,
        rho_max=args.rho_max,
        epsilon=args.epsilon,
        kernel_model=args.kernel_model,
        auto_build=not args.no_auto_build,
    )
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "knot_matrix.json", result)
    write_csv(out / "knot_matrix.csv", result["rows"])
    for knot_id, pair in result["results"].items():
        write_json(out / f"{knot_id}_primary.json", pair["primary"])
        write_json(out / f"{knot_id}_python.json", pair["python"])

    summary = {
        "knot_ids": result["knot_ids"],
        "native_available_for_all_knots": result["native_available_for_all_knots"],
        "native_python_parity_certified_for_all_knots": result["native_python_parity_certified_for_all_knots"],
        "resolution_target_met_for_all_knots": result["resolution_target_met_for_all_knots"],
        "rows": result["rows"],
    }
    print(json.dumps(summary, indent=2))
    if args.require_native and not result["native_python_parity_certified_for_all_knots"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

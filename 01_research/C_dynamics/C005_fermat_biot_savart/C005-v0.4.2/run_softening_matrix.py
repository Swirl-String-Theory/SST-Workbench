#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots
from fermat_ext.knot_scan import KERNEL_MODELS, scan_softening_matrix

DEFAULT_EPSILONS = [0.0010, 0.0015, 0.0018, 0.00185, 0.0019, 0.00195, 0.0020, 0.0025, 0.0035, 0.0045]
PRESETS = {
    "smoke": dict(stations=2, angles=6, radial_samples=48, target=2.0, max_points=4096),
    "standard": dict(stations=4, angles=12, radial_samples=96, target=1.0, max_points=8192),
    "high": dict(stations=8, angles=24, radial_samples=192, target=0.5, max_points=16384),
}


def main() -> int:
    p = argparse.ArgumentParser(
        description="Adaptive Rosenhead-softening scan over 0_1, 3_1, 4_1, and 5_2."
    )
    p.add_argument("--knot-ids", nargs="+", choices=available_knots(), default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--preset", choices=PRESETS, default="smoke")
    p.add_argument("--epsilon-values", nargs="+", type=float, default=DEFAULT_EPSILONS)
    p.add_argument("--target-ds-over-epsilon", type=float)
    p.add_argument("--min-centerline-points", type=int, default=128)
    p.add_argument("--max-centerline-points", type=int)
    p.add_argument("--stations", type=int)
    p.add_argument("--angles", type=int)
    p.add_argument("--radial-samples", type=int)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--rho-min", type=float, default=0.0005)
    p.add_argument("--rho-max", type=float, default=0.03)
    p.add_argument("--kernel-model", choices=KERNEL_MODELS, default="rosenhead_midpoint")
    p.add_argument("--parity-mode", choices=("full", "spot", "none"), default="spot")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="softening_matrix_out")
    args = p.parse_args()

    preset = PRESETS[args.preset]
    result = scan_softening_matrix(
        args.knot_ids,
        epsilon_values=args.epsilon_values,
        target_ds_over_epsilon=args.target_ds_over_epsilon or preset["target"],
        min_centerline_points=args.min_centerline_points,
        max_centerline_points=args.max_centerline_points or preset["max_points"],
        scale_over_rc=args.scale_over_rc,
        stations=args.stations or preset["stations"],
        angles=args.angles or preset["angles"],
        rho_min=args.rho_min,
        rho_max=args.rho_max,
        radial_samples=args.radial_samples or preset["radial_samples"],
        kernel_model=args.kernel_model,
        parity_mode=args.parity_mode,
        auto_build=not args.no_auto_build,
    )
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "softening_matrix.json", result)
    write_csv(out / "softening_matrix.csv", result["rows"])
    for epsilon_key, knot_results in result["results"].items():
        eps_dir = out / f"epsilon_{epsilon_key.replace('.', 'p')}"
        eps_dir.mkdir(exist_ok=True)
        for knot_id, payload in knot_results.items():
            write_json(eps_dir / f"{knot_id}_primary.json", payload["primary"])
            write_json(eps_dir / f"{knot_id}_parity.json", payload["parity"])
            if payload["python"] is not None:
                write_json(eps_dir / f"{knot_id}_python.json", payload["python"])

    summary = {
        "native_available_for_all_rows": result["native_available_for_all_rows"],
        "native_python_parity_certified_for_checked_rows": result["native_python_parity_certified_for_checked_rows"],
        "resolution_target_met_for_all_rows": result["resolution_target_met_for_all_rows"],
        "row_count": len(result["rows"]),
    }
    print(json.dumps(summary, indent=2))
    if args.require_native:
        if not result["native_available_for_all_rows"]:
            return 2
        if args.parity_mode != "none" and not result["native_python_parity_certified_for_checked_rows"]:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

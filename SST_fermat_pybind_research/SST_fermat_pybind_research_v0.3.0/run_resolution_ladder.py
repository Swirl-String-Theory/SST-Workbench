#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots
from fermat_ext.knot_scan import KERNEL_MODELS, field_convergence_ladder


def main() -> int:
    p = argparse.ArgumentParser(description="Fixed-probe centerline-resolution ladder for all four knot classes.")
    p.add_argument("--knot-ids", nargs="+", choices=available_knots(), default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0045)
    p.add_argument("--point-counts", nargs="+", type=int, default=[512, 1024, 2048, 4096, 8192])
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--stations", type=int, default=2)
    p.add_argument("--angles", type=int, default=8)
    p.add_argument("--rho-min", type=float, default=0.001)
    p.add_argument("--rho-max", type=float, default=0.02)
    p.add_argument("--radial-samples", type=int, default=32)
    p.add_argument("--kernel-model", choices=KERNEL_MODELS, default="rosenhead_midpoint")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="resolution_ladder_out")
    args = p.parse_args()

    result = field_convergence_ladder(
        args.knot_ids,
        epsilon=args.epsilon,
        point_counts=args.point_counts,
        scale_over_rc=args.scale_over_rc,
        stations=args.stations,
        angles=args.angles,
        rho_min=args.rho_min,
        rho_max=args.rho_max,
        radial_samples=args.radial_samples,
        kernel_model=args.kernel_model,
        auto_build=not args.no_auto_build,
    )
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "resolution_ladder.json", result)
    write_csv(out / "resolution_ladder.csv", result["rows"])
    print(json.dumps({
        "native_python_parity_certified_for_all_references": result["native_python_parity_certified_for_all_references"],
        "row_count": len(result["rows"]),
    }, indent=2))
    if args.require_native and not result["native_python_parity_certified_for_all_references"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

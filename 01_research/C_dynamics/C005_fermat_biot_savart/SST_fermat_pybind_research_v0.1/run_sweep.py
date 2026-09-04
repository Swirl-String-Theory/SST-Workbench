#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from fermat_ext.core import sweep_profiles, write_csv, write_json


def floats(value: str) -> list[float]:
    return [float(x.strip()) for x in value.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Sweep resolved core radii for a radial Fermat profile.")
    p.add_argument("--profile", choices=["external", "rankine", "rosenhead", "lamb_oseen"], default="rankine")
    p.add_argument("--a-values", default="0.0038,0.0042,0.0048,0.0052,0.0060")
    p.add_argument("--x-min", type=float, default=1e-5)
    p.add_argument("--x-max", type=float, default=0.1)
    p.add_argument("--samples", type=int, default=4000)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--build-verbose", action="store_true")
    p.add_argument("--out-json", default="fermat_sweep.json")
    p.add_argument("--out-csv", default="fermat_sweep.csv")
    args = p.parse_args()
    rows = sweep_profiles(
        args.profile, floats(args.a_values), x_min=args.x_min, x_max=args.x_max,
        samples=args.samples, force_python=args.force_python,
        auto_build=not args.no_auto_build, force_build=args.force_build,
        build_verbose=args.build_verbose,
    )
    write_json(args.out_json, rows)
    write_csv(args.out_csv, rows)
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.core import PACKAGE_VERSION, sweep_profiles, write_csv, write_json

DEFAULT_PROFILES = ["rankine", "rosenhead", "lamb_oseen"]
DEFAULT_A_VALUES = [0.0010, 0.0015, 0.0018, 0.00185, 0.0019, 0.00195, 0.0020, 0.0025, 0.0035, 0.0045, 0.0060]


def main() -> int:
    p = argparse.ArgumentParser(description="Compare the one-dimensional Rankine, Rosenhead, and Lamb-Oseen Fermat profiles.")
    p.add_argument("--profiles", nargs="+", choices=DEFAULT_PROFILES, default=DEFAULT_PROFILES)
    p.add_argument("--a-values", nargs="+", type=float, default=DEFAULT_A_VALUES)
    p.add_argument("--x-min", type=float, default=1e-5)
    p.add_argument("--x-max", type=float, default=0.1)
    p.add_argument("--samples", type=int, default=8000)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--out-dir", default="profile_matrix_out")
    args = p.parse_args()

    rows = []
    for i, profile in enumerate(args.profiles):
        profile_rows = sweep_profiles(
            profile,
            args.a_values,
            x_min=args.x_min,
            x_max=args.x_max,
            samples=args.samples,
            force_python=args.force_python,
            auto_build=(not args.no_auto_build) if i == 0 else False,
        )
        rows.extend(profile_rows)
    result = {
        "schema": "sst.fermat.profile-matrix.v0.6.1",
        "package_version": PACKAGE_VERSION,
        "status": "RESEARCH_TRACK_RADIAL_PROFILE_COMPARISON",
        "profiles": args.profiles,
        "a_values_over_rc": args.a_values,
        "rows": rows,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "profile_matrix.json", result)
    write_csv(out / "profile_matrix.csv", rows)
    print(json.dumps({"row_count": len(rows), "profiles": args.profiles}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Sweep SST dark-knot Rayleigh diagnostics over ε_BS and Ω."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_dark_knot_harness.core import run_sweep, write_csv, write_json


def parse_float_list(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def parse_str_list(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Run ε_BS/Ω sweep for 3_1 and 4_1 dark-knot diagnostics.")
    p.add_argument("--knots", default="3_1,4_1", help="Comma-separated knot ids.")
    p.add_argument("--omegas", default="0.5,1.0", help="Comma-separated Ω values.")
    p.add_argument("--epsilons", default="0.5,1.0,2.0", help="Comma-separated ε_BS values.")
    p.add_argument("--n", type=int, default=192, help="Vertices per generated knot.")
    p.add_argument("--shell-dr", type=float, default=0.25, help="Radial shell spacing Δr.")
    p.add_argument("--shell-h", type=float, default=0.5, help="Gaussian shell bandwidth h.")
    p.add_argument("--gamma", type=float, default=1.0, help="Circulation Γ.")
    p.add_argument("--proxy-response-gain", type=float, default=0.0, help="Smoke-test only: synthetic response for rocking/breathing columns.")
    p.add_argument("--response-source", default="auto", choices=["auto", "proxy", "ridgerunner", "projected_ridgerunner", "solver", "manual", "unknown"], help="Response provenance label for sweeps with proxy-response-gain.")
    p.add_argument("--force-python", action="store_true", help="Use Python backend only.")
    p.add_argument("--skip-build", action="store_true", help="Skip C++ auto-build.")
    p.add_argument("--force-build", action="store_true", help="Force C++ rebuild.")
    p.add_argument("--build-verbose", action="store_true", help="Verbose build output.")
    p.add_argument("--out-json", default="dark_knot_sweep.json", help="JSON output path.")
    p.add_argument("--out-csv", default="dark_knot_sweep.csv", help="CSV output path.")
    args = p.parse_args()
    rows = run_sweep(
        knot_ids=parse_str_list(args.knots),
        omegas=parse_float_list(args.omegas),
        epsilons=parse_float_list(args.epsilons),
        n=args.n,
        shell_dr=args.shell_dr,
        shell_h=args.shell_h,
        gamma=args.gamma,
        proxy_response_gain=args.proxy_response_gain,
        response_source=args.response_source,
        force_python=args.force_python,
        skip_build=args.skip_build,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
    )
    write_json(args.out_json, rows)
    write_csv(args.out_csv, rows)
    print(json.dumps(rows, indent=2))
    return 0 if all(bool(r.get("ok")) for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

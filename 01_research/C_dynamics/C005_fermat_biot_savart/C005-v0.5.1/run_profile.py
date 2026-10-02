#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from fermat_ext.core import analyze_profile, write_json


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze a radial SST Fermat profile.")
    p.add_argument("--profile", choices=["external", "rankine", "rosenhead", "lamb_oseen"], default="external")
    p.add_argument("--a-core-over-rc", type=float, default=0.0045)
    p.add_argument("--x-min", type=float, default=1e-5)
    p.add_argument("--x-max", type=float, default=0.1)
    p.add_argument("--samples", type=int, default=4000)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--build-verbose", action="store_true")
    p.add_argument("--out", default="")
    p.add_argument("--summary-only", action="store_true")
    args = p.parse_args()
    result = analyze_profile(
        args.profile, args.a_core_over_rc, args.x_min, args.x_max, args.samples,
        force_python=args.force_python, auto_build=not args.no_auto_build,
        force_build=args.force_build, build_verbose=args.build_verbose,
    )
    if args.out:
        write_json(args.out, result)
    if args.summary_only:
        print(f"[{result['classification']}] backend={result['backend']['backend']} roots={len(result['critical_roots'])} horizons={len(result['horizon_roots'])}")
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

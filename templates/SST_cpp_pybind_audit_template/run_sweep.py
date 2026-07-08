#!/usr/bin/env python3
"""Parameter sweep entry point for the SST cpp_pybind audit template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from native_ext.core import run_sweep, write_csv, write_json


def _parse_float_list(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(
        description="Sweep operands for the SST cpp_pybind audit template.",
    )
    p.add_argument("--values-a", default="1.0,2.0,3.0", help="Comma-separated a values.")
    p.add_argument("--values-b", default="0.5,1.5,2.5", help="Comma-separated b values.")
    p.add_argument("--force-python", action="store_true", help="Use Python fallback only.")
    p.add_argument("--skip-build", action="store_true", help="Skip C++ auto-build before sweep.")
    p.add_argument("--force-build", action="store_true", help="Force C++ rebuild before sweep.")
    p.add_argument("--build-verbose", action="store_true", help="Verbose compiler output.")
    p.add_argument("--out-json", default="example_sweep.json", help="JSON output path.")
    p.add_argument("--out-csv", default="example_sweep.csv", help="CSV output path.")
    args = p.parse_args()

    rows = run_sweep(
        _parse_float_list(args.values_a),
        _parse_float_list(args.values_b),
        force_python=args.force_python,
        skip_build=args.skip_build,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
    )

    print(json.dumps(rows, indent=2))
    write_json(args.out_json, rows)
    write_csv(args.out_csv, rows)
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

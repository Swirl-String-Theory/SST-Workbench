#!/usr/bin/env python3
"""Single-run entry point for the SST cpp_pybind audit template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from native_ext.core import run_audit, write_json


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run one SST cpp_pybind audit (template — replace kernel in cpp/ and core.py).",
    )
    p.add_argument("--a", type=float, default=2.0, help="First operand passed to add().")
    p.add_argument("--b", type=float, default=3.0, help="Second operand passed to add().")
    p.add_argument(
        "--expected",
        type=float,
        default=None,
        help="Expected result for pass/fail (default: a + b).",
    )
    p.add_argument(
        "--force-python",
        action="store_true",
        help="Skip C++ extension; use Python fallback only.",
    )
    p.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not attempt to build/load C++ before run (fail fast to fallback).",
    )
    p.add_argument(
        "--force-build",
        action="store_true",
        help="Force C++ rebuild before run (hash stamp ignored).",
    )
    p.add_argument(
        "--build-verbose",
        action="store_true",
        help="Print compiler commands when auto-building.",
    )
    p.add_argument(
        "--out",
        default="",
        help="Optional JSON output path (e.g. example_out.json).",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="Print one-line PASS/FAIL instead of full JSON.",
    )
    args = p.parse_args()

    result = run_audit(
        a=args.a,
        b=args.b,
        expected=args.expected,
        force_python=args.force_python,
        skip_build=args.skip_build,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
    )

    if args.out:
        write_json(args.out, result)

    if args.summary_only:
        status = "PASS" if result["ok"] else "FAIL"
        probe = result["probe"]
        print(
            f"[{status}] {result['audit_name']} — "
            f"backend={probe['backend']} value={probe['value']} expected={result['expected']}"
        )
    else:
        print(json.dumps(result, indent=2))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

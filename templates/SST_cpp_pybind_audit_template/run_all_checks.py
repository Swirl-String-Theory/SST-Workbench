#!/usr/bin/env python3
"""Full check battery for the SST cpp_pybind audit template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from native_ext import _config
from native_ext.core import run_all_checks


def main() -> int:
    default_out = str(_config.default_output_dir())
    p = argparse.ArgumentParser(
        description="Run smoke + sweep checks and write {folder}_outputs/ artifacts.",
    )
    p.add_argument(
        "--out-dir",
        default=default_out,
        help=f"Output directory for JSON/CSV (default: {default_out}).",
    )
    p.add_argument("--force-python", action="store_true", help="Run C++ path checks in Python mode.")
    p.add_argument("--force-build", action="store_true", help="Force C++ rebuild before checks.")
    args = p.parse_args()

    summary = run_all_checks(
        out_dir=args.out_dir,
        force_python=args.force_python,
        force_build=args.force_build,
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

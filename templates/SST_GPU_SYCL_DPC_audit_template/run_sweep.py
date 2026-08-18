#!/usr/bin/env python3
"""Sweep query count M for the GPU Biot-Savart kernel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from native_ext.core import run_sweep, write_csv, write_json


def _parse_int_list(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Sweep query counts for GPU Biot-Savart.")
    p.add_argument("--queries", default="1024,4096,8192", help="Comma-separated M values.")
    p.add_argument("--n-segments", type=int, default=256)
    p.add_argument("--backend", default="auto", choices=["auto", "sycl", "openmp", "python"])
    p.add_argument("--allow-sycl-cpu", action="store_true")
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--skip-build", action="store_true")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--build-verbose", action="store_true")
    p.add_argument("--out-json", default="example_sweep.json")
    p.add_argument("--out-csv", default="example_sweep.csv")
    args = p.parse_args()

    rows = run_sweep(
        _parse_int_list(args.queries),
        n_segments=args.n_segments,
        backend=args.backend,
        allow_sycl_cpu=args.allow_sycl_cpu,
        force_python=args.force_python,
        skip_build=args.skip_build,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
        strict_sycl=args.backend == "sycl" and not args.allow_sycl_cpu,
    )
    print(json.dumps(rows, indent=2, default=str))
    write_json(args.out_json, rows)
    write_csv(args.out_csv, rows)
    return 0 if all(r.get("ok") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Single-run GPU-first Biot-Savart (or --tiny vec_add smoke)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from native_ext.core import run_audit, run_tiny, write_json


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run one SST GPU SYCL/DPC++ audit (default: heavy biot_savart on GPU).",
    )
    p.add_argument("--tiny", action="store_true", help="vec_add smoke instead of Biot-Savart.")
    p.add_argument("--n-segments", type=int, default=512, help="Filament samples N.")
    p.add_argument("--n-queries", type=int, default=8192, help="Query count M (GPU work scales with M*N).")
    p.add_argument("--gamma", type=float, default=1.0)
    p.add_argument("--core", type=float, default=1.0)
    p.add_argument("--backend", default="auto", choices=["auto", "sycl", "openmp", "python"])
    p.add_argument("--allow-sycl-cpu", action="store_true", help="Allow SYCL CPU device when no GPU.")
    p.add_argument("--force-python", action="store_true", help="Skip native; Python fallback only.")
    p.add_argument("--skip-build", action="store_true")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--build-verbose", action="store_true")
    p.add_argument("--out", default="", help="Optional JSON output path.")
    p.add_argument("--summary-only", action="store_true")
    args = p.parse_args()

    strict = args.backend == "sycl" and not args.allow_sycl_cpu
    if args.tiny:
        result = {
            "audit_name": "SST GPU template vec_add smoke",
            "probe": run_tiny(
                backend=args.backend,
                allow_sycl_cpu=args.allow_sycl_cpu,
                force_python=args.force_python,
                skip_build=args.skip_build,
                force_build=args.force_build,
                build_verbose=args.build_verbose,
                strict_sycl=strict,
            ),
        }
        result["ok"] = bool(result["probe"].get("ok"))
    else:
        result = run_audit(
            n_segments=args.n_segments,
            n_queries=args.n_queries,
            gamma=args.gamma,
            core=args.core,
            backend=args.backend,
            allow_sycl_cpu=args.allow_sycl_cpu,
            force_python=args.force_python,
            skip_build=args.skip_build,
            force_build=args.force_build,
            build_verbose=args.build_verbose,
            strict_sycl=strict,
        )

    if args.out:
        write_json(args.out, result)

    if args.summary_only:
        status = "PASS" if result["ok"] else "FAIL"
        probe = result["probe"]
        print(
            f"[{status}] {result['audit_name']} -- "
            f"backend={probe.get('backend')} "
            f"is_gpu={probe.get('is_gpu')} last_ms={probe.get('last_kernel_ms')} "
            f"N={probe.get('n_segments')} M={probe.get('n_queries')}"
        )
    else:
        print(json.dumps(result, indent=2, default=str))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

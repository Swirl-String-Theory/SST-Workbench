#!/usr/bin/env python3
"""
Generate a PROXY V(+Omega), V(-Omega) pair from a V0 centerline CSV.

This is NOT a projected Ridgerunner relaxation. It is only a deterministic
quadrupolar rocking/breathing deformation for smoke-testing the SST dark-knot
Rayleigh harness until real forced-relaxation vertices are available.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np


def _bootstrap_imports():
    here = Path(__file__).resolve().parent
    candidates = [
        here,
        here / "SST_dark_knot_rayleigh_harness",
        Path.cwd(),
        Path.cwd() / "SST_dark_knot_rayleigh_harness",
    ]
    for p in candidates:
        if (p / "sst_dark_knot_harness" / "core.py").exists():
            sys.path.insert(0, str(p))
            return


_bootstrap_imports()

try:
    from sst_dark_knot_harness.core import (
        ROPELENGTH_TARGETS,
        load_vertices_csv,
        normalize_centerline,
        polygon_length,
        proxy_response_vertices,
        resample_closed,
        save_vertices_csv,
    )
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Could not import sst_dark_knot_harness.core. Run this script from the "
        "harness root, or put it next to SST_dark_knot_rayleigh_harness/.\n"
        f"Import error: {exc}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Create PROXY Vplus/Vminus CSV files from a V0 CSV for smoke testing."
    )
    ap.add_argument("input_csv", help="V0 centerline CSV, e.g. V0_4_1.csv")
    ap.add_argument("--knot", default="4_1", help="Knot id, e.g. 4_1 or 3_1")
    ap.add_argument("--omega", type=float, default=1.0, help="Omega used for the sign convention")
    ap.add_argument("--gain", type=float, default=0.02, help="Small deformation gain; try 0.005..0.03")
    ap.add_argument("--n", type=int, default=512, help="Resampled vertex count")
    ap.add_argument("--target-length", type=float, default=None, help="Optional target polygon length")
    ap.add_argument("--out-plus", default="Vplus_4_1.csv")
    ap.add_argument("--out-minus", default="Vminus_4_1.csv")
    ap.add_argument("--report", default="response_pair_proxy_report.json")
    args = ap.parse_args()

    if args.n < 16:
        raise SystemExit("--n must be at least 16")
    if args.gain < 0:
        raise SystemExit("--gain must be nonnegative")

    target = args.target_length
    if target is None:
        target = ROPELENGTH_TARGETS.get(args.knot.lower())

    v0_raw = load_vertices_csv(args.input_csv)
    v0 = normalize_centerline(resample_closed(v0_raw, args.n), target_length=target)
    vplus, vminus, status = proxy_response_vertices(
        v0, args.omega, gain=args.gain, knot_id=args.knot
    )

    # Preserve the same centroid/length convention as V0 after deformation.
    vplus = normalize_centerline(vplus, target_length=polygon_length(v0))
    vminus = normalize_centerline(vminus, target_length=polygon_length(v0))

    save_vertices_csv(args.out_plus, vplus)
    save_vertices_csv(args.out_minus, vminus)

    report = {
        "status": status,
        "warning": "PROXY_ONLY: not a physical projected Ridgerunner relaxation; use only for harness plumbing/smoke tests.",
        "input_csv": str(args.input_csv),
        "out_plus": str(args.out_plus),
        "out_minus": str(args.out_minus),
        "knot": args.knot,
        "omega": args.omega,
        "gain": args.gain,
        "n": args.n,
        "length_v0": polygon_length(v0),
        "length_plus": polygon_length(vplus),
        "length_minus": polygon_length(vminus),
        "max_displacement_plus": float(np.max(np.linalg.norm(vplus - v0, axis=1))),
        "max_displacement_minus": float(np.max(np.linalg.norm(vminus - v0, axis=1))),
        "rms_displacement_plus": float(np.sqrt(np.mean(np.sum((vplus - v0) ** 2, axis=1)))),
        "rms_displacement_minus": float(np.sqrt(np.mean(np.sum((vminus - v0) ** 2, axis=1)))),
    }
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate JS Fourier sampler matches package xyz export."""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "sst_ideal_trefoil_biot_package_v2"))
from sst_trefoil_biot_py import load_ideal_knot, sample_fourier_knot  # noqa: E402

ROOT = Path(__file__).resolve().parent
XYZ = ROOT / "sst_ideal_trefoil_biot_package_v2" / "exports" / "3_1_1_points.xyz"
IDEAL = ROOT / "sst_ideal_trefoil_biot_package_v2" / "ideal.txt"


def main() -> int:
    knot = load_ideal_knot(IDEAL, "3:1:1")
    py_pts = sample_fourier_knot(knot, n=384, endpoint=False)

    xyz_lines = [ln.strip() for ln in XYZ.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    assert len(xyz_lines) == 384, len(xyz_lines)

    max_err = 0.0
    for i, line in enumerate(xyz_lines[:10]):
        x, y, z = map(float, line.split())
        px, py, pz = py_pts[i]
        err = max(abs(x - px), abs(y - py), abs(z - pz))
        max_err = max(max_err, err)
        print(f"pt{i}: max|d|={err:.3e}")

  # full 384
    for i, line in enumerate(xyz_lines):
        x, y, z = map(float, line.split())
        px, py, pz = py_pts[i]
        max_err = max(max_err, abs(x - px), abs(y - py), abs(z - pz))

    print(f"global max_err={max_err:.3e}")
    if max_err > 1e-9:
        print("FAIL: sampler mismatch", file=sys.stderr)
        return 1
    print("OK: Fourier sampler matches 3_1_1_points.xyz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

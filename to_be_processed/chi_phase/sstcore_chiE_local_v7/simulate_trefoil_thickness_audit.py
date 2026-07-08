#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSTcore chi_E run 3: trefoil thickness/ropelength audit.

This is a geometry audit for the embedded ideal.txt representative.  It does not
replace a full ridgerunner/octrope thickness computation; it reports useful proxy
quantities: segment-segment tube clearance, MinRad, and ropelength estimates.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np

from sst_trefoil_biot_py import load_ideal_knot, sample_fourier_knot, closed_polyline_length, write_json, write_csv, save_xyz

SCRIPT_DIR = Path(__file__).resolve().parent
EXPORT_DIR = SCRIPT_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def segment_distance(p1: np.ndarray, q1: np.ndarray, p2: np.ndarray, q2: np.ndarray) -> float:
    """Distance between two closed 3D segments."""
    # Adapted from the standard closest-points-on-segments formula.
    u = q1 - p1
    v = q2 - p2
    w = p1 - p2
    a = float(np.dot(u, u))
    b = float(np.dot(u, v))
    c = float(np.dot(v, v))
    d = float(np.dot(u, w))
    e = float(np.dot(v, w))
    D = a * c - b * b
    SMALL = 1e-15
    sD = D
    tD = D

    if D < SMALL:
        sN = 0.0
        sD = 1.0
        tN = e
        tD = c
    else:
        sN = b * e - c * d
        tN = a * e - b * d
        if sN < 0.0:
            sN = 0.0
            tN = e
            tD = c
        elif sN > sD:
            sN = sD
            tN = e + b
            tD = c

    if tN < 0.0:
        tN = 0.0
        if -d < 0.0:
            sN = 0.0
        elif -d > a:
            sN = sD
        else:
            sN = -d
            sD = a
    elif tN > tD:
        tN = tD
        if (-d + b) < 0.0:
            sN = 0.0
        elif (-d + b) > a:
            sN = sD
        else:
            sN = -d + b
            sD = a

    sc = 0.0 if abs(sN) < SMALL else sN / sD
    tc = 0.0 if abs(tN) < SMALL else tN / tD
    dP = w + sc * u - tc * v
    return float(np.linalg.norm(dP))


def cyclic_separation(i: int, j: int, n: int) -> int:
    d = abs(i - j)
    return min(d, n - d)


def min_segment_distance(points: np.ndarray, skip: int) -> Tuple[float, Tuple[int, int]]:
    p = np.asarray(points, dtype=np.float64)
    n = len(p)
    q = np.roll(p, -1, axis=0)
    best = float("inf")
    best_pair = (-1, -1)
    for i in range(n):
        for j in range(i + 1, n):
            if cyclic_separation(i, j, n) <= skip:
                continue
            d = segment_distance(p[i], q[i], p[j], q[j])
            if d < best:
                best = d
                best_pair = (i, j)
    return best, best_pair


def minrad_values(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=np.float64)
    n = len(p)
    vals = np.empty(n, dtype=np.float64)
    for i in range(n):
        a = p[i] - p[(i - 1) % n]
        b = p[(i + 1) % n] - p[i]
        la = float(np.linalg.norm(a))
        lb = float(np.linalg.norm(b))
        if la <= 0 or lb <= 0:
            vals[i] = 0.0
            continue
        ua = a / la
        ub = b / lb
        # turning angle between incoming tangent and outgoing tangent
        cos_theta = float(np.clip(np.dot(ua, ub), -1.0, 1.0))
        theta = math.acos(cos_theta)
        if theta <= 1e-15:
            vals[i] = float("inf")
        else:
            vals[i] = min(la, lb) / (2.0 * math.tan(theta / 2.0))
    return vals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knot-id", default="3:1:1")
    parser.add_argument("--n", type=int, default=384)
    parser.add_argument("--skip", type=int, default=None, help="cyclic segment skip; default max(3,n//10). This avoids local near-neighbor arcs; use smaller skips for stress testing.")
    args = parser.parse_args()

    t0 = time.time()
    knot = load_ideal_knot(SCRIPT_DIR / "ideal.txt", args.knot_id)
    points = sample_fourier_knot(knot, n=args.n, endpoint=False)
    skip = args.skip if args.skip is not None else max(3, args.n // 10)

    L = closed_polyline_length(points)
    seg_min, seg_pair = min_segment_distance(points, skip=skip)
    seg_min_near, seg_pair_near = min_segment_distance(points, skip=1)
    mr = minrad_values(points)
    finite_mr = mr[np.isfinite(mr)]
    minrad = float(np.min(finite_mr)) if finite_mr.size else float("inf")
    minrad_index = int(np.nanargmin(np.where(np.isfinite(mr), mr, np.nan)))

    thickness_radius_proxy = min(minrad, 0.5 * seg_min)
    length_over_radius_proxy = L / thickness_radius_proxy
    length_over_diameter_proxy = L / (2.0 * thickness_radius_proxy)

    summary = {
        "run": "trefoil_thickness_audit",
        "knot_id": knot.knot_id,
        "conway": knot.conway,
        "declared_L": knot.length_L,
        "declared_D": knot.diameter_D,
        "sample_N": args.n,
        "polyline_L_dim": L,
        "skip_segments": skip,
        "min_segment_distance_dim_skip": seg_min,
        "min_segment_pair_skip": list(seg_pair),
        "min_segment_distance_dim_skip1": seg_min_near,
        "min_segment_pair_skip1": list(seg_pair_near),
        "minrad_min_dim": minrad,
        "minrad_index": minrad_index,
        "thickness_radius_proxy": thickness_radius_proxy,
        "length_over_radius_proxy": length_over_radius_proxy,
        "length_over_diameter_proxy": length_over_diameter_proxy,
        "elapsed_s": time.time() - t0,
        "status": "RESEARCH-TRACK / GEOMETRY AUDIT / NOT A FULL OCTROPE/RIDGERUNNER THICKNESS CERTIFICATE",
        "interpretation": (
            "The ideal.txt L value is diameter-normalized in this package convention. "
            "A rigorous ropelength audit needs a full dcsd/MinRad or octrope-style constraint-thickness computation."
        ),
    }

    minrad_rows = [{"index": int(i), "minrad_dim": float(x)} for i, x in enumerate(mr)]
    write_json(EXPORT_DIR / "trefoil_thickness_audit_summary.json", summary)
    write_csv(EXPORT_DIR / "trefoil_minrad_values.csv", minrad_rows)
    save_xyz(EXPORT_DIR / f"{args.knot_id.replace(':','_')}_thickness_audit_points.xyz", points)

    s = np.linspace(0.0, L, args.n, endpoint=False)
    plt.figure(figsize=(10, 6))
    plt.plot(s, mr, linewidth=1, marker="o", markersize=2, label="MinRad")
    plt.axhline(thickness_radius_proxy, linestyle="--", label="thickness radius proxy")
    plt.xlabel("arclength proxy")
    plt.ylabel("dimensionless radius")
    plt.title("Trefoil thickness audit: MinRad along sampled ideal.txt curve")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plot_path = EXPORT_DIR / "trefoil_thickness_audit.png"
    plt.savefig(plot_path, dpi=180)
    print(f"[*] Plot saved: {plot_path}")

    text_path = EXPORT_DIR / "trefoil_thickness_audit_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST trefoil thickness audit\n")
        f.write("===========================\n")
        for k, v in summary.items():
            f.write(f"{k:36s} = {v}\n")
    print(f"[*] Summary saved: {text_path}")
    print("[*] PASS: trefoil thickness audit completed")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dedicated convergence ladder for the spinor vs director/Hodge Hopf routes."""
from __future__ import annotations

import argparse
import csv
import gc
import math
from pathlib import Path
import sys
import numpy as np

from sst_hopf_common import (
    analytic_hopf_spinor,
    connection_from_spinor,
    curl,
    director_curvature_b_fourth_order,
    divergence,
    gauss_linking_number,
    hodge_project_divergence_free,
    hopf_charge,
    hopf_fiber_curve,
    hopf_map,
    json_dump,
    make_cartesian_grid,
    reconstruct_coulomb_connection,
    relative_l2,
    runtime_provenance,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/director_convergence"))
    p.add_argument("--resolutions", type=int, nargs="+", default=[32, 48, 64, 96, 128])
    p.add_argument("--extent", type=float, default=6.0)
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--fiber-samples", type=int, default=700)
    p.add_argument("--standard-tolerance", type=float, default=0.05)
    p.add_argument("--certified-integer", type=float, default=0.01)
    p.add_argument("--certified-route", type=float, default=0.02)
    p.add_argument("--certified-longitudinal", type=float, default=0.01)
    p.add_argument("--certified-divergence", type=float, default=0.02)
    p.add_argument("--certified-curl", type=float, default=0.02)
    return p.parse_args()


def convergence_order(records: list[dict], key: str) -> float | None:
    pts = [(r["spacing"], r[key]) for r in records if r[key] is not None and r[key] > 0]
    if len(pts) < 3:
        return None
    pts = pts[-3:]
    x = np.log([p[0] for p in pts])
    y = np.log([p[1] for p in pts])
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    resolutions = sorted(set(args.resolutions))
    if len(resolutions) < 3:
        raise ValueError("Use at least three resolutions")

    curve_a = hopf_fiber_curve([0, 0, 1], args.fiber_samples)
    curve_b = hopf_fiber_curve([1, 0, 0], args.fiber_samples)
    linking = gauss_linking_number(curve_a, curve_b)

    records = []
    for n in resolutions:
        x, y, z, grid = make_cartesian_grid(n, args.extent)
        psi = analytic_hopf_spinor(x, y, z, args.scale)
        director = hopf_map(psi)

        a_spin = connection_from_spinor(psi, grid.spacing)
        b_spin = curl(a_spin, grid.spacing)
        q_spin = hopf_charge(a_spin, b_spin, grid.spacing)

        b_raw = director_curvature_b_fourth_order(director, grid.spacing)
        b_perp, b_long, delta_long = hodge_project_divergence_free(b_raw, grid.spacing)
        a_dir = reconstruct_coulomb_connection(b_perp, grid.spacing)
        q_dir = hopf_charge(a_dir, b_perp, grid.spacing)

        rec = {
            "n": n,
            "spacing": grid.spacing,
            "q_spinor": q_spin,
            "q_director": q_dir,
            "linking_number": linking,
            "delta_integer_spinor": abs(q_spin - round(q_spin)),
            "delta_integer_director": abs(q_dir - round(q_dir)),
            "delta_routes": abs(q_spin - q_dir),
            "delta_link_spinor": abs(linking - q_spin),
            "delta_link_director": abs(linking - q_dir),
            "delta_longitudinal": delta_long,
            "delta_div_raw": relative_l2(divergence(b_raw, grid.spacing), b_raw),
            "delta_div_projected": relative_l2(divergence(b_perp, grid.spacing), b_perp),
            "delta_curl_projected": relative_l2(curl(a_dir, grid.spacing) - b_perp, b_perp),
        }
        records.append(rec)
        print(
            f"N={n:4d} Qspin={q_spin:+.8f} Qdir={q_dir:+.8f} "
            f"droute={rec['delta_routes']:.3e} dint={rec['delta_integer_director']:.3e} "
            f"dlong={delta_long:.3e}"
        )
        del x, y, z, psi, director, a_spin, b_spin, b_raw, b_perp, b_long, a_dir
        gc.collect()

    last = records[-1]
    director_standard = all(
        last[k] <= args.standard_tolerance
        for k in ("delta_integer_director", "delta_longitudinal", "delta_div_projected", "delta_curl_projected")
    )
    director_certified = (
        last["delta_integer_director"] <= args.certified_integer
        and last["delta_longitudinal"] <= args.certified_longitudinal
        and last["delta_div_projected"] <= args.certified_divergence
        and last["delta_curl_projected"] <= args.certified_curl
    )
    director_qualification = "CERTIFIED_PASS" if director_certified else ("STANDARD_PASS" if director_standard else "FAIL")

    h1_standard = director_standard and last["delta_routes"] <= args.standard_tolerance and last["delta_integer_spinor"] <= args.standard_tolerance
    h1_certified = director_certified and last["delta_routes"] <= args.certified_route and last["delta_integer_spinor"] <= args.certified_integer
    h1_qualification = "CERTIFIED_PASS" if h1_certified else ("STANDARD_PASS" if h1_standard else "FAIL")

    h3_standard = (
        abs(linking - round(linking)) <= 5e-3
        and last["delta_link_spinor"] <= 0.05
        and last["delta_link_director"] <= 0.05
    )
    h3_certified = (
        abs(linking - round(linking)) <= 1e-3
        and last["delta_link_spinor"] <= 0.01
        and last["delta_link_director"] <= 0.01
    )
    h3_qualification = "CERTIFIED_PASS" if h3_certified else ("STANDARD_PASS" if h3_standard else "FAIL")

    overall_standard = h1_standard and h3_standard
    overall_certified = h1_certified and h3_certified
    qualification = "CERTIFIED_PASS" if overall_certified else ("STANDARD_PASS" if overall_standard else "FAIL")

    payload = {
        "runtime": runtime_provenance(),
        "parameters": {
            "resolutions": resolutions,
            "extent": args.extent,
            "scale": args.scale,
            "fiber_samples": args.fiber_samples,
            "director_derivative_order": 4,
        },
        "linking_number": linking,
        "qualification": qualification,
        "director_reconstruction_qualification": director_qualification,
        "h1_joint_qualification": h1_qualification,
        "h3_qualification": h3_qualification,
        "convergence_orders": {
            "delta_integer_spinor": convergence_order(records, "delta_integer_spinor"),
            "delta_integer_director": convergence_order(records, "delta_integer_director"),
            "delta_routes": convergence_order(records, "delta_routes"),
            "delta_longitudinal": convergence_order(records, "delta_longitudinal"),
            "delta_div_projected": convergence_order(records, "delta_div_projected"),
            "delta_curl_projected": convergence_order(records, "delta_curl_projected"),
        },
        "records": records,
    }
    json_dump(args.output / "director_convergence.json", payload)

    csv_path = args.output / "director_convergence.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"director={director_qualification} H1={h1_qualification} H3={h3_qualification} overall={qualification}")
    print(args.output.resolve())
    return 0 if overall_standard else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

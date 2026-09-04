#!/usr/bin/env python3
"""Step 2: analytic Hopf benchmark for gates H0-H3."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import numpy as np

from sst_hopf_common import (
    analytic_hopf_spinor,
    canonical_array_sha256,
    connection_from_spinor,
    curl,
    director_norm_residual,
    gauss_linking_number,
    gate_record,
    hopf_charge,
    hopf_fiber_curve,
    hopf_map,
    json_dump,
    make_cartesian_grid,
    relative_l2,
    spinor_norm_residual,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/step02_hopf_benchmark"))
    p.add_argument("--resolutions", type=int, nargs="+", default=[24, 32, 48, 64])
    p.add_argument("--extent", type=float, default=6.0)
    p.add_argument("--scale", type=float, default=1.0)
    p.add_argument("--gauge-strength", type=float, default=0.35)
    p.add_argument("--fiber-samples", type=int, default=500)
    p.add_argument("--norm-tolerance", type=float, default=1e-10)
    p.add_argument("--integer-tolerance", type=float, default=0.12)
    p.add_argument("--gauge-tolerance", type=float, default=0.04)
    p.add_argument("--link-tolerance", type=float, default=5e-3)
    return p.parse_args()


def evaluate(n_grid: int, extent: float, scale: float, gauge_strength: float) -> tuple[dict, dict[str, np.ndarray]]:
    x, y, z, grid = make_cartesian_grid(n_grid, extent)
    psi = analytic_hopf_spinor(x, y, z, scale)
    director = hopf_map(psi)
    connection = connection_from_spinor(psi, grid.spacing)
    curvature_b = curl(connection, grid.spacing)
    q = hopf_charge(connection, curvature_b, grid.spacing)

    chi = gauge_strength * x * np.exp(-(x * x + y * y + z * z) / (2.5 * scale) ** 2)
    psi_gauge = psi * np.exp(1j * chi)[..., None]
    connection_gauge = connection_from_spinor(psi_gauge, grid.spacing)
    curvature_gauge = curl(connection_gauge, grid.spacing)
    q_gauge = hopf_charge(connection_gauge, curvature_gauge, grid.spacing)

    record = {
        "n": n_grid,
        "spacing": grid.spacing,
        "q_hopf": q,
        "q_gauge": q_gauge,
        "delta_integer": abs(abs(q) - 1.0),
        "delta_gauge": abs(q_gauge - q),
        "delta_norm_psi": spinor_norm_residual(psi),
        "delta_norm_n": director_norm_residual(director),
        "delta_curvature_gauge": relative_l2(curvature_gauge - curvature_b, curvature_b),
    }
    fields = {
        "psi": psi,
        "director": director,
        "connection": connection,
        "curvature_b": curvature_b,
        "psi_gauge": psi_gauge,
        "spacing": np.array(grid.spacing),
        "extent": np.array(extent),
    }
    return record, fields


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    resolutions = sorted(set(args.resolutions))
    if len(resolutions) < 2:
        raise ValueError("Use at least two resolutions for convergence evidence")

    convergence: list[dict] = []
    highest_fields: dict[str, np.ndarray] | None = None
    for n_grid in resolutions:
        record, fields = evaluate(n_grid, args.extent, args.scale, args.gauge_strength)
        convergence.append(record)
        highest_fields = fields
        print(
            f"N={n_grid:4d} Q={record['q_hopf']:+.8f} "
            f"delta_int={record['delta_integer']:.3e} delta_gauge={record['delta_gauge']:.3e}"
        )

    assert highest_fields is not None
    curve_a = hopf_fiber_curve([0.0, 0.0, 1.0], args.fiber_samples)
    curve_b = hopf_fiber_curve([1.0, 0.0, 0.0], args.fiber_samples)
    linking = gauss_linking_number(curve_a, curve_b)
    final = convergence[-1]
    delta_link = abs(linking - np.sign(final["q_hopf"]))

    h0_pass = final["delta_norm_psi"] < args.norm_tolerance and final["delta_norm_n"] < args.norm_tolerance
    h1_pass = final["delta_integer"] < args.integer_tolerance and convergence[-1]["delta_integer"] < convergence[0]["delta_integer"]
    h2_pass = final["delta_gauge"] < args.gauge_tolerance
    h3_pass = delta_link < args.link_tolerance

    input_hash = canonical_array_sha256(highest_fields["psi"])
    gates = [
        gate_record("H0", "PASS" if h0_pass else "FAIL", "ORTHODOX", {
            "delta_norm_psi": final["delta_norm_psi"], "delta_norm_n": final["delta_norm_n"]
        }, input_sha256=input_hash),
        gate_record("H1", "PASS" if h1_pass else "FAIL", "ORTHODOX", {
            "q_hopf": final["q_hopf"], "delta_integer": final["delta_integer"]
        }, parameters={"resolutions": resolutions, "extent": args.extent}, input_sha256=input_hash),
        gate_record("H2", "PASS" if h2_pass else "FAIL", "ORTHODOX", {
            "q_original": final["q_hopf"], "q_gauge": final["q_gauge"], "delta_gauge": final["delta_gauge"]
        }, input_sha256=input_hash),
        gate_record("H3", "PASS" if h3_pass else "FAIL", "ORTHODOX", {
            "linking_number": linking, "delta_link": delta_link
        }, parameters={"fiber_samples": args.fiber_samples}, input_sha256=input_hash),
    ]

    np.savez_compressed(
        args.output / "analytic_hopf_benchmark.npz",
        **highest_fields,
        curve_a=curve_a,
        curve_b=curve_b,
    )
    json_dump(args.output / "convergence.json", {"records": convergence})
    json_dump(args.output / "H0_H3_evidence.json", {"gates": gates})
    json_dump(args.output / "preimage_linking.json", {"linking_number": linking, "delta_link": delta_link})

    all_pass = all(g["status"] == "PASS" for g in gates)
    print(f"H0-H3 {'PASS' if all_pass else 'FAIL'}; linking={linking:.8f}")
    print(args.output.resolve())
    return 0 if all_pass else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

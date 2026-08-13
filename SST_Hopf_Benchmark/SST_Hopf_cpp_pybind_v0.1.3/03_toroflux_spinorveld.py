#!/usr/bin/env python3
"""Step 3: construct a circular toroflux spinor/director field (H4 candidate)."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import numpy as np

from sst_hopf_common import (
    canonical_array_sha256,
    circular_toroflux_spinor,
    director_norm_residual,
    gate_record,
    hopf_map,
    json_dump,
    make_cartesian_grid,
    runtime_provenance,
    spinor_norm_residual,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/step03_toroflux_spinor"))
    p.add_argument("--n-grid", type=int, default=64)
    p.add_argument("--extent", type=float, default=4.0)
    p.add_argument("--major-radius", type=float, default=2.0)
    p.add_argument("--tube-radius", type=float, default=0.65)
    p.add_argument("--m", type=int, default=1)
    p.add_argument("--n-winding", type=int, default=1)
    p.add_argument("--profile", choices=["regularized", "source"], default="regularized")
    p.add_argument("--tolerance", type=float, default=1e-10)
    p.add_argument("--boundary-tolerance", type=float, default=1e-8)
    p.add_argument("--seam-tolerance", type=float, default=1e-12)
    return p.parse_args()


def boundary_director_residual(n_field: np.ndarray) -> float:
    faces = np.concatenate(
        [
            n_field[0].reshape(-1, 3), n_field[-1].reshape(-1, 3),
            n_field[:, 0].reshape(-1, 3), n_field[:, -1].reshape(-1, 3),
            n_field[:, :, 0].reshape(-1, 3), n_field[:, :, -1].reshape(-1, 3),
        ], axis=0,
    )
    target = np.array([0.0, 0.0, -1.0]) if np.mean(faces[:, 2]) < 0 else np.array([0.0, 0.0, 1.0])
    return float(np.max(np.linalg.norm(faces - target[None, :], axis=1)))


def _ray_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Gauge-minimized spinor distance without loss of precision near overlap=1."""
    overlap = np.sum(np.conj(a) * b, axis=-1)
    magnitude = np.abs(overlap)
    phase = np.ones_like(overlap)
    valid = magnitude > 0.0
    phase[valid] = np.conj(overlap[valid]) / magnitude[valid]
    aligned_b = b * phase[..., None]
    return np.linalg.norm(a - aligned_b, axis=-1)


def seam_endpoint_residuals(m: int, n: int, samples: int = 257) -> tuple[float, float]:
    """Compare exactly identical torus points represented on either side of atan2 branch cuts."""
    beta = np.linspace(0.0, np.pi, samples)
    c = np.cos(beta / 2.0)
    s = np.sin(beta / 2.0)

    # Longitudinal s seam: s=+pi and s=-pi at the same physical point.
    psi_s_plus = np.stack([c * np.exp(1j * m * np.pi), s], axis=-1)
    psi_s_minus = np.stack([c * np.exp(-1j * m * np.pi), s], axis=-1)

    # Cross-section phi seam: phi=+pi and phi=-pi at the same physical point.
    psi_p_plus = np.stack([c, s * np.exp(1j * n * np.pi)], axis=-1)
    psi_p_minus = np.stack([c, s * np.exp(-1j * n * np.pi)], axis=-1)

    director_delta = max(
        float(np.max(np.linalg.norm(hopf_map(psi_s_plus) - hopf_map(psi_s_minus), axis=-1))),
        float(np.max(np.linalg.norm(hopf_map(psi_p_plus) - hopf_map(psi_p_minus), axis=-1))),
    )
    spinor_ray_delta = max(
        float(np.max(_ray_distance(psi_s_plus, psi_s_minus))),
        float(np.max(_ray_distance(psi_p_plus, psi_p_minus))),
    )
    return director_delta, spinor_ray_delta


def main() -> int:
    args = parse_args()
    if args.major_radius <= args.tube_radius:
        raise ValueError("major-radius should exceed tube-radius for a non-self-intersecting circular tube")
    args.output.mkdir(parents=True, exist_ok=True)

    x, y, z, grid = make_cartesian_grid(args.n_grid, args.extent)
    psi, aux = circular_toroflux_spinor(
        x, y, z,
        major_radius=args.major_radius,
        tube_radius=args.tube_radius,
        m=args.m,
        n=args.n_winding,
        profile_orientation=args.profile,
    )
    director = hopf_map(psi)
    delta_psi = spinor_norm_residual(psi)
    delta_n = director_norm_residual(director)
    delta_boundary = boundary_director_residual(director)
    defect_count = int(np.count_nonzero(aux["defects"]))
    axis_singularity = bool(args.profile == "source" and args.n_winding != 0)

    # True branch-cut check at identical physical points, modulo U(1) for the spinor.
    delta_seam_director, delta_seam_spinor_gauge = seam_endpoint_residuals(args.m, args.n_winding)

    # Retain the old grid-neighbor quantity only as a smoothness diagnostic; it is not a seam certificate.
    seam_index = np.argmin(np.abs(np.linspace(-args.extent, args.extent, args.n_grid)))
    seam_a = director[:, seam_index, :, :]
    seam_b = np.roll(director, 1, axis=1)[:, seam_index, :, :]
    seam_grid_neighbor_99pct = float(np.quantile(np.linalg.norm(seam_a - seam_b, axis=-1), 0.99))

    passed = (
        not axis_singularity
        and defect_count == 0
        and delta_psi < args.tolerance
        and delta_n < args.tolerance
        and delta_boundary < args.boundary_tolerance
        and delta_seam_director < args.seam_tolerance
        and delta_seam_spinor_gauge < args.seam_tolerance
    )
    status = "PASS" if passed else ("INDETERMINATE" if axis_singularity else "FAIL")
    field_hash = canonical_array_sha256(psi)

    notes = [
        "This is a circular-torus field ansatz, not a derivation from the SST action.",
        "The director can be compactified even where the spinor differs by a U(1) phase outside the tube.",
        "seam_grid_neighbor_99pct is a local smoothness diagnostic only; H4 is gated by exact branch-cut endpoint tests.",
    ]
    if aux["warning"]:
        notes.append(str(aux["warning"]))

    evidence = gate_record(
        "H4",
        status,
        "SST_ANSATZ",
        {
            "delta_norm_psi": delta_psi,
            "delta_norm_n": delta_n,
            "delta_boundary": delta_boundary,
            "delta_seam_director": delta_seam_director,
            "delta_seam_spinor_gauge": delta_seam_spinor_gauge,
            "seam_grid_neighbor_99pct": seam_grid_neighbor_99pct,
            "defect_count": defect_count,
            "axis_singularity_flag": axis_singularity,
        },
        parameters={
            "grid": grid.to_dict(),
            "major_radius": args.major_radius,
            "tube_radius": args.tube_radius,
            "m": args.m,
            "n": args.n_winding,
            "profile": args.profile,
            "seam_tolerance": args.seam_tolerance,
        },
        notes=notes,
        input_sha256=field_hash,
    )
    evidence["runtime"] = runtime_provenance()

    np.savez_compressed(
        args.output / "toroflux_spinor_field.npz",
        psi=psi,
        director=director,
        spacing=np.array(grid.spacing),
        extent=np.array(grid.extent),
        rho=aux["rho"],
        phi=aux["phi"],
        s=aux["s"],
        beta=aux["beta"],
    )
    json_dump(args.output / "H4_toroflux_evidence.json", evidence)
    json_dump(args.output / "winding_metadata.json", {
        "m": args.m, "n": args.n_winding, "profile": args.profile,
        "field_sha256": field_hash, "status": status,
        "runtime": runtime_provenance(),
    })
    print(
        f"H4 {status}: boundary={delta_boundary:.3e}, "
        f"seam_director={delta_seam_director:.3e}, seam_ray={delta_seam_spinor_gauge:.3e}"
    )
    print(args.output.resolve())
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

#!/usr/bin/env python3
"""Step 1: construct and validate an SST order-parameter candidate (H4).

Default mode is a synthetic, nowhere-zero C² ansatz intended to validate the
pipeline. Use --input-npz with arrays phi1 and phi2 to evaluate an SST-derived
candidate. Passing H4 does not make the spinor a quantum state.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import numpy as np

from sst_hopf_common import (
    canonical_array_sha256,
    director_norm_residual,
    gate_record,
    hopf_map,
    json_dump,
    make_cartesian_grid,
    normalize_spinor,
    spinor_norm_residual,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/step01_order_parameter"))
    p.add_argument("--input-npz", type=Path, help="NPZ containing complex arrays phi1 and phi2")
    p.add_argument("--n", type=int, default=48)
    p.add_argument("--extent", type=float, default=8.0)
    p.add_argument("--scale", type=float, default=2.0)
    p.add_argument("--amplitude", type=float, default=0.45)
    p.add_argument("--twist", type=float, default=1.0)
    p.add_argument("--epsilon-norm", type=float, default=1e-12)
    p.add_argument("--tolerance", type=float, default=1e-10)
    p.add_argument("--boundary-tolerance", type=float, default=5e-3)
    return p.parse_args()


def synthetic_phi(x: np.ndarray, y: np.ndarray, z: np.ndarray, scale: float, amplitude: float, twist: float) -> np.ndarray:
    """Nowhere-zero candidate with fixed director at infinity and Q_H expected 0."""
    r2 = x * x + y * y + z * z
    envelope = np.exp(-0.5 * r2 / scale ** 2)
    phi1 = np.ones_like(x, dtype=np.complex128)
    phi2 = amplitude * ((x + 1j * y) / scale) * envelope * np.exp(1j * twist * z / scale)
    return np.stack([phi1, phi2], axis=-1)


def boundary_residual(n_field: np.ndarray) -> tuple[float, np.ndarray]:
    faces = np.concatenate(
        [
            n_field[0].reshape(-1, 3), n_field[-1].reshape(-1, 3),
            n_field[:, 0].reshape(-1, 3), n_field[:, -1].reshape(-1, 3),
            n_field[:, :, 0].reshape(-1, 3), n_field[:, :, -1].reshape(-1, 3),
        ],
        axis=0,
    )
    mean = np.mean(faces, axis=0)
    mean_norm = np.linalg.norm(mean)
    n_inf = mean / mean_norm if mean_norm > 0 else np.array([0.0, 0.0, 1.0])
    residual = float(np.max(np.linalg.norm(faces - n_inf[None, :], axis=1)))
    return residual, n_inf


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if args.input_npz:
        data = np.load(args.input_npz)
        if not {"phi1", "phi2"}.issubset(data.files):
            raise ValueError("Input NPZ must contain phi1 and phi2")
        phi = np.stack([data["phi1"], data["phi2"]], axis=-1)
        spacing = float(data["spacing"]) if "spacing" in data.files else 1.0
        source = "external_sst_candidate"
        grid_meta = {"shape": list(phi.shape[:-1]), "spacing": spacing}
    else:
        x, y, z, grid = make_cartesian_grid(args.n, args.extent)
        phi = synthetic_phi(x, y, z, args.scale, args.amplitude, args.twist)
        spacing = grid.spacing
        source = "synthetic_pipeline_ansatz"
        grid_meta = grid.to_dict()

    psi, norm2, defects = normalize_spinor(phi, epsilon=args.epsilon_norm)
    n_field = hopf_map(psi)
    min_norm2 = float(np.min(norm2))
    delta_psi = spinor_norm_residual(psi[~defects]) if np.any(~defects) else float("inf")
    delta_n = director_norm_residual(n_field[~defects]) if np.any(~defects) else float("inf")
    delta_boundary, n_inf = boundary_residual(n_field)

    # Local gauge invariance diagnostic.
    shape = phi.shape[:-1]
    index = np.indices(shape, dtype=float)
    chi = 0.17 * np.sin(2.0 * np.pi * index[0] / max(shape[0] - 1, 1))
    gauged = psi * np.exp(1j * chi)[..., None]
    gauge_director_residual = float(np.max(np.abs(hopf_map(gauged) - n_field)))

    passed = (
        min_norm2 > args.epsilon_norm
        and not np.any(defects)
        and delta_psi < args.tolerance
        and delta_n < args.tolerance
        and gauge_director_residual < args.tolerance
        and delta_boundary < args.boundary_tolerance
    )
    status = "PASS" if passed else "FAIL"

    array_hash = canonical_array_sha256(phi)
    evidence = gate_record(
        "H4",
        status,
        "SST_ANSATZ",
        {
            "min_phi_norm_squared": min_norm2,
            "defect_count": int(np.count_nonzero(defects)),
            "delta_norm_psi": delta_psi,
            "delta_norm_n": delta_n,
            "delta_gauge_director": gauge_director_residual,
            "delta_boundary": delta_boundary,
        },
        parameters={
            "source": source,
            "grid": grid_meta,
            "epsilon_norm": args.epsilon_norm,
            "tolerance": args.tolerance,
            "boundary_tolerance": args.boundary_tolerance,
        },
        notes=[
            "H4 validates regularity/compactification of a candidate order parameter only.",
            "The default field is synthetic and is not derived from the SST action.",
        ],
        input_sha256=array_hash,
    )

    np.savez_compressed(
        args.output / "sst_order_parameter.npz",
        phi=phi,
        psi=psi,
        director=n_field,
        norm2=norm2,
        defects=defects,
        spacing=np.array(spacing),
        n_infinity=n_inf,
    )
    json_dump(args.output / "H4_evidence.json", evidence)
    json_dump(
        args.output / "sst_order_parameter.json",
        {"status": status, "source": source, "field_sha256": array_hash, "grid": grid_meta},
    )
    print(f"H4 {status}: min|Phi|^2={min_norm2:.6e}, boundary residual={delta_boundary:.6e}")
    print(args.output.resolve())
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

#!/usr/bin/env python3
"""Step 5: compare Hopf connection/curvature with SST velocity/vorticity (H5)."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import numpy as np

from sst_hopf_common import (
    canonical_array_sha256,
    connection_from_spinor,
    curl,
    gate_record,
    hopf_charge,
    hopf_map,
    json_dump,
    relative_l2,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("field_npz", type=Path, help="NPZ containing psi or connection/curvature fields")
    p.add_argument("--sst-fields", type=Path, help="Optional NPZ with velocity and vorticity arrays")
    p.add_argument("--output", type=Path, default=Path("results/step05_helicity_bridge"))
    p.add_argument("--circulation", type=float, default=1.0)
    p.add_argument("--omega-tolerance", type=float, default=0.05)
    p.add_argument("--helicity-tolerance", type=float, default=0.05)
    p.add_argument("--kappa-tolerance", type=float, default=0.05)
    return p.parse_args()


def load_hopf_fields(path: Path) -> tuple[np.ndarray, np.ndarray, float]:
    data = np.load(path)
    spacing = float(np.asarray(data["spacing"]).item()) if "spacing" in data.files else 1.0
    if "connection" in data.files and "curvature_b" in data.files:
        return data["connection"], data["curvature_b"], spacing
    if "a_director" in data.files and "b_director" in data.files:
        return data["a_director"], data["b_director"], spacing
    if "psi" in data.files:
        a = connection_from_spinor(data["psi"], spacing)
        return a, curl(a, spacing), spacing
    if "director" in data.files:
        raise ValueError("Director-only input should first be processed by step 4")
    raise ValueError("Could not find connection/curvature or psi in field NPZ")


def integrate_dot(a: np.ndarray, b: np.ndarray, spacing: float) -> float:
    return float(np.sum(np.sum(a * b, axis=-1), dtype=np.float64) * spacing ** 3)


def main() -> int:
    args = parse_args()
    if not np.isfinite(args.circulation) or args.circulation == 0:
        raise ValueError("circulation must be finite and nonzero")
    args.output.mkdir(parents=True, exist_ok=True)

    connection, curvature_b, spacing = load_hopf_fields(args.field_npz)
    q_hopf = hopf_charge(connection, curvature_b, spacing)
    expected_kappa = args.circulation / (2.0 * np.pi)

    if args.sst_fields:
        data = np.load(args.sst_fields)
        if not {"velocity", "vorticity"}.issubset(data.files):
            raise ValueError("--sst-fields NPZ must contain velocity and vorticity")
        velocity = np.asarray(data["velocity"], dtype=float)
        vorticity = np.asarray(data["vorticity"], dtype=float)
        source = "independent_sst_fields"
        epistemic = "BRIDGE"
    else:
        velocity = expected_kappa * connection
        vorticity = curl(velocity, spacing)
        source = "constructed_identity_benchmark"
        epistemic = "ORTHODOX"

    denominator = integrate_dot(curvature_b, curvature_b, spacing)
    if abs(denominator) < 1e-30:
        raise ValueError("Hopf curvature norm is too small")
    kappa_star = integrate_dot(vorticity, curvature_b, spacing) / denominator
    delta_omega = relative_l2(vorticity - kappa_star * curvature_b, vorticity)

    helicity_sst = integrate_dot(velocity, vorticity, spacing)
    helicity_target = args.circulation ** 2 * q_hopf
    delta_helicity = abs(helicity_sst - helicity_target) / (
        abs(helicity_sst) + abs(helicity_target) + 1e-15
    )
    delta_kappa = abs(kappa_star - expected_kappa) / (abs(expected_kappa) + 1e-15)

    strong = (
        delta_omega < args.omega_tolerance
        and delta_helicity < args.helicity_tolerance
        and delta_kappa < args.kappa_tolerance
    )
    if source == "constructed_identity_benchmark":
        status = "DEMONSTRATION" if strong else "FAIL"
    else:
        status = "PASS" if strong else "FAIL"

    evidence = gate_record(
        "H5",
        status,
        epistemic,
        {
            "q_hopf": q_hopf,
            "kappa_star": kappa_star,
            "expected_kappa": expected_kappa,
            "delta_kappa": delta_kappa,
            "delta_omega": delta_omega,
            "helicity_sst": helicity_sst,
            "helicity_target": helicity_target,
            "delta_helicity": delta_helicity,
        },
        parameters={
            "source": source,
            "circulation": args.circulation,
            "spacing": spacing,
        },
        notes=[
            "DEMONSTRATION validates the numerical identity only; it does not close the SST bridge.",
            "PASS requires independently supplied SST velocity/vorticity fields.",
        ],
        input_sha256=canonical_array_sha256(curvature_b),
    )

    np.savez_compressed(
        args.output / "helicity_bridge_fields.npz",
        connection=connection,
        curvature_b=curvature_b,
        velocity=velocity,
        vorticity=vorticity,
        spacing=np.array(spacing),
    )
    json_dump(args.output / "H5_evidence.json", evidence)
    json_dump(args.output / "helicity_bridge_summary.json", {
        "source": source,
        "status": status,
        "q_hopf": q_hopf,
        "helicity_sst": helicity_sst,
        "helicity_target": helicity_target,
    })
    print(f"H5 {status}: delta_omega={delta_omega:.3e}, delta_H={delta_helicity:.3e}")
    print(args.output.resolve())
    return 0 if status in {"PASS", "DEMONSTRATION"} else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

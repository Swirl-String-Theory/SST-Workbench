#!/usr/bin/env python3
"""Step 7: SU(2) 2π/4π diagnostic and optional H9 certificate aggregation.

The numerical spinor path demonstrates the double cover SU(2)->SO(3). It does
not by itself prove the topology of the SST configuration space. H9 remains
INDETERMINATE unless an external Finkelstein-Rubinstein/configuration-space
certificate is supplied.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys
import numpy as np

from sst_hopf_common import (
    canonical_array_sha256,
    gate_record,
    hopf_map,
    json_dump,
    ray_distance,
    su2_rotation,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/step07_four_pi"))
    p.add_argument("--samples", type=int, default=1001)
    p.add_argument("--axis", type=float, nargs=3, default=[0.0, 0.0, 1.0])
    p.add_argument("--initial-spinor", type=float, nargs=4, metavar=("RE1", "IM1", "RE2", "IM2"), default=[1.0, 0.0, 0.0, 0.0])
    p.add_argument("--fr-certificate", type=Path, help="JSON with two_pi_nontrivial, four_pi_trivial, method")
    p.add_argument("--tolerance", type=float, default=1e-10)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.samples < 5:
        raise ValueError("samples must be >= 5")

    psi0 = np.array([
        args.initial_spinor[0] + 1j * args.initial_spinor[1],
        args.initial_spinor[2] + 1j * args.initial_spinor[3],
    ], dtype=np.complex128)
    norm = np.linalg.norm(psi0)
    if norm == 0:
        raise ValueError("initial spinor must be nonzero")
    psi0 /= norm

    angles = np.linspace(0.0, 4.0 * np.pi, args.samples)
    spinors = np.stack([su2_rotation(args.axis, angle) @ psi0 for angle in angles], axis=0)
    directors = hopf_map(spinors)

    i_2pi = int(np.argmin(np.abs(angles - 2.0 * np.pi)))
    i_4pi = -1
    raw_2pi = float(np.linalg.norm(spinors[i_2pi] - psi0))
    raw_4pi = float(np.linalg.norm(spinors[i_4pi] - psi0))
    minus_2pi = float(np.linalg.norm(spinors[i_2pi] + psi0))
    ray_2pi = ray_distance(spinors[i_2pi], psi0)
    director_2pi = float(np.linalg.norm(directors[i_2pi] - directors[0]))
    director_4pi = float(np.linalg.norm(directors[i_4pi] - directors[0]))

    algebraic_pass = (
        minus_2pi < args.tolerance
        and raw_4pi < args.tolerance
        and director_2pi < args.tolerance
        and director_4pi < args.tolerance
    )

    notes = [
        "The SU(2) path demonstrates spinor double-cover kinematics only.",
        "H9 requires a theorem/certificate about the physical SST configuration space.",
    ]
    certificate_data: dict = {}
    if args.fr_certificate:
        certificate_data = json.loads(args.fr_certificate.read_text(encoding="utf-8"))
        two_nontrivial = bool(certificate_data.get("two_pi_nontrivial", False))
        four_trivial = bool(certificate_data.get("four_pi_trivial", False))
        method = str(certificate_data.get("method", ""))
        complete = bool(method.strip())
        status = "PASS" if algebraic_pass and two_nontrivial and four_trivial and complete else "FAIL"
        notes.append("H9 status incorporates the externally supplied certificate; the script does not independently prove it.")
    else:
        status = "INDETERMINATE" if algebraic_pass else "FAIL"

    path_hash = canonical_array_sha256(spinors)
    h9 = gate_record(
        "H9",
        status,
        "OPEN_THEOREM_TARGET",
        {
            "raw_distance_2pi": raw_2pi,
            "distance_to_minus_initial_2pi": minus_2pi,
            "ray_distance_2pi": ray_2pi,
            "raw_distance_4pi": raw_4pi,
            "director_distance_2pi": director_2pi,
            "director_distance_4pi": director_4pi,
            "algebraic_double_cover_pass": algebraic_pass,
        },
        parameters={"axis": args.axis, "samples": args.samples, "certificate": certificate_data},
        notes=notes,
        input_sha256=path_hash,
    )

    np.savez_compressed(
        args.output / "four_pi_path.npz",
        angles=angles,
        spinors=spinors,
        directors=directors,
    )
    json_dump(args.output / "H9_evidence.json", h9)
    json_dump(args.output / "four_pi_summary.json", {
        "status": status,
        "algebraic_double_cover_pass": algebraic_pass,
        "raw_2pi": raw_2pi,
        "minus_2pi": minus_2pi,
        "raw_4pi": raw_4pi,
    })
    print(f"H9 {status}: ||psi(2pi)+psi0||={minus_2pi:.3e}, ||psi(4pi)-psi0||={raw_4pi:.3e}")
    print(args.output.resolve())
    return 0 if status in {"PASS", "INDETERMINATE"} and algebraic_pass else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

#!/usr/bin/env python3
"""Step 4: compute Hopf charge by spinor, director/FFT and preimage routes."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import numpy as np

from sst_hopf_common import (
    canonical_array_sha256,
    connection_from_spinor,
    curl,
    director_curvature_b,
    divergence,
    gauss_linking_number,
    gate_record,
    hopf_charge,
    hopf_map,
    json_dump,
    reconstruct_coulomb_connection,
    relative_l2,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="NPZ from step 1, 2 or 3")
    p.add_argument("--output", type=Path, default=Path("results/step04_hopf_charge"))
    p.add_argument("--integer-tolerance", type=float, default=0.20)
    p.add_argument("--route-tolerance", type=float, default=0.20)
    p.add_argument("--divergence-tolerance", type=float, default=0.20)
    p.add_argument("--curl-tolerance", type=float, default=0.20)
    p.add_argument("--link-tolerance", type=float, default=0.20)
    return p.parse_args()


def load_fields(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    out = {name: data[name] for name in data.files}
    if "psi" not in out and "phi" in out:
        raise ValueError("Input has phi but no normalized psi; run step 1 first")
    if "psi" not in out and "director" not in out:
        raise ValueError("Input must contain psi or director")
    if "director" not in out:
        out["director"] = hopf_map(out["psi"])
    if "spacing" not in out:
        raise ValueError("Input NPZ must contain spacing")
    return out


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fields = load_fields(args.input)
    spacing = float(np.asarray(fields["spacing"]).item())
    director = np.asarray(fields["director"], dtype=float)
    input_hash = canonical_array_sha256(director)

    # Route A: native spinor connection if available.
    q_spinor = None
    a_spinor = None
    b_spinor = None
    if "psi" in fields:
        psi = np.asarray(fields["psi"], dtype=np.complex128)
        a_spinor = connection_from_spinor(psi, spacing)
        b_spinor = curl(a_spinor, spacing)
        q_spinor = hopf_charge(a_spinor, b_spinor, spacing)

    # Route B: director curvature and Coulomb-gauge reconstruction.
    b_director = director_curvature_b(director, spacing)
    a_director = reconstruct_coulomb_connection(b_director, spacing)
    q_director = hopf_charge(a_director, b_director, spacing)
    delta_div = relative_l2(divergence(b_director, spacing), b_director)
    delta_curl = relative_l2(curl(a_director, spacing) - b_director, b_director)
    delta_integer = abs(q_director - round(q_director))
    delta_routes = abs(q_spinor - q_director) if q_spinor is not None else None

    # Route C: analytic or extracted preimage curves when present.
    linking = None
    delta_link = None
    if "curve_a" in fields and "curve_b" in fields:
        linking = gauss_linking_number(fields["curve_a"], fields["curve_b"])
        delta_link = abs(linking - q_director)

    h1_pass = (
        delta_integer < args.integer_tolerance
        and delta_div < args.divergence_tolerance
        and delta_curl < args.curl_tolerance
        and (delta_routes is None or delta_routes < args.route_tolerance)
    )
    h2_status = "INDETERMINATE"
    h2_notes = ["Gauge invariance requires at least two gauge-related input fields; step 2 performs that test."]
    h3_status = "INDETERMINATE" if linking is None else ("PASS" if delta_link is not None and delta_link < args.link_tolerance else "FAIL")

    h1 = gate_record(
        "H1", "PASS" if h1_pass else "FAIL", "ORTHODOX",
        {
            "q_spinor": q_spinor if q_spinor is not None else 0.0,
            "q_director": q_director,
            "delta_integer": delta_integer,
            "delta_routes": delta_routes if delta_routes is not None else 0.0,
            "delta_div": delta_div,
            "delta_curl": delta_curl,
        },
        parameters={"spacing": spacing, "input": str(args.input)},
        input_sha256=input_hash,
        notes=["q_spinor=0 with route absent is represented in residuals but route availability is recorded separately."],
    )
    h2 = gate_record("H2", h2_status, "ORTHODOX", {}, input_sha256=input_hash, notes=h2_notes)
    h3 = gate_record(
        "H3", h3_status, "ORTHODOX",
        {"linking_number": linking if linking is not None else 0.0, "delta_link": delta_link if delta_link is not None else 0.0},
        input_sha256=input_hash,
        notes=[] if linking is not None else ["No curve_a/curve_b present in input NPZ."],
    )

    np.savez_compressed(
        args.output / "hopf_charge_fields.npz",
        director=director,
        a_director=a_director,
        b_director=b_director,
        a_spinor=a_spinor if a_spinor is not None else np.empty((0,)),
        b_spinor=b_spinor if b_spinor is not None else np.empty((0,)),
        spacing=np.array(spacing),
    )
    json_dump(args.output / "hopf_charge_spinor.json", {
        "available": q_spinor is not None, "q_hopf": q_spinor if q_spinor is not None else 0.0
    })
    json_dump(args.output / "hopf_charge_director.json", {
        "q_hopf": q_director, "delta_integer": delta_integer,
        "delta_div": delta_div, "delta_curl": delta_curl,
    })
    json_dump(args.output / "preimage_linking.json", {
        "available": linking is not None,
        "linking_number": linking if linking is not None else 0.0,
        "delta_link": delta_link if delta_link is not None else 0.0,
    })
    json_dump(args.output / "H1_H3_evidence.json", {
        "route_availability": {"spinor": q_spinor is not None, "director": True, "preimage": linking is not None},
        "gates": [h1, h2, h3],
    })

    print(f"H1 {h1['status']}: Q_director={q_director:+.8f}, Q_spinor={q_spinor}")
    print(f"H3 {h3_status}: linking={linking}")
    print(args.output.resolve())
    return 0 if h1_pass and h3_status != "FAIL" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

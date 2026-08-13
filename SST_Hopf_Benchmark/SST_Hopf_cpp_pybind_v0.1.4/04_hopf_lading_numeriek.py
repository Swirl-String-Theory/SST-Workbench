#!/usr/bin/env python3
"""Step 4: Hopf charge by spinor, director/Hodge and preimage routes with certification tiers."""
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
    director_curvature_b_fourth_order,
    divergence,
    gauss_linking_number,
    gate_record,
    hodge_project_divergence_free,
    hopf_charge,
    hopf_map,
    json_dump,
    reconstruct_coulomb_connection,
    relative_l2,
    runtime_provenance,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="NPZ from step 1, 2 or 3")
    p.add_argument("--output", type=Path, default=Path("results/step04_hopf_charge"))
    p.add_argument("--director-order", type=int, choices=[2, 4], default=4)

    # STANDARD_PASS: routine convergence evidence, not a final topological certificate.
    p.add_argument("--standard-integer-tolerance", type=float, default=0.05)
    p.add_argument("--standard-route-tolerance", type=float, default=0.05)
    p.add_argument("--standard-longitudinal-tolerance", type=float, default=0.05)
    p.add_argument("--standard-divergence-tolerance", type=float, default=0.05)
    p.add_argument("--standard-curl-tolerance", type=float, default=0.05)
    p.add_argument("--standard-link-integer-tolerance", type=float, default=5e-3)
    p.add_argument("--standard-link-spinor-tolerance", type=float, default=0.05)
    p.add_argument("--standard-link-director-tolerance", type=float, default=0.05)

    # CERTIFIED_PASS: deliberately stricter; expected to require high resolution.
    p.add_argument("--certified-integer-tolerance", type=float, default=0.01)
    p.add_argument("--certified-route-tolerance", type=float, default=0.02)
    p.add_argument("--certified-longitudinal-tolerance", type=float, default=0.01)
    p.add_argument("--certified-divergence-tolerance", type=float, default=0.02)
    p.add_argument("--certified-curl-tolerance", type=float, default=0.02)
    p.add_argument("--certified-link-integer-tolerance", type=float, default=1e-3)
    p.add_argument("--certified-link-spinor-tolerance", type=float, default=0.01)
    p.add_argument("--certified-link-director-tolerance", type=float, default=0.01)
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


def _qualify(metrics: dict[str, float], standard: dict[str, float], certified: dict[str, float]) -> str:
    if all(metrics[k] <= certified[k] for k in certified):
        return "CERTIFIED_PASS"
    if all(metrics[k] <= standard[k] for k in standard):
        return "STANDARD_PASS"
    return "FAIL"


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fields = load_fields(args.input)
    spacing = float(np.asarray(fields["spacing"]).item())
    director = np.asarray(fields["director"], dtype=float)
    input_hash = canonical_array_sha256(director)

    # Route A: direct spinor connection.
    q_spinor = None
    a_spinor = None
    b_spinor = None
    if "psi" in fields:
        psi = np.asarray(fields["psi"], dtype=np.complex128)
        a_spinor = connection_from_spinor(psi, spacing)
        b_spinor = curl(a_spinor, spacing)
        q_spinor = hopf_charge(a_spinor, b_spinor, spacing)

    # Route B: director curvature -> explicit Hodge projection -> Coulomb reconstruction.
    curvature_fn = director_curvature_b_fourth_order if args.director_order == 4 else director_curvature_b
    b_director_raw = curvature_fn(director, spacing)
    b_director, b_longitudinal, delta_longitudinal = hodge_project_divergence_free(b_director_raw, spacing)
    a_director = reconstruct_coulomb_connection(b_director, spacing)

    q_director = hopf_charge(a_director, b_director, spacing)
    q_director_raw_pairing = hopf_charge(a_director, b_director_raw, spacing)
    delta_div_raw = relative_l2(divergence(b_director_raw, spacing), b_director_raw)
    delta_div_projected = relative_l2(divergence(b_director, spacing), b_director)
    delta_curl_projected = relative_l2(curl(a_director, spacing) - b_director, b_director)
    delta_integer_director = abs(q_director - round(q_director))
    delta_integer_spinor = abs(q_spinor - round(q_spinor)) if q_spinor is not None else None
    delta_routes = abs(q_spinor - q_director) if q_spinor is not None else None

    director_metrics = {
        "integer_director": delta_integer_director,
        "longitudinal": delta_longitudinal,
        "divergence": delta_div_projected,
        "curl": delta_curl_projected,
    }
    standard_director = {
        "integer_director": args.standard_integer_tolerance,
        "longitudinal": args.standard_longitudinal_tolerance,
        "divergence": args.standard_divergence_tolerance,
        "curl": args.standard_curl_tolerance,
    }
    certified_director = {
        "integer_director": args.certified_integer_tolerance,
        "longitudinal": args.certified_longitudinal_tolerance,
        "divergence": args.certified_divergence_tolerance,
        "curl": args.certified_curl_tolerance,
    }
    director_qualification = _qualify(director_metrics, standard_director, certified_director)

    h1_metrics = dict(director_metrics)
    standard_h1 = dict(standard_director)
    certified_h1 = dict(certified_director)
    if delta_routes is not None:
        h1_metrics["route"] = delta_routes
        standard_h1["route"] = args.standard_route_tolerance
        certified_h1["route"] = args.certified_route_tolerance
    if delta_integer_spinor is not None:
        h1_metrics["integer_spinor"] = delta_integer_spinor
        standard_h1["integer_spinor"] = args.standard_integer_tolerance
        certified_h1["integer_spinor"] = args.certified_integer_tolerance

    h1_qualification = _qualify(h1_metrics, standard_h1, certified_h1)
    h1_pass = h1_qualification != "FAIL"

    # Route C: independent preimage linking.
    linking = None
    delta_link_integer = None
    delta_link_spinor = None
    delta_link_director = None
    if "curve_a" in fields and "curve_b" in fields:
        linking = gauss_linking_number(fields["curve_a"], fields["curve_b"])
        delta_link_integer = abs(linking - round(linking))
        delta_link_spinor = abs(linking - q_spinor) if q_spinor is not None else None
        delta_link_director = abs(linking - q_director)

    if linking is None:
        h3_qualification = "INDETERMINATE"
        h3_pass = True
    else:
        standard_h3 = {
            "link_integer": args.standard_link_integer_tolerance,
            "link_director": args.standard_link_director_tolerance,
        }
        certified_h3 = {
            "link_integer": args.certified_link_integer_tolerance,
            "link_director": args.certified_link_director_tolerance,
        }
        h3_metrics = {
            "link_integer": float(delta_link_integer),
            "link_director": float(delta_link_director),
        }
        if delta_link_spinor is not None:
            h3_metrics["link_spinor"] = float(delta_link_spinor)
            standard_h3["link_spinor"] = args.standard_link_spinor_tolerance
            certified_h3["link_spinor"] = args.certified_link_spinor_tolerance
        h3_qualification = _qualify(h3_metrics, standard_h3, certified_h3)
        h3_pass = h3_qualification != "FAIL"

    h1 = gate_record(
        "H1", "PASS" if h1_pass else "FAIL", "ORTHODOX",
        {
            "q_spinor": q_spinor,
            "q_director_projected": q_director,
            "q_director_raw_pairing": q_director_raw_pairing,
            "delta_integer_spinor": delta_integer_spinor,
            "delta_integer_director": delta_integer_director,
            "delta_routes": delta_routes,
            "delta_longitudinal": delta_longitudinal,
            "delta_div_raw": delta_div_raw,
            "delta_div_projected": delta_div_projected,
            "delta_curl_projected": delta_curl_projected,
        },
        parameters={
            "spacing": spacing,
            "input": str(args.input),
            "director_derivative_order": args.director_order,
        },
        input_sha256=input_hash,
        notes=[
            "STANDARD_PASS is routine convergence evidence; CERTIFIED_PASS uses stricter thresholds.",
            "The Hodge projection is explicit and delta_longitudinal reports the removed longitudinal component.",
        ],
    )
    h1["qualification"] = h1_qualification
    h1["director_reconstruction_qualification"] = director_qualification
    h1["thresholds"] = {"standard": standard_h1, "certified": certified_h1}
    h1["runtime"] = runtime_provenance()

    h2 = gate_record(
        "H2", "INDETERMINATE", "ORTHODOX", {}, input_sha256=input_hash,
        notes=["Gauge invariance requires at least two gauge-related input fields; step 2 performs that test."],
    )
    h2["runtime"] = runtime_provenance()

    h3 = gate_record(
        "H3",
        "INDETERMINATE" if linking is None else ("PASS" if h3_pass else "FAIL"),
        "ORTHODOX",
        {
            "linking_number": linking,
            "delta_link_integer": delta_link_integer,
            "delta_link_spinor": delta_link_spinor,
            "delta_link_director": delta_link_director,
        },
        input_sha256=input_hash,
        notes=[] if linking is not None else ["No curve_a/curve_b present in input NPZ."],
    )
    h3["qualification"] = h3_qualification
    h3["runtime"] = runtime_provenance()

    np.savez_compressed(
        args.output / "hopf_charge_fields.npz",
        director=director,
        a_director=a_director,
        b_director=b_director,
        b_director_raw=b_director_raw,
        b_longitudinal=b_longitudinal,
        a_spinor=a_spinor if a_spinor is not None else np.empty((0,)),
        b_spinor=b_spinor if b_spinor is not None else np.empty((0,)),
        spacing=np.array(spacing),
    )
    json_dump(args.output / "hopf_charge_spinor.json", {
        "available": q_spinor is not None,
        "q_hopf": q_spinor,
        "delta_integer": delta_integer_spinor,
        "runtime": runtime_provenance(),
    })
    json_dump(args.output / "hopf_charge_director.json", {
        "q_hopf": q_director,
        "q_hopf_raw_pairing": q_director_raw_pairing,
        "delta_integer": delta_integer_director,
        "delta_longitudinal": delta_longitudinal,
        "delta_div_raw": delta_div_raw,
        "delta_div_projected": delta_div_projected,
        "delta_curl_projected": delta_curl_projected,
        "director_derivative_order": args.director_order,
        "qualification": h1_qualification,
        "director_reconstruction_qualification": director_qualification,
        "runtime": runtime_provenance(),
    })
    json_dump(args.output / "preimage_linking.json", {
        "available": linking is not None,
        "linking_number": linking,
        "delta_link_integer": delta_link_integer,
        "delta_link_spinor": delta_link_spinor,
        "delta_link_director": delta_link_director,
        "qualification": h3_qualification,
    })
    json_dump(args.output / "H1_H3_evidence.json", {
        "route_availability": {"spinor": q_spinor is not None, "director": True, "preimage": linking is not None},
        "runtime": runtime_provenance(),
        "gates": [h1, h2, h3],
    })

    print(
        f"H1 {h1_qualification}: Q_director={q_director:+.8f}, "
        f"Q_spinor={q_spinor}, d_long={delta_longitudinal:.3e}, d_route={delta_routes}"
    )
    print(f"H3 {h3_qualification}: linking={linking}")
    print(args.output.resolve())
    return 0 if h1_pass and h3_pass else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

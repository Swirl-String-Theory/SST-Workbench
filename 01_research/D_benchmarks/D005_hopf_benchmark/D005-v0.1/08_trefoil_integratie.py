#!/usr/bin/env python3
"""Step 8: trefoil geometry, framing and H10 evidence integration.

The default parametric T(2,3) curve is a known candidate, not an independent
knot certificate. H10 can PASS only when external knot/Hopf evidence is supplied
and the required upstream gates are closed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys
import numpy as np

from sst_hopf_common import (
    bishop_frame,
    canonical_array_sha256,
    frame_twist,
    gate_record,
    json_dump,
    polygonal_writhe,
    structured_tube_spinor,
    torus_knot_centerline,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/step08_trefoil"))
    p.add_argument("--centerline", type=Path, help="Optional NPZ/NPY; NPZ must contain centerline")
    p.add_argument("--samples", type=int, default=400)
    p.add_argument("--major-radius", type=float, default=2.0)
    p.add_argument("--minor-radius", type=float, default=0.7)
    p.add_argument("--tube-radius", type=float, default=0.22)
    p.add_argument("--radial-samples", type=int, default=8)
    p.add_argument("--angular-samples", type=int, default=24)
    p.add_argument("--m", type=int, default=1)
    p.add_argument("--n-winding", type=int, default=1)
    p.add_argument("--knot-certificate", type=Path, help="JSON with status PASS, knot_type 3_1 and provenance_complete")
    p.add_argument("--hopf-evidence", type=Path, help="H1/H3 evidence JSON")
    p.add_argument("--helicity-evidence", type=Path, help="H5 evidence JSON")
    p.add_argument("--spin-evidence", type=Path, help="H6-H9 evidence JSON or aggregate")
    p.add_argument("--event-ledger", type=Path, help="Optional JSON event ledger")
    return p.parse_args()


def read_json(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_centerline(args: argparse.Namespace) -> tuple[np.ndarray, str]:
    if args.centerline is None:
        return torus_knot_centerline(2, 3, args.samples, args.major_radius, args.minor_radius), "parametric_T_2_3_candidate"
    if args.centerline.suffix.lower() == ".npy":
        curve = np.load(args.centerline)
    else:
        data = np.load(args.centerline)
        if "centerline" not in data.files:
            raise ValueError("Centerline NPZ must contain centerline")
        curve = data["centerline"]
    curve = np.asarray(curve, dtype=float)
    if curve.ndim != 2 or curve.shape[1] != 3 or len(curve) < 20:
        raise ValueError("Centerline must have shape (N,3), N>=20")
    return curve, "external_centerline"


def extract_gate_status(payload: dict, gate: str) -> str | None:
    if payload.get("gate") == gate:
        return payload.get("status")
    for item in payload.get("gates", []):
        if item.get("gate") == gate:
            return item.get("status")
    for value in payload.values():
        if isinstance(value, dict):
            found = extract_gate_status(value, gate)
            if found:
                return found
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found = extract_gate_status(item, gate)
                    if found:
                        return found
    return None


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    curve, source = load_centerline(args)
    tangent, e1, e2 = bishop_frame(curve)
    writhe = polygonal_writhe(curve)
    twist = frame_twist(tangent, e1)
    self_link_proxy = writhe + twist

    positions, psi_tube, director_tube = structured_tube_spinor(
        curve, e1, e2,
        radial_samples=args.radial_samples,
        angular_samples=args.angular_samples,
        tube_radius=args.tube_radius,
        m=args.m,
        n=args.n_winding,
    )

    knot_cert = read_json(args.knot_certificate)
    hopf_ev = read_json(args.hopf_evidence)
    helicity_ev = read_json(args.helicity_evidence)
    spin_ev = read_json(args.spin_evidence)
    ledger = read_json(args.event_ledger)

    knot_pass = (
        knot_cert.get("status") == "PASS"
        and str(knot_cert.get("knot_type")) in {"3_1", "T(2,3)", "trefoil"}
        and bool(knot_cert.get("provenance_complete", False))
    )
    h1 = extract_gate_status(hopf_ev, "H1")
    h3 = extract_gate_status(hopf_ev, "H3")
    h5 = extract_gate_status(helicity_ev, "H5")
    upstream = {gate: extract_gate_status(spin_ev, gate) for gate in ["H6", "H7", "H8", "H9"]}
    ledger_consistent = bool(ledger.get("consistent", False)) if ledger else False

    required_closed = knot_pass and h1 == "PASS" and h3 == "PASS" and h5 == "PASS" and all(upstream[g] == "PASS" for g in upstream) and ledger_consistent
    any_explicit_failure = (
        knot_cert.get("status") == "FAIL"
        or h1 == "FAIL" or h3 == "FAIL" or h5 == "FAIL"
        or any(value == "FAIL" for value in upstream.values())
        or (ledger and not ledger_consistent)
    )
    status = "PASS" if required_closed else ("FAIL" if any_explicit_failure else "INDETERMINATE")

    curve_hash = canonical_array_sha256(curve)
    h10 = gate_record(
        "H10",
        status,
        "OPEN_THEOREM_TARGET",
        {
            "writhe": writhe,
            "bishop_frame_twist": twist,
            "self_link_proxy": self_link_proxy,
            "knot_certificate_pass": knot_pass,
            "H1": h1 or "MISSING",
            "H3": h3 or "MISSING",
            "H5": h5 or "MISSING",
            **upstream,
            "event_ledger_consistent": ledger_consistent,
        },
        parameters={
            "source": source,
            "samples": len(curve),
            "tube_radius": args.tube_radius,
            "m": args.m,
            "n": args.n_winding,
        },
        notes=[
            "The default parametric trefoil is not an independent knot certificate.",
            "Knot type K and Hopf charge Q_H remain separate invariants.",
            "H10 PASS requires external certification and all upstream gates H1/H3/H5-H9 PASS.",
        ],
        input_sha256=curve_hash,
    )

    np.savez_compressed(
        args.output / "trefoil_geometry_and_tube.npz",
        centerline=curve,
        tangent=tangent,
        e1=e1,
        e2=e2,
        tube_positions=positions,
        tube_spinor=psi_tube,
        tube_director=director_tube,
    )
    json_dump(args.output / "trefoil_invariants.json", {
        "candidate_knot_type": "3_1",
        "independently_certified": knot_pass,
        "writhe": writhe,
        "twist": twist,
        "self_link_proxy": self_link_proxy,
        "centerline_sha256": curve_hash,
    })
    json_dump(args.output / "H10_evidence.json", h10)
    json_dump(args.output / "event_ledger_template.json", ledger or {
        "consistent": False,
        "events": [],
        "required_fields": ["time", "event_type", "K_before", "K_after", "QH_before", "QH_after", "helicity_change"],
    })

    print(f"H10 {status}: Wr={writhe:+.6f}, Tw={twist:+.6f}, SL~={self_link_proxy:+.6f}")
    print(args.output.resolve())
    return 0 if status in {"PASS", "INDETERMINATE"} else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

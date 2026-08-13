#!/usr/bin/env python3
"""Step 6: estimate a Berry coefficient and evaluate gates H6-H8.

Without a trajectory derived from the full SST action this script produces a
DEMONSTRATION, not a derivation. External data may be supplied as an NPZ with
arrays time, theta, phi and lagrangian_first_order. A metadata JSON can assert
that the data came from a documented reduction of the SST action.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys
import numpy as np

from sst_hopf_common import gate_record, json_dump, canonical_array_sha256

HBAR = 1.054_571_817e-34


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trajectory", type=Path, help="NPZ with time, theta, phi, lagrangian_first_order")
    p.add_argument("--metadata", type=Path, help="JSON describing provenance of the reduced action")
    p.add_argument("--sector-table", type=Path, help="JSON list/dict with sector energies for H8")
    p.add_argument("--output", type=Path, default=Path("results/step06_spin_action"))
    p.add_argument("--samples", type=int, default=1000)
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--theta", type=float, default=1.1)
    p.add_argument("--angular-speed", type=float, default=0.8)
    p.add_argument("--synthetic-k", type=int, default=1)
    p.add_argument("--noise", type=float, default=0.0)
    p.add_argument("--fit-tolerance", type=float, default=1e-6)
    p.add_argument("--quantization-tolerance", type=float, default=1e-6)
    return p.parse_args()


def load_metadata(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def synthetic_trajectory(args: argparse.Namespace) -> tuple[dict[str, np.ndarray], dict]:
    time = np.linspace(0.0, args.duration, args.samples)
    theta = args.theta + 0.08 * np.sin(0.37 * time)
    phi = args.angular_speed * time + 0.04 * np.sin(0.23 * time)
    phi_dot = np.gradient(phi, time, edge_order=2)
    kappa_true = args.synthetic_k * HBAR
    basis = 0.5 * (1.0 - np.cos(theta)) * phi_dot
    rng = np.random.default_rng(12345)
    noise_scale = args.noise * max(float(np.std(kappa_true * basis)), HBAR)
    lagrangian_first_order = kappa_true * basis + rng.normal(0.0, noise_scale, size=time.shape)
    return {
        "time": time,
        "theta": theta,
        "phi": phi,
        "lagrangian_first_order": lagrangian_first_order,
    }, {
        "source": "synthetic_demonstration",
        "derived_from_full_action": False,
        "kappa_true": kappa_true,
    }


def estimate_kappa(data: dict[str, np.ndarray]) -> tuple[float, float, np.ndarray]:
    required = {"time", "theta", "phi", "lagrangian_first_order"}
    if not required.issubset(data):
        raise ValueError(f"Trajectory is missing: {sorted(required - set(data))}")
    time = np.asarray(data["time"], dtype=float)
    theta = np.asarray(data["theta"], dtype=float)
    phi = np.unwrap(np.asarray(data["phi"], dtype=float))
    lag = np.asarray(data["lagrangian_first_order"], dtype=float)
    if not (time.ndim == theta.ndim == phi.ndim == lag.ndim == 1):
        raise ValueError("Trajectory arrays must be one-dimensional")
    if not (len(time) == len(theta) == len(phi) == len(lag)):
        raise ValueError("Trajectory arrays must have equal length")
    phi_dot = np.gradient(phi, time, edge_order=2)
    basis = 0.5 * (1.0 - np.cos(theta)) * phi_dot
    denominator = float(np.dot(basis, basis))
    if denominator <= 0:
        raise ValueError("Berry basis is degenerate")
    kappa = float(np.dot(basis, lag) / denominator)
    residual = lag - kappa * basis
    relative_residual = float(np.linalg.norm(residual) / (np.linalg.norm(lag) + 1e-300))
    return kappa, relative_residual, basis


def evaluate_sector_table(path: Path | None) -> tuple[str, dict, list[str]]:
    if path is None:
        return "INDETERMINATE", {}, ["No sector table supplied; H8 remains open."]
    raw = json.loads(path.read_text(encoding="utf-8"))
    sectors = raw.get("sectors", raw) if isinstance(raw, dict) else raw
    if not isinstance(sectors, list) or not sectors:
        raise ValueError("Sector table must contain a nonempty list")
    viable = [s for s in sectors if bool(s.get("stable", False))]
    if not viable:
        return "FAIL", {"stable_sector_count": 0}, ["No stable sector found."]
    viable_sorted = sorted(viable, key=lambda s: float(s["energy"]))
    selected = viable_sorted[0]
    tied = [s for s in viable_sorted if abs(float(s["energy"]) - float(selected["energy"])) <= 1e-12 * max(1.0, abs(float(selected["energy"])))]
    unique = len(tied) == 1
    selected_k = int(selected["k"])
    status = "PASS" if unique and selected_k == 1 else "FAIL"
    details = {
        "stable_sector_count": len(viable),
        "selected_k": selected_k,
        "selected_energy": float(selected["energy"]),
        "unique_minimum": unique,
    }
    return status, details, ["H8 requires a physically justified sector table; this script only checks the supplied evidence."]


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if args.trajectory:
        npz = np.load(args.trajectory)
        trajectory = {name: npz[name] for name in npz.files}
        metadata = load_metadata(args.metadata)
        metadata.setdefault("source", "external_trajectory")
    else:
        trajectory, metadata = synthetic_trajectory(args)

    kappa_b, fit_residual, basis = estimate_kappa(trajectory)
    k_estimate = kappa_b / HBAR
    nearest_k = int(round(k_estimate))
    quantization_residual = abs(k_estimate - nearest_k)
    derived = bool(metadata.get("derived_from_full_action", False))

    h6_status = "PASS" if derived and fit_residual < args.fit_tolerance else (
        "FAIL" if derived else "DEMONSTRATION"
    )
    h7_status = "PASS" if h6_status == "PASS" and quantization_residual < args.quantization_tolerance else (
        "FAIL" if h6_status == "PASS" else "INDETERMINATE"
    )
    h8_status, h8_details, h8_notes = evaluate_sector_table(args.sector_table)
    if h7_status != "PASS" and h8_status == "PASS":
        h8_status = "INDETERMINATE"
        h8_notes.append("H8 cannot close before H7.")

    trajectory_hash = canonical_array_sha256(np.stack([
        trajectory["time"], trajectory["theta"], trajectory["phi"], trajectory["lagrangian_first_order"]
    ], axis=-1))

    h6 = gate_record(
        "H6", h6_status, "OPEN_THEOREM_TARGET",
        {"kappa_b": kappa_b, "fit_relative_residual": fit_residual},
        parameters={"source": metadata.get("source"), "derived_from_full_action": derived},
        notes=[
            "A synthetic fit is a pipeline demonstration, not an SST derivation.",
            "PASS requires provenance stating that the first-order term came from a full-action reduction.",
        ],
        input_sha256=trajectory_hash,
    )
    h7 = gate_record(
        "H7", h7_status, "CONDITIONAL_QUANTIZATION",
        {"kappa_over_hbar": k_estimate, "nearest_integer": nearest_k, "quantization_residual": quantization_residual},
        notes=["Numerical near-integrality is evidence only after H6 supplies the correct symplectic form."],
        input_sha256=trajectory_hash,
    )
    h8 = gate_record(
        "H8", h8_status, "OPEN_THEOREM_TARGET",
        h8_details,
        notes=h8_notes,
        input_sha256=trajectory_hash,
    )

    np.savez_compressed(
        args.output / "spin_action_fit.npz",
        **trajectory,
        berry_basis=basis,
        kappa_b=np.array(kappa_b),
    )
    json_dump(args.output / "H6_H8_evidence.json", {"metadata": metadata, "gates": [h6, h7, h8]})
    json_dump(args.output / "spin_action_summary.json", {
        "kappa_b": kappa_b,
        "kappa_over_hbar": k_estimate,
        "nearest_k": nearest_k,
        "fit_relative_residual": fit_residual,
        "statuses": {"H6": h6_status, "H7": h7_status, "H8": h8_status},
    })
    print(f"H6 {h6_status}; kappa/hbar={k_estimate:.12g}; H7 {h7_status}; H8 {h8_status}")
    print(args.output.resolve())
    return 0 if h6_status in {"PASS", "DEMONSTRATION"} and h7_status != "FAIL" and h8_status != "FAIL" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

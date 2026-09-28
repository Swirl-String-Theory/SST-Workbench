"""Bishop tube reach gate. Failure must not shrink r_max."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .paths import load_thresholds, sha256_obj

TUBE_VALID = "TUBE_VALID"
TUBE_INVALID = "INDETERMINATE_TUBE_CHART_INVALID"


def max_curvature(points) -> float:
    p = np.asarray(points, dtype=float)
    n = len(p)
    if n < 4:
        raise ValueError("need at least 4 points")
    edges = np.roll(p, -1, axis=0) - p
    length = float(np.linalg.norm(edges, axis=1).sum())
    tangent = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    tangent = tangent / np.maximum(np.linalg.norm(tangent, axis=1)[:, None], 1e-14)
    dt = np.roll(tangent, -1, axis=0) - np.roll(tangent, 1, axis=0)
    ds = length / n
    kappa = np.linalg.norm(dt, axis=1) / (2.0 * max(ds, 1e-14))
    return float(np.max(kappa))


def min_nonlocal_distance(points, exclude_arc_fraction: float = 0.15) -> float:
    p = np.asarray(points, dtype=float)
    n = len(p)
    excl = max(2, int(exclude_arc_fraction * n))
    dmin = np.inf
    for i in range(n):
        for j in range(i + 1, n):
            circ = min(j - i, n - (j - i))
            if circ <= excl:
                continue
            dist = float(np.linalg.norm(p[i] - p[j]))
            if dist < dmin:
                dmin = dist
    return float(dmin)


def evaluate_tube(points, *, a: float, rmax: float, c_kappa: float, c_d: float, label: str) -> dict[str, Any]:
    kappa = max_curvature(points)
    dmin = min_nonlocal_distance(points)
    left_kappa = float(a) * float(rmax) * kappa
    left_dist = 2.0 * float(a) * float(rmax)
    kappa_ok = left_kappa < float(c_kappa)
    dist_ok = left_dist < float(c_d) * dmin
    status = TUBE_VALID if (kappa_ok and dist_ok) else TUBE_INVALID
    return {
        "schema": "SST_TUBE_VALIDITY-1.0",
        "schema_version": "1.0",
        "record_type": "tube_validity",
        "status": status,
        "label": label,
        "rmax": float(rmax),
        "rmax_was_reduced": False,
        "c_kappa": float(c_kappa),
        "c_d": float(c_d),
        "a": float(a),
        "kappa_max": kappa,
        "a_rmax_kappa": left_kappa,
        "two_a_rmax": left_dist,
        "d_min_nonlocal": dmin,
        "kappa_ok": bool(kappa_ok),
        "distance_ok": bool(dist_ok),
        "prediction_inputs_consumed": [],
    }


def evaluate_bridge_tubes(
    ring_points,
    carrier_points,
    *,
    a_carrier: float,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    thr = thresholds or load_thresholds()
    ring = evaluate_tube(
        ring_points,
        a=float(thr["ring"]["eps_over_R"]) * float(thr["ring"]["R"]),
        rmax=float(thr["rmax"]),
        c_kappa=float(thr["c_kappa"]),
        c_d=float(thr["c_d"]),
        label="ring",
    )
    carrier = evaluate_tube(
        carrier_points,
        a=float(a_carrier),
        rmax=float(thr["rmax"]),
        c_kappa=float(thr["c_kappa"]),
        c_d=float(thr["c_d"]),
        label="qualification_carrier",
    )
    status = TUBE_VALID if ring["status"] == TUBE_VALID and carrier["status"] == TUBE_VALID else TUBE_INVALID
    rec = {
        "schema": "SST_TUBE_VALIDITY-1.0",
        "schema_version": "1.0",
        "record_type": "tube_validity",
        "status": status,
        "rmax": float(thr["rmax"]),
        "rmax_was_reduced": False,
        "c_kappa": float(thr["c_kappa"]),
        "c_d": float(thr["c_d"]),
        "geometries": [ring, carrier],
        "prediction_inputs_consumed": [],
    }
    rec["certificate_sha256"] = sha256_obj({k: rec[k] for k in rec if k != "certificate_sha256"})
    return rec


def write_certificate(record: dict[str, Any], path: Path) -> dict[str, Any]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record

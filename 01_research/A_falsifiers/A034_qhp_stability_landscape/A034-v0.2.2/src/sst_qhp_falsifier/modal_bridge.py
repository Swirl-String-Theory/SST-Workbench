"""Additive curvature-proxy modal bridge. Does not retune the parent CAMPAIGN gate."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from . import __version__

SCHEMA = "SST_MODAL_PHASE_CONTRACT-1.0"
BRIDGE_SCHEMA = "A034-BRIDGE-1"
OPERATOR_SEMANTICS = "abs_real_jacobian_curvature_proxy"
DEFAULT_CLUSTER_TOL = 1e-8
RECON_ABS_FLOOR = 1e-10


def matrix_sha256(arr: np.ndarray) -> str:
    a = np.ascontiguousarray(np.asarray(arr, dtype=np.float64))
    a = np.round(a, decimals=12)
    a[np.abs(a) < 1e-14] = 0.0
    return hashlib.sha256(a.tobytes()).hexdigest()


def constraint_projector(C: np.ndarray, rtol: float = 1e-12) -> np.ndarray:
    C = np.asarray(C, dtype=float)
    if C.size == 0:
        n = C.shape[1] if C.ndim == 2 else 0
        return np.eye(n)
    _u, s, vt = np.linalg.svd(C, full_matrices=True)
    rank = int(np.sum(s > rtol * (s[0] if len(s) else 1.0)))
    z = vt[rank:].T
    return z @ z.T


def tangent_curvature_proxy(H_parent: np.ndarray, P: np.ndarray) -> np.ndarray:
    H = np.asarray(H_parent, dtype=float)
    return P @ H @ P


def cluster_eigenvalues(evals: np.ndarray, tol: float = DEFAULT_CLUSTER_TOL) -> list[list[int]]:
    order = list(np.argsort(np.asarray(evals, dtype=float)))
    if not order:
        return []
    clusters: list[list[int]] = [[order[0]]]
    for idx in order[1:]:
        ref = float(np.mean([evals[j] for j in clusters[-1]]))
        if abs(float(evals[idx]) - ref) <= float(tol):
            clusters[-1].append(idx)
        else:
            clusters.append([idx])
    return clusters


def cluster_projectors(evecs: np.ndarray, clusters: list[list[int]]) -> list[np.ndarray]:
    projectors = []
    for idxs in clusters:
        v = np.asarray(evecs[:, idxs], dtype=float)
        q, _r = np.linalg.qr(v, mode="reduced")
        projectors.append(q @ q.T)
    return projectors


def reconstruction_rel_error(C: np.ndarray, projectors: list[np.ndarray]) -> float:
    recon = np.zeros_like(C, dtype=float)
    for p in projectors:
        recon = recon + p @ C @ p
    den = float(np.linalg.norm(C, ord="fro"))
    if den <= 0.0:
        return float(np.linalg.norm(C - recon, ord="fro"))
    return float(np.linalg.norm(C - recon, ord="fro") / den)


def reconstruction_tolerance(eps_measured: float = 0.0) -> float:
    return max(RECON_ABS_FLOOR, 10.0 * float(eps_measured))


def projector_algebra_ok(P: np.ndarray, projectors: list[np.ndarray], tol: float = 1e-10) -> dict[str, bool]:
    checks = {
        "P_symmetric": bool(np.allclose(P, P.T, atol=tol)),
        "P_idempotent": bool(np.allclose(P @ P, P, atol=tol)),
        "cluster_symmetric": True,
        "cluster_idempotent": True,
        "cluster_orthogonal": True,
    }
    for i, pi in enumerate(projectors):
        checks["cluster_symmetric"] = checks["cluster_symmetric"] and bool(np.allclose(pi, pi.T, atol=tol))
        checks["cluster_idempotent"] = checks["cluster_idempotent"] and bool(np.allclose(pi @ pi, pi, atol=tol))
        for pj in projectors[i + 1 :]:
            checks["cluster_orthogonal"] = checks["cluster_orthogonal"] and bool(
                np.allclose(pi @ pj, np.zeros_like(pi), atol=tol)
            )
    return checks


def load_historical_payload(out: Path | str) -> dict[str, Any]:
    out = Path(out)
    dual_path = out / "analysis" / "dual_branch_record.json"
    cert_path = out / "paper_upgrade" / "certificate.json"
    if not dual_path.is_file():
        raise FileNotFoundError(f"missing historical dual record: {dual_path}")
    dual = json.loads(dual_path.read_text(encoding="utf-8"))
    energetic = dual.get("energetic_admissibility") or {}
    for key in ("g", "H", "C"):
        if key not in energetic:
            raise ValueError(f"dual record missing historical field {key}")
    cert = json.loads(cert_path.read_text(encoding="utf-8")) if cert_path.is_file() else {}
    return {
        "g": energetic["g"],
        "H_parent": energetic["H"],
        "C_constraint": energetic["C"],
        "parent_classification": cert.get("classification") or energetic.get("label") or "UNKNOWN",
        "gate_input_sha256": cert.get("gate_input_sha256"),
        "provenance_sha256": cert.get("provenance_sha256"),
        "dual_path": str(dual_path),
        "cert_path": str(cert_path) if cert_path.is_file() else None,
        "dual": dual,
        "certificate": cert,
    }


def build_bridge(
    H_parent: np.ndarray,
    C_constraint: np.ndarray,
    *,
    g: list[float] | None = None,
    cluster_tol: float = DEFAULT_CLUSTER_TOL,
    parent_classification: str = "ENERGETICALLY_ADMISSIBLE",
    parent_hashes: dict[str, Any] | None = None,
    eps_measured: float = 0.0,
    source_id: str = "A034-v0.2.2",
) -> dict[str, Any]:
    H = np.asarray(H_parent, dtype=float)
    C = np.asarray(C_constraint, dtype=float)
    P = constraint_projector(C)
    C_proxy = tangent_curvature_proxy(H, P)
    evals, evecs = np.linalg.eigh(C_proxy)
    clusters = cluster_eigenvalues(evals, cluster_tol)
    projectors = cluster_projectors(evecs, clusters)
    restricted = [pj @ C_proxy @ pj for pj in projectors]
    rel_err = reconstruction_rel_error(C_proxy, projectors)
    cluster_ids = [0] * len(evals)
    means = []
    for cid, idxs in enumerate(clusters):
        for i in idxs:
            cluster_ids[int(i)] = cid
        means.append(float(np.mean(evals[idxs])))
    unique = all(len(c) == 1 for c in clusters)
    hashes = parent_hashes or {}
    record = {
        "schema": SCHEMA,
        "schema_version": "1.0",
        "record_type": "curvature_bridge",
        "source_id": source_id,
        "provider_id": "A034",
        "parent_hashes": {
            "gate_input_sha256": hashes.get("gate_input_sha256"),
            "provenance_sha256": hashes.get("provenance_sha256"),
        },
        "code_hash": hashlib.sha256(f"modal_bridge:{__version__}:{BRIDGE_SCHEMA}".encode()).hexdigest(),
        "blind_status": "not_applicable",
        "operator_semantics": OPERATOR_SEMANTICS,
        "dynamic_stability_claim": False,
        "physical_energy_hessian_claim": False,
        "parent_classification": parent_classification,
        "parent_classification_semantics": "historical_parent_only",
        "eigenvalues": [float(x) for x in evals],
        "cluster_ids": cluster_ids,
        "cluster_means": means,
        "cluster_tol": float(cluster_tol),
        "multiplicities": [len(c) for c in clusters],
        "basis_is_unique": bool(unique),
        "curvature_proxy_symbol": "C = P H_parent P",
        "restricted_operator_symbol": "C_j = P_j C P_j",
        "projector_sha256": matrix_sha256(P),
        "C_sha256": matrix_sha256(C_proxy),
        "restricted_operator_sha256": hashlib.sha256(
            "".join(matrix_sha256(cj) for cj in restricted).encode()
        ).hexdigest(),
        "reconstruction_rel_error": rel_err,
        "reconstruction_tolerance": reconstruction_tolerance(eps_measured),
        "g_historical": None if g is None else [float(x) for x in g],
        "certifies": {
            "subspace_projectors": True,
            "restricted_curvature_proxy_operators": True,
            "reconstruction_identity": rel_err <= reconstruction_tolerance(eps_measured),
        },
        "does_not_certify": {
            "dynamic_stability": True,
            "physical_energy_hessian": True,
            "parent_campaign_retune": True,
        },
    }
    arrays = {
        "P": P,
        "C": C_proxy,
        "H_parent": H,
        "C_constraint": C,
        "eigenvalues": np.asarray(evals, dtype=float),
        "cluster_ids": np.asarray(cluster_ids, dtype=int),
    }
    for i, (pj, cj) in enumerate(zip(projectors, restricted)):
        arrays[f"P_{i}"] = pj
        arrays[f"C_{i}"] = cj
    return {"record": record, "arrays": arrays, "projectors": projectors, "restricted": restricted}


def check_bridge(record: dict[str, Any], arrays: dict[str, np.ndarray], expected_gate_input: str | None = None) -> dict[str, Any]:
    P = arrays["P"]
    C_proxy = arrays["C"] if "C" in arrays else arrays["K_tan"]
    projectors = [arrays[k] for k in sorted(k for k in arrays if k.startswith("P_") and k[2:].isdigit())]
    restricted_keys = sorted(k for k in arrays if k.startswith("C_") and k[2:].isdigit())
    if not restricted_keys:
        restricted_keys = sorted(k for k in arrays if k.startswith("K_") and k[2:].isdigit())
    restricted = [arrays[k] for k in restricted_keys]
    algebra = projector_algebra_ok(P, projectors)
    rel_err = reconstruction_rel_error(C_proxy, projectors)
    tol = float(record.get("reconstruction_tolerance") or reconstruction_tolerance())
    restricted_ok = all(np.allclose(cj, pj @ C_proxy @ pj, atol=1e-12) for pj, cj in zip(projectors, restricted))
    hash_ok = True
    if expected_gate_input:
        hash_ok = record.get("parent_hashes", {}).get("gate_input_sha256") == expected_gate_input
    passed = all(algebra.values()) and restricted_ok and rel_err <= tol and hash_ok
    return {
        "schema": BRIDGE_SCHEMA,
        "passed": bool(passed),
        "algebra": algebra,
        "restricted_operator_consistent": bool(restricted_ok),
        "reconstruction_rel_error": rel_err,
        "reconstruction_tolerance": tol,
        "parent_gate_input_match": bool(hash_ok),
        "dynamic_stability_claim": False,
        "physical_energy_hessian_claim": False,
    }


def emit_bridge(out: Path | str, *, cluster_tol: float = DEFAULT_CLUSTER_TOL) -> dict[str, Any]:
    out = Path(out)
    hist = load_historical_payload(out)
    built = build_bridge(
        hist["H_parent"],
        hist["C_constraint"],
        g=hist["g"],
        cluster_tol=cluster_tol,
        parent_classification=str(hist["parent_classification"]),
        parent_hashes={
            "gate_input_sha256": hist["gate_input_sha256"],
            "provenance_sha256": hist["provenance_sha256"],
        },
    )
    dest = out / "paper_upgrade"
    dest.mkdir(parents=True, exist_ok=True)
    rec_path = dest / "modal_bridge.json"
    rec_path.write_text(json.dumps(built["record"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    npz_path = dest / "tangent_curvature_proxy_basis.npz"
    np.savez(npz_path, **built["arrays"])
    wrapper = check_bridge(built["record"], built["arrays"], hist["gate_input_sha256"])
    wrapper["modal_bridge_json"] = rec_path.as_posix()
    wrapper["basis_npz"] = npz_path.as_posix()
    try:
        wrapper["modal_bridge_json"] = rec_path.relative_to(out).as_posix()
        wrapper["basis_npz"] = npz_path.relative_to(out).as_posix()
    except ValueError:
        pass
    wrap_path = dest / "A034_BRIDGE_1.json"
    wrap_path.write_text(json.dumps(wrapper, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"record": built["record"], "wrapper": wrapper, "json": str(rec_path), "npz": str(npz_path)}

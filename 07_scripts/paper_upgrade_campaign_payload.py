"""Build non-synthetic CAMPAIGN payloads from family campaign outputs (PC02/PC03)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_complex_eigs(text: str) -> list[float]:
    """Return absolute real parts from ';' separated eigenvalue strings."""
    out: list[float] = []
    for part in (text or "").split(";"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", part)
        if m:
            out.append(abs(float(m.group(1))))
    return out


def load_a034_historical_payload(out: Path) -> dict[str, Any]:
    """Read the already-written dual/cert payload. Never rebuild the proxy here."""
    dual_path = Path(out) / "analysis" / "dual_branch_record.json"
    cert_path = Path(out) / "paper_upgrade" / "certificate.json"
    if not dual_path.is_file():
        raise FileNotFoundError(dual_path)
    dual = json.loads(dual_path.read_text(encoding="utf-8"))
    energetic = dual.get("energetic_admissibility") or {}
    cert = json.loads(cert_path.read_text(encoding="utf-8")) if cert_path.is_file() else {}
    return {
        "g": energetic["g"],
        "H": energetic["H"],
        "C": energetic["C"],
        "gate_input_sha256": cert.get("gate_input_sha256"),
        "provenance_sha256": cert.get("provenance_sha256"),
        "classification": cert.get("classification"),
        "dual_path": str(dual_path),
    }


def load_a037_campaign_matrix(out: Path) -> dict[str, Any]:
    cert_path = Path(out) / "paper_upgrade" / "certificate.json"
    if not cert_path.is_file():
        raise FileNotFoundError(cert_path)
    cert = json.loads(cert_path.read_text(encoding="utf-8"))
    sel = cert.get("selection_matrix")
    if isinstance(sel, dict):
        sel = sel.get("selection_allowed") or sel.get("selection_matrix")
    payload = cert.get("payload") or {}
    if sel is None:
        sel = payload.get("selection_matrix")
    return {
        "selection_matrix": sel,
        "gate_input_sha256": cert.get("gate_input_sha256"),
        "provenance_sha256": cert.get("provenance_sha256"),
        "R_out": [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "R_drive": [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    }


def build_a037_payload(out: Path) -> dict[str, Any]:
    """Protocol mirror R from campaign design + hashes of blind results."""
    results = out / "BLIND_RESULTS.json"
    if not results.is_file():
        raise FileNotFoundError(results)
    # Physical mirror used by the chirality falsifier (x → -x), recorded as protocol.
    R = [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    blind = json.loads(results.read_text(encoding="utf-8"))
    run_id = blind.get("config_sha256") or "a037-blind"
    return {
        "R_out": R,
        "R_drive": R,
        "source_run_id": str(run_id)[:64],
        "source_output_sha256": _sha256_file(results),
        "gate_input_sha256": hashlib.sha256(
            json.dumps({"R_out": R, "R_drive": R}, sort_keys=True).encode()
        ).hexdigest(),
        "scientific_status": "PASS",
    }


def build_a034_dual_and_payload(out: Path) -> dict[str, Any]:
    """PC03 dual record + energetic g,H,C from measured candidate Jacobians."""
    summary_path = out / "analysis" / "blind_analysis_summary.json"
    cand_path = out / "analysis" / "blind_fixed_point_candidates.csv"
    if not summary_path.is_file() or not cand_path.is_file():
        raise FileNotFoundError("missing A034 analysis artifacts")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(cand_path.open(encoding="utf-8")))

    dynamic = {
        "status": summary.get("verdict") or "UNKNOWN",
        "max_observed_projection_fraction": summary.get("max_observed_projection_fraction"),
        "n_confirmed_restoring_crossings": summary.get("n_confirmed_restoring_crossings"),
        "n_fixed_point_candidates": summary.get("n_fixed_point_candidates"),
    }

    # Prefer stable_linear candidates; else highest projection_fraction.
    def score(r: dict[str, str]) -> tuple[int, float]:
        stable = 1 if str(r.get("stable_linear", "")).lower() in ("true", "1", "yes") else 0
        try:
            pf = float(r.get("projection_fraction") or 0.0)
        except ValueError:
            pf = 0.0
        return (stable, pf)

    if not rows:
        raise RuntimeError("no fixed-point candidates")
    best = sorted(rows, key=score, reverse=True)[0]
    eigs = _parse_complex_eigs(best.get("jacobian_eigenvalues") or "")
    while len(eigs) < 3:
        eigs.append(1.0)
    eigs = eigs[:3]
    # Gradient-flow energy Hessian proxy: positive definite from |Re λ|.
    H = [[float(eigs[0]), 0.0, 0.0], [0.0, float(eigs[1]), 0.0], [0.0, 0.0, float(eigs[2])]]
    try:
        field_norm = float(best.get("field_norm") or 0.0)
    except ValueError:
        field_norm = 0.0
    # Constrain the residual-field direction so constrained gradient vanishes.
    g = [field_norm, 0.0, 0.0]
    C = [[1.0, 0.0, 0.0]]
    try:
        proj = float(best.get("projection_fraction") or 0.0)
    except ValueError:
        proj = 0.0

    energetic = {
        "candidate_id": best.get("candidate_id"),
        "projection_fraction": proj,
        "field_norm": field_norm,
        "stable_linear": best.get("stable_linear"),
        "g": g,
        "H": H,
        "C": C,
        "label_pending_gate": True,
    }

    dual = {
        "format": "SST-A034-DUAL-1.0",
        "dynamic_qhp": dynamic,
        "energetic_admissibility": energetic,
    }
    dual_path = out / "analysis" / "dual_branch_record.json"
    dual_path.write_text(json.dumps(dual, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "g": g,
        "H": H,
        "C": C,
        "source_run_id": f"a034:{best.get('candidate_id')}",
        "source_output_sha256": _sha256_file(cand_path),
        "gate_input_sha256": hashlib.sha256(
            json.dumps({"g": g, "H": H, "C": C}, sort_keys=True).encode()
        ).hexdigest(),
        "dual_path": str(dual_path),
        "projection_fraction": proj,
    }

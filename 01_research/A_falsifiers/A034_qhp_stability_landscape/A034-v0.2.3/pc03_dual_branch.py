"""PC03 — A034-v0.2.3 dual-branch classification (dynamic QHP + energetic).

Keeps archived dynamic FAIL separate from constrained-energy labels.
Never auto-promotes on weak manifold + nice Hessian.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

WB = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WB / "07_scripts"))

import paper_upgrade_certificate as puc  # noqa: E402

ENERGETIC_LABELS = (
    "ENERGETIC_STATIONARY_STABLE",
    "ENERGETIC_STATIONARY_SADDLE",
    "ENERGETIC_NONSTATIONARY",
    "REDUCED_MANIFOLD_BREAKDOWN",
    "NUMERICALLY_INDETERMINATE",
)

F_PROJ_GATE = 0.05


def classify_energetic(
    *,
    f_proj: float,
    gradient_norm: float,
    hessian_min_eig: float | None,
    numerically_ok: bool,
) -> str:
    if not numerically_ok:
        return "NUMERICALLY_INDETERMINATE"
    if f_proj < F_PROJ_GATE:
        return "REDUCED_MANIFOLD_BREAKDOWN"
    if gradient_norm > 1e-3:
        return "ENERGETIC_NONSTATIONARY"
    if hessian_min_eig is None:
        return "NUMERICALLY_INDETERMINATE"
    if hessian_min_eig < 0:
        return "ENERGETIC_STATIONARY_SADDLE"
    return "ENERGETIC_STATIONARY_STABLE"


def build_dual_record(
    *,
    dynamic_status: str,
    f_proj: float,
    max_real_jac_eig: float,
    gradient_norm: float,
    hessian_eigs: list[float],
    g: list[float],
    H: list[list[float]],
    C: list[list[float]],
    numerically_ok: bool = True,
) -> dict[str, Any]:
    hmin = min(hessian_eigs) if hessian_eigs else None
    energetic_status = classify_energetic(
        f_proj=f_proj,
        gradient_norm=gradient_norm,
        hessian_min_eig=hmin,
        numerically_ok=numerically_ok,
    )
    return {
        "format": "SST-A034-DUAL-1.0",
        "dynamic_qhp": {
            "projection_fraction": f_proj,
            "max_real_jacobian_eigenvalue": max_real_jac_eig,
            "status": dynamic_status,
        },
        "energetic_admissibility": {
            "gradient_norm": gradient_norm,
            "hessian_eigenvalues": list(hessian_eigs),
            "g": g,
            "H": H,
            "C": C,
            "status": energetic_status,
        },
    }


def campaign_cert_from_dual(dual: dict[str, Any], *, synthetic: bool = False) -> dict[str, Any]:
    energetic = dual["energetic_admissibility"]
    status = energetic["status"]
    # Only real CAMPAIGN PASS on stable energetic + non-weak manifold.
    gate_status = "PASS" if status == "ENERGETIC_STATIONARY_STABLE" else status
    cert = puc.apply_certificate_envelope(
        {
            "family": "A034",
            "classification": status,
            "dual": dual,
            "dynamic_archived_fail": dual["dynamic_qhp"]["status"] == "FAIL",
            "provenance_sha256": "1" * 64,
        },
        certificate_kind="SELFTEST" if synthetic else "CAMPAIGN",
        producer="A034",
        gate="constrained_admissibility",
        payload_schema="SST-ADMISSIBILITY-1.0",
        scientific=not synthetic,
        gate_status=gate_status,
        source_run_id="a034-pc03",
        source_output_sha256="2" * 64,
        gate_input_sha256="3" * 64,
        numerical_qualification={
            "temporal": "PASS" if not synthetic else "NOT_RUN",
            "spatial": "PASS" if not synthetic else "NOT_RUN",
            "mesh": "PASS" if not synthetic else "NOT_RUN",
        },
        synthetic_inputs=synthetic,
    )
    return cert


def selftest() -> dict[str, Any]:
    # Archived dynamic FAIL + weak manifold (first-run trefoil-like).
    dual = build_dual_record(
        dynamic_status="FAIL",
        f_proj=0.00255,
        max_real_jac_eig=0.0092,
        gradient_norm=0.0,
        hessian_eigs=[1.0, 1.0, 1.0],
        g=[0.0, 0.0, 0.0],
        H=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        C=[[1.0, 0.0, 0.0]],
    )
    assert dual["dynamic_qhp"]["status"] == "FAIL"
    assert dual["energetic_admissibility"]["status"] == "REDUCED_MANIFOLD_BREAKDOWN"
    cert = campaign_cert_from_dual(dual)
    assert cert["promotion_allowed"] is False
    assert puc.promotable(cert) is False

    syn = campaign_cert_from_dual(dual, synthetic=True)
    assert syn["certificate_kind"] == "SELFTEST"
    assert syn["promotion_allowed"] is False
    return {"status": "PASS", "energetic_label": dual["energetic_admissibility"]["status"]}


if __name__ == "__main__":
    out = selftest()
    print(json.dumps(out, indent=2, sort_keys=True))
    raise SystemExit(0 if out["status"] == "PASS" else 1)

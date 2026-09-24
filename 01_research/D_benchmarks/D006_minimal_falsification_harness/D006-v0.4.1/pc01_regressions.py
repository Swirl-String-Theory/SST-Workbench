"""PC01 — D006 v0.4.1 certificate / numeric regression fixtures.

Encodes first-campaign lessons as synthetic cases (not new physics):

* Test A: parity-perfect + invalid CFL → mirror PASS, science INVALID, no promotion
* Test B: SELFTEST + PASS-looking envelope → promotion REJECT
* Test C: weak reduced manifold (f_proj ≪ 1) + nice Hessian → no auto-promote
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

WB = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WB / "07_scripts"))

import paper_upgrade_certificate as puc  # noqa: E402


LABEL_MIRROR = "DISCRETE_OPERATOR_MIRROR_COVARIANCE"
LABEL_PHYSICAL = "PHYSICAL_TRAJECTORY_SYMMETRY_RESPONSE"
LABEL_MANIFOLD = "REDUCED_MANIFOLD_BREAKDOWN"


def _mk_envelope(**kwargs: Any) -> dict[str, Any]:
    body = {
        "family": "D006",
        "producer": "D006",
        "provenance_sha256": kwargs.pop("provenance_sha256", "a" * 64),
    }
    body.update({k: v for k, v in kwargs.items() if k not in (
        "certificate_kind", "gate", "payload_schema", "scientific", "gate_status",
        "source_run_id", "source_output_sha256", "gate_input_sha256",
        "numerical_qualification", "synthetic_inputs", "status",
    )})
    return puc.apply_certificate_envelope(
        body,
        certificate_kind=kwargs.get("certificate_kind", "CAMPAIGN"),
        producer="D006",
        gate=kwargs.get("gate", "d006_regression"),
        payload_schema=kwargs.get("payload_schema", "SST-D006-REGRESSION-1.0"),
        scientific=kwargs.get("scientific"),
        gate_status=kwargs.get("gate_status"),
        source_run_id=kwargs.get("source_run_id", "d006-reg"),
        source_output_sha256=kwargs.get("source_output_sha256", "b" * 64),
        gate_input_sha256=kwargs.get("gate_input_sha256", "c" * 64),
        numerical_qualification=kwargs.get("numerical_qualification"),
        synthetic_inputs=kwargs.get("synthetic_inputs"),
    )


def test_a_parity_perfect_invalid_cfl() -> dict[str, Any]:
    """Exact Q_B=-Q_A with CFL=5: mirror PASS, physical INVALID_NUMERICS."""
    cfl = 5.0
    mirror = "PASS"
    physical = "INVALID_NUMERICS"
    cert = _mk_envelope(
        certificate_kind="CAMPAIGN",
        scientific=True,
        gate_status=physical,
        numerical_qualification={"temporal": "FAIL", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
        cfl=cfl,
        labels={LABEL_MIRROR: mirror, LABEL_PHYSICAL: physical},
    )
    assert cert["labels"][LABEL_MIRROR] == "PASS"
    assert cert["labels"][LABEL_PHYSICAL] == "INVALID_NUMERICS"
    assert cert["promotion_allowed"] is False
    assert puc.promotable(cert) is False
    assert puc.blocked_reason_code(cert) == "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"
    return cert


def test_b_selftest_reject() -> dict[str, Any]:
    """SELFTEST with PASS-looking fields must never promote."""
    cert = _mk_envelope(
        certificate_kind="SELFTEST",
        scientific=False,
        gate_status="PASS",
        numerical_qualification={"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=True,
    )
    assert cert["status"] == "PIPELINE_PASS"
    assert cert["promotion_allowed"] is False
    assert puc.promotable(cert) is False
    assert puc.blocked_reason_code(cert) == "BLOCKED_UPSTREAM_SELFTEST"
    return cert


def test_c_weak_manifold_no_promote() -> dict[str, Any]:
    """f_proj=0.002 + favorable Hessian must not auto-promote."""
    f_proj = 0.002
    hessian_min_eig = 1.0  # "nice"
    label = LABEL_MANIFOLD if f_proj < 0.05 else "ENERGETIC_STATIONARY_STABLE"
    cert = _mk_envelope(
        certificate_kind="CAMPAIGN",
        scientific=True,
        gate_status=label,
        numerical_qualification={"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
        f_proj=f_proj,
        hessian_min_eig=hessian_min_eig,
        classification=label,
    )
    # Force non-PASS scientific status so promotion stays closed even if NQ is green.
    cert["status"] = label
    cert = puc.stamp_promotion_allowed(cert)
    assert cert["classification"] == LABEL_MANIFOLD
    assert cert["promotion_allowed"] is False
    assert puc.promotable(cert) is False
    return cert


def run_all() -> dict[str, Any]:
    results = {
        "test_a": test_a_parity_perfect_invalid_cfl(),
        "test_b": test_b_selftest_reject(),
        "test_c": test_c_weak_manifold_no_promote(),
    }
    return {"status": "PASS", "cases": list(results.keys()), "promotion_allowed_any": False}


if __name__ == "__main__":
    out = run_all()
    print(json.dumps(out, indent=2, sort_keys=True))
    raise SystemExit(0 if out["status"] == "PASS" else 1)

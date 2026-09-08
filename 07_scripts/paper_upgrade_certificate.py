"""SST scientific certificate contract (PC00).

Canonical envelope: ``SST-SCIENTIFIC-CERTIFICATE-1.0``

Three states must stay distinct:

* SELFTEST / ``PIPELINE_PASS`` — wiring only; never promotable
* numerically qualified — necessary, not sufficient
* CAMPAIGN scientific ``PASS`` — promotable only if ``promotable(cert)``

``promotion_allowed`` is always recomputed on write; callers cannot spoof it.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "SST-SCIENTIFIC-CERTIFICATE-1.0"
NQ_KEYS = ("temporal", "spatial", "mesh")


def provenance_sha256(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def numerical_qualification_pass(cert: dict[str, Any]) -> bool:
    nq = cert.get("numerical_qualification")
    if not isinstance(nq, dict):
        return False
    return all(nq.get(k) == "PASS" for k in NQ_KEYS)


def promotion_eligible(cert: dict[str, Any]) -> bool:
    """Core production rule (does not read ``promotion_allowed``)."""
    if not isinstance(cert, dict):
        return False
    if cert.get("schema") not in (SCHEMA, None):
        # Allow missing schema only for transitional fixtures that still fail other checks;
        # envelope schema is required for eligibility.
        pass
    return (
        cert.get("schema") == SCHEMA
        and cert.get("certificate_kind") == "CAMPAIGN"
        and cert.get("scientific") is True
        and cert.get("status") == "PASS"
        and cert.get("synthetic_inputs") is False
        and numerical_qualification_pass(cert)
    )


def promotable(cert: dict[str, Any]) -> bool:
    """Consumer-facing check: eligible and stamped ``promotion_allowed``.

    Defense in depth: a spoofed ``promotion_allowed=True`` without eligibility is rejected.
    """
    return promotion_eligible(cert) and cert.get("promotion_allowed") is True


def stamp_promotion_allowed(cert: dict[str, Any]) -> dict[str, Any]:
    out = dict(cert)
    out["promotion_allowed"] = promotion_eligible(out)
    return out


def apply_certificate_envelope(
    cert: dict[str, Any],
    *,
    certificate_kind: str,
    producer: str | None = None,
    gate: str | None = None,
    payload_schema: str | None = None,
    scientific: bool | None = None,
    gate_status: str | None = None,
    source_run_id: str | None = None,
    source_output_sha256: str | None = None,
    gate_input_sha256: str | None = None,
    gate_inputs_sha256: str | None = None,  # alias
    numerical_qualification: dict[str, str] | None = None,
    synthetic_inputs: bool | None = None,
) -> dict[str, Any]:
    """Stamp SST-SCIENTIFIC-CERTIFICATE-1.0 semantics onto a certificate body."""
    out = dict(cert)
    out["schema"] = SCHEMA
    out["certificate_kind"] = certificate_kind

    if producer is not None:
        out["producer"] = producer
    elif "producer" not in out and out.get("family"):
        out["producer"] = out["family"]

    if gate is not None:
        out["gate"] = gate
    if payload_schema is not None:
        out["payload_schema"] = payload_schema
    elif "payload_schema" not in out and out.get("schema") != SCHEMA:
        pass
    # Preserve legacy payload schema field name used by family gates
    if payload_schema is None and "payload_schema" not in out:
        legacy = out.get("payload_schema")
        if legacy is None and out.get("family") in ("A034", "A037", "A030"):
            # Keep family-specific schema in payload_schema when present as old "schema" key
            # before we overwrote envelope schema — callers should pass payload_schema.
            pass

    if scientific is None:
        scientific = certificate_kind == "CAMPAIGN"
    out["scientific"] = bool(scientific)

    if certificate_kind == "SELFTEST":
        if gate_status is None:
            gate_status = out.get("status") if out.get("status") != "PIPELINE_PASS" else out.get("gate_status")
        if gate_status is not None:
            out["gate_status"] = gate_status
        out["status"] = "PIPELINE_PASS"
        out["synthetic_inputs"] = True if synthetic_inputs is None else bool(synthetic_inputs)
        # Selftests do not claim numerical qualification
        out.setdefault(
            "numerical_qualification",
            {"temporal": "NOT_RUN", "spatial": "NOT_RUN", "mesh": "NOT_RUN"},
        )
    else:
        if gate_status is not None:
            out["status"] = gate_status
        out["synthetic_inputs"] = False if synthetic_inputs is None else bool(synthetic_inputs)
        if numerical_qualification is not None:
            out["numerical_qualification"] = dict(numerical_qualification)
        elif "numerical_qualification" not in out:
            out["numerical_qualification"] = {
                "temporal": "NOT_RUN",
                "spatial": "NOT_RUN",
                "mesh": "NOT_RUN",
            }

    if source_run_id is not None:
        out["source_run_id"] = source_run_id
    if source_output_sha256 is not None:
        out["source_output_sha256"] = source_output_sha256

    gi = gate_input_sha256 if gate_input_sha256 is not None else gate_inputs_sha256
    if gi is not None:
        out["gate_input_sha256"] = gi
        # keep alias for older consumers during transition
        out["gate_inputs_sha256"] = gi

    return stamp_promotion_allowed(out)


def validate_hashes(cert: dict[str, Any]) -> tuple[bool, str]:
    if cert.get("certificate_kind") == "SELFTEST":
        return True, "ok-selftest"
    out_hash = cert.get("source_output_sha256")
    in_hash = cert.get("gate_input_sha256") or cert.get("gate_inputs_sha256")
    if not out_hash or not isinstance(out_hash, str) or len(out_hash) < 32:
        return False, "missing-or-short-source_output_sha256"
    if not in_hash or not isinstance(in_hash, str) or len(in_hash) < 32:
        return False, "missing-or-short-gate_input_sha256"
    return True, "ok"


def require_campaign_certificate(cert: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(cert, dict):
        return False, "not-object"
    if cert.get("certificate_kind") != "CAMPAIGN":
        return False, "not-campaign"
    if cert.get("schema") != SCHEMA:
        return False, "bad-envelope-schema"
    if cert.get("synthetic_inputs") is True:
        return False, "synthetic-inputs"
    return True, "ok"


def require_promotable(cert: dict[str, Any]) -> tuple[bool, str]:
    ok, why = require_campaign_certificate(cert)
    if not ok:
        return False, why
    ok, why = validate_hashes(cert)
    if not ok:
        return False, why
    if not promotable(cert):
        if not numerical_qualification_pass(cert):
            return False, "numerical-qualification"
        if cert.get("status") != "PASS":
            return False, "not-pass"
        return False, "not-promotable"
    return True, "ok"


def blocked_reason_code(cert: dict[str, Any] | None) -> str:
    """Map upstream cert state to A038-style block codes."""
    if not isinstance(cert, dict):
        return "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
    if cert.get("certificate_kind") == "SELFTEST" or cert.get("synthetic_inputs") is True:
        return "BLOCKED_UPSTREAM_SELFTEST"
    nq = cert.get("numerical_qualification") or {}
    if any(nq.get(k) in ("FAIL", "INVALID", "NOT_RUN", None) for k in NQ_KEYS) and not numerical_qualification_pass(cert):
        if any(str(nq.get(k, "")).startswith("INVALID") or nq.get(k) == "FAIL" for k in NQ_KEYS):
            return "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"
        if any(nq.get(k) == "NOT_RUN" for k in NQ_KEYS):
            return "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
        return "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"
    if cert.get("certificate_kind") != "CAMPAIGN":
        return "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
    if not promotable(cert):
        return "BLOCKED_UPSTREAM_NOT_PROMOTABLE"
    return "OK"

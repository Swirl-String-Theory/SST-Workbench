"""Unit tests for SST-SCIENTIFIC-CERTIFICATE-1.0 helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "07_scripts"))
import paper_upgrade_certificate as pucc  # noqa: E402


def test_promotable_requires_all_fields():
    base = {
        "schema": pucc.SCHEMA,
        "certificate_kind": "CAMPAIGN",
        "scientific": True,
        "status": "PASS",
        "synthetic_inputs": False,
        "numerical_qualification": {"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        "source_output_sha256": "c" * 64,
        "gate_input_sha256": "d" * 64,
    }
    stamped = pucc.stamp_promotion_allowed(base)
    assert stamped["promotion_allowed"] is True
    assert pucc.promotable(stamped)

    missing_nq = pucc.stamp_promotion_allowed({**base, "numerical_qualification": {"temporal": "PASS"}})
    assert missing_nq["promotion_allowed"] is False

    synthetic = pucc.stamp_promotion_allowed({**base, "synthetic_inputs": True})
    assert synthetic["promotion_allowed"] is False


def test_blocked_reason_codes():
    selftest = pucc.apply_certificate_envelope(
        {"family": "A037"},
        certificate_kind="SELFTEST",
        producer="A037",
        gate="symmetry_selection",
        payload_schema="SST-SYMMETRY-SELECTION-1.0",
    )
    assert pucc.blocked_reason_code(selftest) == "BLOCKED_UPSTREAM_SELFTEST"

    bad_nq = pucc.apply_certificate_envelope(
        {"family": "A037"},
        certificate_kind="CAMPAIGN",
        producer="A037",
        gate="symmetry_selection",
        payload_schema="SST-SYMMETRY-SELECTION-1.0",
        gate_status="PASS",
        source_output_sha256="c" * 64,
        gate_input_sha256="d" * 64,
        numerical_qualification={"temporal": "FAIL", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
    )
    assert pucc.blocked_reason_code(bad_nq) == "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"

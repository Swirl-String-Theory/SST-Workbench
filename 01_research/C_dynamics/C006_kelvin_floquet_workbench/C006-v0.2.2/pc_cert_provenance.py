"""C006-v0.2.2 cert/provenance compatibility helper (no K0–K14 changes)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WB / "07_scripts"))

import paper_upgrade_certificate as puc  # noqa: E402


def selftest_certificate() -> dict:
    cert = puc.apply_certificate_envelope(
        {
            "family": "C006",
            "floquet_complete": False,
            "k6": "SKIP",
            "note": "cert/provenance only; P26 bridge lives in C006-v0.2.1",
            "provenance_sha256": "c006v022".ljust(64, "0")[:64],
        },
        certificate_kind="SELFTEST",
        producer="C006",
        gate="floquet_parity",
        payload_schema="SST-FLOQUET-PARITY-1.0",
        scientific=False,
        gate_status="PIPELINE_PASS",
        source_run_id="c006-v022-selftest",
        source_output_sha256="c006out".ljust(64, "1")[:64],
        gate_input_sha256="c006in".ljust(64, "2")[:64],
        synthetic_inputs=True,
    )
    assert cert["promotion_allowed"] is False
    assert puc.promotable(cert) is False
    return cert


if __name__ == "__main__":
    c = selftest_certificate()
    print(json.dumps({"status": "PASS", "promotion_allowed": c["promotion_allowed"]}, indent=2))

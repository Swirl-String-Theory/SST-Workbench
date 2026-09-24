"""Provenance integrity for modal dispatch. Extends, does not replace, upstream_gate."""

from __future__ import annotations

from typing import Any

PLACEHOLDER_HASHES = {
    "a" * 64,
    "b" * 64,
    "c" * 64,
    "d" * 64,
    "e" * 64,
}
FIXTURE_GATES = {"fixture"}
FIXTURE_RUNS = {"fixture-run"}
TEST_RUNS = {"selftest"}


def _hash_fields(cert: dict[str, Any]) -> list[str]:
    return [
        str(cert.get("source_output_sha256") or ""),
        str(cert.get("gate_input_sha256") or ""),
        str(cert.get("provenance_sha256") or ""),
    ]


def is_missing(cert: Any) -> bool:
    return not isinstance(cert, dict) or not cert


def is_fixture_cert(cert: dict[str, Any]) -> bool:
    if str(cert.get("gate") or "") in FIXTURE_GATES:
        return True
    if str(cert.get("source_run_id") or "") in FIXTURE_RUNS:
        return True
    return False


def is_placeholder_cert(cert: dict[str, Any]) -> bool:
    return any(h in PLACEHOLDER_HASHES for h in _hash_fields(cert) if h)


def is_synthetic_cert(cert: dict[str, Any]) -> bool:
    return bool(cert.get("synthetic_inputs"))


def is_selftest_cert(cert: dict[str, Any]) -> bool:
    if str(cert.get("certificate_kind") or "") == "SELFTEST":
        return True
    return str(cert.get("source_run_id") or "") in TEST_RUNS


def is_genuine_campaign(cert: dict[str, Any]) -> bool:
    if is_missing(cert) or is_fixture_cert(cert) or is_placeholder_cert(cert) or is_synthetic_cert(cert):
        return False
    if is_selftest_cert(cert):
        return False
    return str(cert.get("certificate_kind") or "") == "CAMPAIGN"


def provenance_issue(cert: Any) -> str | None:
    if is_missing(cert):
        return "missing"
    if is_fixture_cert(cert):
        return "fixture"
    if is_placeholder_cert(cert):
        return "placeholder"
    if is_synthetic_cert(cert):
        return "synthetic"
    if is_selftest_cert(cert):
        return "selftest"
    return None

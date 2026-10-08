from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _status_map(ledger: dict[str, Any]) -> dict[str, str]:
    return {
        str(r.get("gate_id")): str(r.get("status"))
        for r in ledger.get("records", [])
        if r.get("gate_id") is not None
    }


def reveal_eligibility(instance_root: Path, output_root: Path) -> dict[str, Any]:
    """Non-mutating preflight mirroring framework v1.0.4 reveal policy.

    This does *not* replace the framework REVEAL verification.  It only lets
    unattended launchers distinguish an intentionally withheld reveal from an
    operational crash.  If eligible=True, the canonical framework REVEAL path
    must still execute and verify both commitments.
    """
    root = Path(instance_root)
    out = Path(output_root)
    policy = _read_json(root / "blind_policy.json")
    summary = _read_json(out / "RUN_SUMMARY.json")
    ledger = _read_json(out / "GATE_LEDGER.json")
    frozen = _read_json(root / "preregistration" / "FROZEN_PROTOCOL.json")
    statuses = _status_map(ledger)

    decision: dict[str, Any] = {
        "schema": "A056-REVEAL-DECISION-1",
        "eligible": False,
        "performed": False,
        "prior_mode": summary.get("mode"),
        "required_gate": policy.get("reveal_requires_gate", "G3"),
        "required_gate_statuses": list(policy.get("reveal_requires_gate_status", ["PASS", "FAIL"])),
        "gate_statuses": statuses,
        "blind_gate_ledger_sha256": ledger.get("ledger_sha256"),
        "protocol_bundle_sha256": summary.get("protocol_bundle_sha256"),
        "reason": "",
    }

    if not summary or not ledger:
        decision["reason"] = "Blind FULL/CERTIFY artifacts are incomplete; reveal cannot be evaluated."
        return decision

    allowed_modes = set(policy.get("reveal_allowed_after_modes", ["FULL", "CERTIFY"]))
    if summary.get("mode") not in allowed_modes:
        decision["reason"] = f"prior mode {summary.get('mode')!r} is not reveal-eligible"
        return decision

    if summary.get("protocol_bundle_sha256") != frozen.get("bundle_sha256"):
        decision["reason"] = "blind run protocol hash differs from the currently frozen protocol"
        return decision

    req = decision["required_gate"]
    allowed_statuses = set(decision["required_gate_statuses"])
    actual = statuses.get(req)
    if actual not in allowed_statuses:
        upstream = ", ".join(f"{g}={statuses.get(g, 'MISSING')}" for g in ("G0", "G1", "G2", "G3"))
        decision["reason"] = (
            f"{req} status={actual}; requires one of {sorted(allowed_statuses)}. "
            f"Upstream status: {upstream}. Blind result remains sealed."
        )
        return decision

    if policy.get("block_reveal_on_unresolved", True):
        unresolved = [g for g, status in statuses.items() if g != "G9" and status == "UNRESOLVED"]
        if unresolved:
            decision["reason"] = f"blind gates remain UNRESOLVED: {unresolved}"
            decision["unresolved_gates"] = unresolved
            return decision

    decision["eligible"] = True
    decision["reason"] = "Framework reveal preconditions are satisfied; canonical REVEAL verification may run."
    return decision

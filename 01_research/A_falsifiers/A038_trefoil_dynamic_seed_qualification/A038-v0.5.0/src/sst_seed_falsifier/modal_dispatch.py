"""Map upstream_gate results onto SST-DYNAMIC-SEED-DISPATCH-2.0 statuses."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .provenance_lock import is_genuine_campaign, provenance_issue

REQUIRED = ("geometry", "mesh", "admissibility", "symmetry")

DISPATCH_SCHEMA = "SST-DYNAMIC-SEED-DISPATCH-2.0"
QUALIFIED = "QUALIFIED_FOR_MODAL_ANALYSIS"
BLOCKED_PROVENANCE = "BLOCKED_PROVENANCE"
BLOCKED_A034 = "BLOCKED_A034"
BLOCKED_A037 = "BLOCKED_A037"
BLOCKED_NUMERICS = "BLOCKED_NUMERICS"
SELFTEST_LOGIC = "SELFTEST_LOGIC_PASS_NON_PROMOTABLE"

KEY_STATUS = {
    "geometry": BLOCKED_PROVENANCE,
    "mesh": BLOCKED_PROVENANCE,
    "admissibility": BLOCKED_A034,
    "symmetry": BLOCKED_A037,
}


def map_dispatch_status(upstream: dict[str, Any], certs: dict[str, Any] | None = None) -> dict[str, Any]:
    certs = certs or {}
    primary = str(upstream.get("primary_block") or "OK")
    reasons = list(upstream.get("reasons") or [])
    block_codes = list(upstream.get("block_codes") or [])
    issues = {key: provenance_issue(certs.get(key)) for key in ("geometry", "mesh", "admissibility", "symmetry")}
    scientific = bool(upstream.get("qualified")) and all(is_genuine_campaign(certs.get(key) or {}) for key in ("geometry", "mesh", "admissibility", "symmetry"))
    if scientific:
        status = QUALIFIED
    elif any(issues[k] in {"fixture", "placeholder", "synthetic", "missing"} for k in ("geometry", "mesh", "admissibility", "symmetry")):
        if issues["admissibility"] in {"fixture", "placeholder", "synthetic", "missing"} and issues["geometry"] is None and issues["mesh"] is None:
            status = BLOCKED_A034
        elif issues["symmetry"] in {"fixture", "placeholder", "synthetic", "missing"} and issues["geometry"] is None and issues["mesh"] is None:
            status = BLOCKED_A037
        else:
            status = BLOCKED_PROVENANCE
    elif "NUMERICAL" in primary:
        status = BLOCKED_NUMERICS
    elif any(c.startswith("admissibility:") for c in block_codes):
        status = BLOCKED_A034
    elif any(c.startswith("symmetry:") for c in block_codes):
        status = BLOCKED_A037
    elif all(issues[k] == "selftest" or issues[k] is None for k in issues) and not scientific:
        status = SELFTEST_LOGIC if upstream.get("structural_ok") else BLOCKED_PROVENANCE
    else:
        status = BLOCKED_PROVENANCE
    extra_ignored = {k: ("ignored" if k in certs else "absent") for k in ("clock", "closure", "A030", "A035")}
    return {
        "schema": DISPATCH_SCHEMA,
        "dispatch_status": status,
        "qualified_for_modal_analysis": status == QUALIFIED,
        "dynamic_stability_claim": False,
        "primary_block": primary,
        "reasons": reasons,
        "block_codes": block_codes,
        "provenance_issues": issues,
        "non_required_certs": extra_ignored,
        "promotable_science_claim": False if status != QUALIFIED else False,
        "dispatch_eligibility_only": True,
    }


class ModalDispatchBlocked(RuntimeError):
    """Scientific entry was blocked by provenance-aware modal dispatch."""


def load_upstream_certs(out: str | Path) -> tuple[dict[str, Any] | None, Path | None]:
    candidates = []
    env = os.environ.get("SST_A038_UPSTREAM", "").strip()
    if env:
        candidates.append(Path(env))
    out = Path(out)
    candidates.extend(
        [
            out / "paper_upgrade" / "upstream_certs.json",
            out.parent / "paper_upgrade" / "upstream_certs.json",
        ]
    )
    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8")), path
    return None, None


def evaluate_certs(certs: dict[str, Any] | None) -> dict[str, Any]:
    certs = certs or {}
    reasons = []
    block_codes = []
    for key in REQUIRED:
        issue = provenance_issue(certs.get(key))
        if issue:
            reasons.append(f"{key}:provenance:{issue}")
            block_codes.append(f"{key}:BLOCKED_UPSTREAM_PROVENANCE" if issue != "selftest" else f"{key}:BLOCKED_UPSTREAM_SELFTEST")
        elif not is_genuine_campaign(certs.get(key) or {}):
            reasons.append(f"{key}:not-genuine-campaign")
            block_codes.append(f"{key}:BLOCKED_UPSTREAM_MISSING_CAMPAIGN")
    authorized = not reasons
    primary = "OK" if authorized else (block_codes[0].split(":", 1)[1] if block_codes else "BLOCKED_UPSTREAM_MISSING_CAMPAIGN")
    upstream = {
        "qualified": authorized,
        "reasons": reasons,
        "block_codes": block_codes,
        "primary_block": primary,
        "downstream_authorized": authorized,
        "structural_ok": all(provenance_issue(certs.get(k)) == "selftest" for k in REQUIRED) if certs else False,
    }
    return map_dispatch_status(upstream, certs)


def enforce_modal_dispatch(out: str | Path, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or {}
    run_kind = str(cfg.get("run_kind", "blind_scientific"))
    certs, _path = load_upstream_certs(out)
    result = evaluate_certs(certs)
    dest_dir = Path(out) / "paper_upgrade"
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "modal_dispatch.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if run_kind == "blind_scientific" and result.get("dispatch_status") != QUALIFIED:
        raise ModalDispatchBlocked(result.get("dispatch_status") or BLOCKED_PROVENANCE)
    return result

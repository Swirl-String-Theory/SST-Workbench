"""PC04 — A038-v0.5.1 promotion firewall + preflight-only mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

WB = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WB / "07_scripts"))

import paper_upgrade_certificate as puc  # noqa: E402

REQUIRED = {
    "A034": "SST-ADMISSIBILITY-1.0",
    "A037": "SST-SYMMETRY-SELECTION-1.0",
}


def map_upstream(cert: dict[str, Any] | None) -> str:
    code = puc.blocked_reason_code(cert)
    if code == "OK":
        return "OK"
    # Never collapse to FAIL_TREFOIL
    assert code.startswith("BLOCKED_UPSTREAM_") or code == "BLOCKED_UPSTREAM_NOT_PROMOTABLE"
    return code


def preflight(certs: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    blocks: list[str] = []
    details: dict[str, Any] = {}
    for family, schema in REQUIRED.items():
        cert = certs.get(family)
        code = map_upstream(cert)
        if isinstance(cert, dict) and cert.get("payload_schema") not in (None, schema):
            code = "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
        ok, why = (False, "missing")
        if isinstance(cert, dict):
            ok, why = puc.require_promotable(cert)
        details[family] = {"block": code, "require_promotable": ok, "why": why}
        if code != "OK":
            blocks.append(f"{family}:{code}")
    authorized = not blocks
    primary = "OK" if authorized else blocks[0].split(":", 1)[1]
    return {
        "qualified": authorized,
        "primary_block": primary,
        "block_codes": blocks,
        "details": details,
        "fail_trefoil": False,
        "mode": "preflight",
    }


def _mk(
    family: str,
    schema: str,
    *,
    kind: str = "CAMPAIGN",
    nq: dict[str, str] | None = None,
    status: str = "PASS",
    synthetic: bool = False,
) -> dict[str, Any]:
    return puc.apply_certificate_envelope(
        {"family": family, "provenance_sha256": (family + "p").ljust(64, "0")[:64]},
        certificate_kind=kind,
        producer=family,
        gate="pc04",
        payload_schema=schema,
        scientific=kind == "CAMPAIGN",
        gate_status=status,
        source_run_id=f"{family}-run",
        source_output_sha256=(family + "o").ljust(64, "1")[:64],
        gate_input_sha256=(family + "i").ljust(64, "2")[:64],
        numerical_qualification=nq or {"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=synthetic,
    )


def selftest() -> dict[str, Any]:
    good = {
        "A034": _mk("A034", "SST-ADMISSIBILITY-1.0"),
        "A037": _mk("A037", "SST-SYMMETRY-SELECTION-1.0"),
    }
    g = preflight(good)
    assert g["qualified"] and g["fail_trefoil"] is False

    selftest_certs = {
        "A034": _mk("A034", "SST-ADMISSIBILITY-1.0", kind="SELFTEST", synthetic=True),
        "A037": _mk("A037", "SST-SYMMETRY-SELECTION-1.0", kind="SELFTEST", synthetic=True),
    }
    r_st = preflight(selftest_certs)
    assert not r_st["qualified"]
    assert r_st["primary_block"] == "BLOCKED_UPSTREAM_SELFTEST"
    assert "FAIL_TREFOIL" not in json.dumps(r_st)

    num = {
        "A034": _mk("A034", "SST-ADMISSIBILITY-1.0"),
        "A037": _mk(
            "A037",
            "SST-SYMMETRY-SELECTION-1.0",
            nq={"temporal": "FAIL", "spatial": "PASS", "mesh": "PASS"},
            status="INVALID_NUMERICS",
        ),
    }
    r_num = preflight(num)
    assert not r_num["qualified"]
    assert r_num["primary_block"] == "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"

    missing = {"A034": good["A034"], "A037": None}
    r_miss = preflight(missing)
    assert r_miss["primary_block"] == "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
    return {"status": "PASS", "cases": ["good", "selftest", "numerical", "missing"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--a034")
    ap.add_argument("--a037")
    ap.add_argument("--out")
    ns = ap.parse_args(argv)
    if ns.selftest or (not ns.preflight):
        out = selftest()
        text = json.dumps(out, indent=2, sort_keys=True)
        print(text)
        return 0 if out["status"] == "PASS" else 1
    certs = {
        "A034": json.loads(Path(ns.a034).read_text(encoding="utf-8")) if ns.a034 else None,
        "A037": json.loads(Path(ns.a037).read_text(encoding="utf-8")) if ns.a037 else None,
    }
    result = preflight(certs)
    text = json.dumps(result, indent=2, sort_keys=True)
    if ns.out:
        Path(ns.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["qualified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

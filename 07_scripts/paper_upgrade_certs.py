"""Paper-upgrade certificate emit/consume helpers (PU02 / PU02b / PC00).

Canonical path: ``<out>/paper_upgrade/certificate.json``

Envelope schema: ``SST-SCIENTIFIC-CERTIFICATE-1.0`` (see paper_upgrade_certificate.py).

Env overrides for consumers:
  SST_A034_CERT, SST_A037_CERT, SST_A030_CERT
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from paper_upgrade_certificate import (
    SCHEMA,
    apply_certificate_envelope,
    blocked_reason_code,
    promotable,
    promotion_eligible,
    provenance_sha256,
    require_promotable,
    stamp_promotion_allowed,
)


def cert_path(out: str | Path) -> Path:
    p = Path(out) / "paper_upgrade"
    p.mkdir(parents=True, exist_ok=True)
    return p / "certificate.json"


# Back-compat aliases used by older tests / callers
apply_certificate_semantics = apply_certificate_envelope
compute_promotion_allowed = promotion_eligible


def write_certificate(out: str | Path, cert: dict[str, Any]) -> Path:
    path = cert_path(out)
    cert = dict(cert)
    if cert.get("schema") != SCHEMA or "certificate_kind" not in cert:
        cert = apply_certificate_envelope(
            cert,
            certificate_kind=cert.get("certificate_kind") or "SELFTEST",
            producer=cert.get("producer") or cert.get("family"),
            payload_schema=cert.get("payload_schema"),
        )
    else:
        cert = stamp_promotion_allowed(cert)
    body = {k: v for k, v in cert.items() if k != "provenance_sha256"}
    cert["provenance_sha256"] = provenance_sha256(body)
    path.write_text(json.dumps(cert, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_certificate(path: str | Path | None = None, *, env_key: str | None = None) -> dict[str, Any]:
    if env_key:
        env_path = os.environ.get(env_key, "").strip()
        if env_path:
            path = env_path
    if path is None:
        raise FileNotFoundError("certificate path not provided")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def run_gate(gate_py: Path, payload: dict[str, Any], output: Path | None = None) -> dict[str, Any]:
    import tempfile

    gate_py = Path(gate_py).resolve()
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.json"
        outp = Path(td) / "out.json"
        inp.write_text(json.dumps(payload), encoding="utf-8")
        cmd = [sys.executable, str(gate_py), "--input", str(inp), "--output", str(outp)]
        proc = subprocess.run(cmd, cwd=str(gate_py.parent.parent), capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"gate failed rc={proc.returncode}: {proc.stderr or proc.stdout}")
        data = json.loads(outp.read_text(encoding="utf-8"))
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data


def emit_a034(
    *,
    out: str | Path,
    g: list[float],
    H: list[list[float]],
    C: list[list[float]],
    gate_py: Path | None = None,
    certificate_kind: str = "CAMPAIGN",
    source_run_id: str | None = None,
    source_output_sha256: str | None = None,
    gate_input_sha256: str | None = None,
    numerical_qualification: dict[str, str] | None = None,
) -> Path:
    if gate_py is None:
        raise ValueError("gate_py required")
    result = run_gate(gate_py, {"operation": "classify", "g": g, "H": H, "C": C})
    label = result.get("label") or result.get("classification")
    status = "PASS" if label == "ENERGETICALLY_ADMISSIBLE" else ("QUALIFIED" if label == "SOFT_MODE" else "FAIL")
    body = {
        "family": "A034",
        "classification": label,
        "constrained_gradient_norm": result.get("constrained_gradient_norm"),
        "tangent_hessian_eigenvalues": result.get("tangent_hessian_eigenvalues"),
        "soft_mode": result.get("soft_mode"),
        "gate_result": result,
        "payload": {
            "classification": label,
            "constrained_gradient_norm": result.get("constrained_gradient_norm"),
            "tangent_hessian_eigenvalues": result.get("tangent_hessian_eigenvalues"),
        },
    }
    cert = apply_certificate_envelope(
        body,
        certificate_kind=certificate_kind,
        producer="A034",
        gate="constrained_admissibility",
        payload_schema="SST-ADMISSIBILITY-1.0",
        gate_status=status,
        source_run_id=source_run_id,
        source_output_sha256=source_output_sha256,
        gate_input_sha256=gate_input_sha256,
        numerical_qualification=numerical_qualification,
        synthetic_inputs=(certificate_kind == "SELFTEST"),
    )
    return write_certificate(out, cert)


def emit_a037(
    *,
    out: str | Path,
    R_out: list[list[float]],
    R_drive: list[list[float]],
    q_plus: list[list[float]] | None = None,
    q_minus: list[list[float]] | None = None,
    delta: list[float] | None = None,
    gate_py: Path | None = None,
    certificate_kind: str = "CAMPAIGN",
    source_run_id: str | None = None,
    source_output_sha256: str | None = None,
    gate_input_sha256: str | None = None,
    numerical_qualification: dict[str, str] | None = None,
    scientific_status: str = "PASS",
) -> Path:
    if gate_py is None:
        raise ValueError("gate_py required")
    sel = run_gate(
        gate_py,
        {"operation": "selection_matrix", "R_out": R_out, "R_drive": R_drive},
    )
    extras: dict[str, Any] = {}
    if q_plus is not None and q_minus is not None and delta is not None:
        extras["has_response_inputs"] = True
    body = {
        "family": "A037",
        "selection_matrix": sel if isinstance(sel, list) else sel,
        "payload": {"selection_matrix": sel},
        **extras,
    }
    cert = apply_certificate_envelope(
        body,
        certificate_kind=certificate_kind,
        producer="A037",
        gate="symmetry_selection",
        payload_schema="SST-SYMMETRY-SELECTION-1.0",
        gate_status=scientific_status,
        source_run_id=source_run_id,
        source_output_sha256=source_output_sha256,
        gate_input_sha256=gate_input_sha256,
        numerical_qualification=numerical_qualification,
        synthetic_inputs=(certificate_kind == "SELFTEST"),
    )
    return write_certificate(out, cert)


def emit_a030(
    *,
    out: str | Path,
    u00: list[complex] | list[list[float]],
    u10: list[complex] | list[list[float]],
    u11: list[complex] | list[list[float]],
    u01: list[complex] | list[list[float]],
    gate_py: Path | None = None,
    certificate_kind: str = "CAMPAIGN",
    source_run_id: str | None = None,
    source_output_sha256: str | None = None,
    gate_input_sha256: str | None = None,
    numerical_qualification: dict[str, str] | None = None,
) -> Path:
    if gate_py is None:
        raise ValueError("gate_py required")
    payload = {
        "operation": "plaquette_curvature",
        "u00": u00,
        "u10": u10,
        "u11": u11,
        "u01": u01,
    }
    result = run_gate(gate_py, payload)
    body = {
        "family": "A030",
        "plaquette_curvature": result.get("plaquette_curvature", result),
        "gate_result": result,
        "payload": result,
    }
    cert = apply_certificate_envelope(
        body,
        certificate_kind=certificate_kind,
        producer="A030",
        gate="geometric_phase",
        payload_schema="SST-GEOMETRIC-PHASE-1.0",
        gate_status="PASS",
        source_run_id=source_run_id,
        source_output_sha256=source_output_sha256,
        gate_input_sha256=gate_input_sha256,
        numerical_qualification=numerical_qualification,
        synthetic_inputs=(certificate_kind == "SELFTEST"),
    )
    return write_certificate(out, cert)


def consume_a034_cert(cert: dict[str, Any], gate_py: Path) -> dict[str, Any]:
    return run_gate(gate_py, {"operation": "consume_a034", "cert": cert})


def upstream_gate_a038(certs: dict[str, Any], gate_py: Path) -> dict[str, Any]:
    return run_gate(gate_py, {"operation": "upstream_gate", "certs": certs})


def dependency_guard_a030(a030_certificate: dict[str, Any], gate_py: Path) -> dict[str, Any]:
    return run_gate(gate_py, {"operation": "dependency_guard", "a030_certificate": a030_certificate})


def synthetic_a034_payload() -> dict[str, Any]:
    return {
        "g": [7.0, 0.0, 0.0],
        "H": [[-3.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 4.0]],
        "C": [[1.0, 0.0, 0.0]],
    }


def synthetic_a037_payload() -> dict[str, Any]:
    return {
        "R_out": [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "R_drive": [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    }


def campaign_fixture_cert(
    *,
    family: str,
    payload_schema: str,
    status: str = "PASS",
    classification: str | None = None,
    gate: str = "fixture",
) -> dict[str, Any]:
    """Minimal promotable CAMPAIGN cert for consumer unit tests."""
    body: dict[str, Any] = {
        "family": family,
        "status": status,
    }
    if classification is not None:
        body["classification"] = classification
        body["payload"] = {"classification": classification}
    return apply_certificate_envelope(
        body,
        certificate_kind="CAMPAIGN",
        producer=family,
        gate=gate,
        payload_schema=payload_schema,
        gate_status=status,
        source_run_id="fixture-run",
        source_output_sha256="c" * 64,
        gate_input_sha256="d" * 64,
        numerical_qualification={"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="paper_upgrade_certs")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("emit-a034-synthetic")
    p.add_argument("--out", required=True)
    p.add_argument("--gate", required=True)

    p = sub.add_parser("emit-a037-synthetic")
    p.add_argument("--out", required=True)
    p.add_argument("--gate", required=True)

    p = sub.add_parser("emit-a034-campaign")
    p.add_argument("--out", required=True)
    p.add_argument("--gate", required=True)
    p.add_argument("--from-out", default=None, help="Campaign output dir (default: --out)")
    p.add_argument("--payload", default=None, help="Optional JSON payload override")

    p = sub.add_parser("emit-a037-campaign")
    p.add_argument("--out", required=True)
    p.add_argument("--gate", required=True)
    p.add_argument("--from-out", default=None, help="Campaign output dir (default: --out)")
    p.add_argument("--payload", default=None, help="Optional JSON payload override")

    p = sub.add_parser("consume-a034")
    p.add_argument("--cert", required=True)
    p.add_argument("--gate", required=True)
    p.add_argument("--output", default=None)

    p = sub.add_parser("upstream-a038")
    p.add_argument("--certs", required=True)
    p.add_argument("--gate", required=True)
    p.add_argument("--output", default=None)

    p = sub.add_parser("guard-a030")
    p.add_argument("--cert", required=True)
    p.add_argument("--gate", required=True)
    p.add_argument("--output", default=None)

    p = sub.add_parser("write-a038-upstream")
    p.add_argument("--out", required=True)
    p.add_argument("--a034", required=True)
    p.add_argument("--a037", required=True)

    p = sub.add_parser("check-promotable")
    p.add_argument("--cert", required=True)

    ns = ap.parse_args(argv)
    if ns.cmd == "emit-a034-synthetic":
        path = emit_a034(
            out=ns.out,
            gate_py=Path(ns.gate),
            certificate_kind="SELFTEST",
            **synthetic_a034_payload(),
        )
        print(path)
        return 0
    if ns.cmd == "emit-a037-synthetic":
        path = emit_a037(
            out=ns.out,
            gate_py=Path(ns.gate),
            certificate_kind="SELFTEST",
            **synthetic_a037_payload(),
        )
        print(path)
        return 0
    if ns.cmd == "emit-a034-campaign":
        from paper_upgrade_campaign_payload import build_a034_dual_and_payload
        from paper_upgrade_numerics import qualify_a034_from_basic_out

        src = Path(ns.from_out or ns.out)
        if ns.payload:
            payload = json.loads(Path(ns.payload).read_text(encoding="utf-8"))
        else:
            payload = build_a034_dual_and_payload(src)
        nq_report = qualify_a034_from_basic_out(src)
        nq = nq_report["numerical_qualification"]
        nq_path = Path(ns.out) / "paper_upgrade" / "numerical_qualification.json"
        nq_path.parent.mkdir(parents=True, exist_ok=True)
        nq_path.write_text(json.dumps(nq_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not all(nq.get(k) == "PASS" for k in ("temporal", "spatial", "mesh")):
            # Still write a non-promotable CAMPAIGN envelope recording INVALID_NUMERICS.
            path = emit_a034(
                out=ns.out,
                gate_py=Path(ns.gate),
                certificate_kind="CAMPAIGN",
                numerical_qualification=nq,
                source_run_id=payload.get("source_run_id"),
                source_output_sha256=payload.get("source_output_sha256"),
                gate_input_sha256=payload.get("gate_input_sha256"),
                g=payload["g"],
                H=payload["H"],
                C=payload["C"],
            )
            cert = json.loads(path.read_text(encoding="utf-8"))
            cert["status"] = "FAIL"
            cert["scientific"] = True
            cert["invalid_numerics"] = True
            write_certificate(ns.out, cert)
            print(path)
            return 2
        path = emit_a034(
            out=ns.out,
            gate_py=Path(ns.gate),
            certificate_kind="CAMPAIGN",
            numerical_qualification=nq,
            source_run_id=payload.get("source_run_id"),
            source_output_sha256=payload.get("source_output_sha256"),
            gate_input_sha256=payload.get("gate_input_sha256"),
            g=payload["g"],
            H=payload["H"],
            C=payload["C"],
        )
        print(path)
        cert = json.loads(path.read_text(encoding="utf-8"))
        return 0 if promotable(cert) else 1
    if ns.cmd == "emit-a037-campaign":
        from paper_upgrade_campaign_payload import build_a037_payload
        from paper_upgrade_numerics import qualify_a037_from_blind_out

        src = Path(ns.from_out or ns.out)
        if ns.payload:
            payload = json.loads(Path(ns.payload).read_text(encoding="utf-8"))
        else:
            payload = build_a037_payload(src)
        nq_report = qualify_a037_from_blind_out(src)
        nq = nq_report["numerical_qualification"]
        nq_path = Path(ns.out) / "paper_upgrade" / "numerical_qualification.json"
        nq_path.parent.mkdir(parents=True, exist_ok=True)
        nq_path.write_text(json.dumps(nq_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not all(nq.get(k) == "PASS" for k in ("temporal", "spatial", "mesh")):
            path = emit_a037(
                out=ns.out,
                gate_py=Path(ns.gate),
                certificate_kind="CAMPAIGN",
                numerical_qualification=nq,
                source_run_id=payload.get("source_run_id"),
                source_output_sha256=payload.get("source_output_sha256"),
                gate_input_sha256=payload.get("gate_input_sha256"),
                scientific_status="FAIL",
                R_out=payload["R_out"],
                R_drive=payload["R_drive"],
            )
            cert = json.loads(path.read_text(encoding="utf-8"))
            cert["invalid_numerics"] = True
            write_certificate(ns.out, cert)
            print(path)
            return 2
        path = emit_a037(
            out=ns.out,
            gate_py=Path(ns.gate),
            certificate_kind="CAMPAIGN",
            numerical_qualification=nq,
            source_run_id=payload.get("source_run_id"),
            source_output_sha256=payload.get("source_output_sha256"),
            gate_input_sha256=payload.get("gate_input_sha256"),
            scientific_status=payload.get("scientific_status") or "PASS",
            R_out=payload["R_out"],
            R_drive=payload["R_drive"],
        )
        print(path)
        cert = json.loads(path.read_text(encoding="utf-8"))
        return 0 if promotable(cert) else 1
    if ns.cmd == "consume-a034":
        cert = load_certificate(ns.cert)
        result = consume_a034_cert(cert, Path(ns.gate))
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if ns.output:
            Path(ns.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0 if result.get("accepted") else 1
    if ns.cmd == "upstream-a038":
        certs = json.loads(Path(ns.certs).read_text(encoding="utf-8"))
        result = upstream_gate_a038(certs, Path(ns.gate))
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if ns.output:
            Path(ns.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0 if result.get("downstream_authorized") else 1
    if ns.cmd == "guard-a030":
        cert = load_certificate(ns.cert)
        result = dependency_guard_a030(cert, Path(ns.gate))
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if ns.output:
            Path(ns.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0 if result.get("migration_authorized") else 1
    if ns.cmd == "check-promotable":
        cert = load_certificate(ns.cert)
        ok, why = require_promotable(cert)
        print(json.dumps({"promotable": ok, "reason": why, "blocked": blocked_reason_code(cert)}, indent=2))
        return 0 if ok else 1
    if ns.cmd == "write-a038-upstream":
        out = Path(ns.out)
        a034 = load_certificate(ns.a034)
        a037 = load_certificate(ns.a037)
        certs = {
            "geometry": campaign_fixture_cert(family="geometry", payload_schema="SST-GEOMETRY-1.0"),
            "mesh": campaign_fixture_cert(family="mesh", payload_schema="SST-MESH-1.0"),
            "admissibility": a034,
            "symmetry": a037,
        }
        dest = out / "paper_upgrade" / "upstream_certs.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(certs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(dest)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

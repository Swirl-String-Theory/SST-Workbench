from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import importlib.util
import numpy as np

def _write(obj, path):
    text=json.dumps(obj, indent=2, sort_keys=True)
    if path: Path(path).write_text(text+"\n", encoding="utf-8")
    else: print(text)

def _arr(x): return np.asarray(x, dtype=float)

REQUIRED = ("geometry", "mesh", "admissibility", "symmetry")
PAYLOAD_SCHEMAS = {
    "admissibility": "SST-ADMISSIBILITY-1.0",
    "symmetry": "SST-SYMMETRY-SELECTION-1.0",
}

def _cert_mod():
    for parent in Path(__file__).resolve().parents:
        cand = parent / "07_scripts" / "paper_upgrade_certificate.py"
        if cand.is_file():
            name = "paper_upgrade_certificate"
            if name in sys.modules:
                return sys.modules[name]
            spec = importlib.util.spec_from_file_location(name, cand)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("paper_upgrade_certificate not found")

def validate_certificate(cert, expected_key=None):
    puc = _cert_mod()
    if not isinstance(cert, dict):
        return False, "not-object", puc.blocked_reason_code(cert if isinstance(cert, dict) else None)
    if expected_key in PAYLOAD_SCHEMAS:
        ps = cert.get("payload_schema")
        if ps and ps != PAYLOAD_SCHEMAS[expected_key]:
            return False, "payload-schema-mismatch", "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
    ok, why = puc.require_promotable(cert)
    if not ok:
        return False, why, puc.blocked_reason_code(cert)
    return True, "ok", "OK"

def upstream_gate(certs):
    reasons = []
    block_codes = []
    for key in REQUIRED:
        ok, why, code = validate_certificate(certs.get(key), expected_key=key)
        if not ok:
            reasons.append(f"{key}:{why}")
            block_codes.append(f"{key}:{code}")
    authorized = not reasons
    # Prefer numerical qualification block code when present
    primary = "OK"
    if not authorized:
        primary = next((c.split(":", 1)[1] for c in block_codes if "NUMERICAL" in c), None)
        if primary is None:
            primary = block_codes[0].split(":", 1)[1] if block_codes else "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
    return {
        "qualified": authorized,
        "reasons": reasons,
        "block_codes": block_codes,
        "primary_block": primary,
        "downstream_authorized": authorized,
    }

def selftest():
    puc = _cert_mod()
    def mk(family, payload_schema, gate):
        c = puc.apply_certificate_envelope(
            {"family": family, "provenance_sha256": "a" * 64},
            certificate_kind="CAMPAIGN",
            producer=family,
            gate=gate,
            payload_schema=payload_schema,
            gate_status="PASS",
            source_run_id="selftest",
            source_output_sha256="c" * 64,
            gate_input_sha256="d" * 64,
            numerical_qualification={"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
            synthetic_inputs=False,
        )
        c["provenance_sha256"] = "a" * 64
        return c
    good = {
        "geometry": mk("geometry", "SST-GEOMETRY-1.0", "geometry"),
        "mesh": mk("mesh", "SST-MESH-1.0", "mesh"),
        "admissibility": mk("A034", "SST-ADMISSIBILITY-1.0", "constrained_admissibility"),
        "symmetry": mk("A037", "SST-SYMMETRY-SELECTION-1.0", "symmetry_selection"),
    }
    assert upstream_gate(good)["qualified"]
    bad = dict(good)
    bad["symmetry"] = puc.apply_certificate_envelope(
        {"family": "A037", "provenance_sha256": "b" * 64},
        certificate_kind="CAMPAIGN",
        producer="A037",
        gate="symmetry_selection",
        payload_schema="SST-SYMMETRY-SELECTION-1.0",
        gate_status="FAIL",
        source_run_id="selftest",
        source_output_sha256="c" * 64,
        gate_input_sha256="d" * 64,
        numerical_qualification={"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
    )
    bad["symmetry"]["provenance_sha256"] = "b" * 64
    assert not upstream_gate(bad)["qualified"]
    synth = dict(good)
    synth["admissibility"] = puc.apply_certificate_envelope(
        {"family": "A034", "provenance_sha256": "c" * 64, "classification": "ENERGETICALLY_ADMISSIBLE"},
        certificate_kind="SELFTEST",
        producer="A034",
        gate="constrained_admissibility",
        payload_schema="SST-ADMISSIBILITY-1.0",
    )
    synth["admissibility"]["provenance_sha256"] = "c" * 64
    r = upstream_gate(synth)
    assert not r["qualified"]
    assert any("SELFTEST" in c for c in r["block_codes"])
    num = dict(good)
    num["symmetry"] = puc.apply_certificate_envelope(
        {"family": "A037", "provenance_sha256": "e" * 64},
        certificate_kind="CAMPAIGN",
        producer="A037",
        gate="symmetry_selection",
        payload_schema="SST-SYMMETRY-SELECTION-1.0",
        gate_status="PASS",
        source_run_id="selftest",
        source_output_sha256="c" * 64,
        gate_input_sha256="d" * 64,
        numerical_qualification={"temporal": "FAIL", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
    )
    num["symmetry"]["provenance_sha256"] = "e" * 64
    r2 = upstream_gate(num)
    assert not r2["qualified"]
    assert r2["primary_block"] == "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"
    return {"status": "PASS", "required": list(REQUIRED)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--selftest',action='store_true'); ap.add_argument('--input'); ap.add_argument('--output')
    ns=ap.parse_args()
    if ns.selftest: return _write(selftest(),ns.output)
    if not ns.input: ap.error('--input required unless --selftest')
    data=json.loads(Path(ns.input).read_text(encoding='utf-8'))
    op=data.pop('operation',None)
    if not op or op not in globals() or not callable(globals()[op]): raise SystemExit(f'unknown operation: {op}')
    _write(globals()[op](**data),ns.output)
if __name__=='__main__': main()

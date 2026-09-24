from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import importlib.util
import numpy as np

def _pack_mod(name):
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return __import__(f"sst_seed_falsifier.{name}", fromlist=["sst_seed_falsifier"])

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
    lock = _pack_mod("provenance_lock")
    dispatch = _pack_mod("modal_dispatch")
    reasons = []
    block_codes = []
    structural_ok = True
    for key in REQUIRED:
        cert = certs.get(key) if isinstance(certs, dict) else None
        ok, why, code = validate_certificate(cert, expected_key=key)
        issue = lock.provenance_issue(cert)
        if issue in {"fixture", "placeholder", "synthetic", "missing"}:
            ok = False
            why = f"provenance:{issue}"
            code = "BLOCKED_UPSTREAM_PROVENANCE"
        elif issue == "selftest":
            structural_ok = structural_ok and isinstance(cert, dict) and bool(cert.get("schema"))
            ok = False
            why = "provenance:selftest"
            code = "BLOCKED_UPSTREAM_SELFTEST"
        if not ok:
            reasons.append(f"{key}:{why}")
            block_codes.append(f"{key}:{code}")
            if issue != "selftest":
                structural_ok = False
    authorized = not reasons
    primary = "OK"
    if not authorized:
        primary = next((c.split(":", 1)[1] for c in block_codes if "NUMERICAL" in c), None)
        if primary is None:
            primary = next((c.split(":", 1)[1] for c in block_codes if "PROVENANCE" in c or "SELFTEST" in c), None)
        if primary is None:
            primary = block_codes[0].split(":", 1)[1] if block_codes else "BLOCKED_UPSTREAM_MISSING_CAMPAIGN"
    result = {
        "qualified": authorized,
        "reasons": reasons,
        "block_codes": block_codes,
        "primary_block": primary,
        "downstream_authorized": authorized,
        "structural_ok": bool(structural_ok and not authorized and all(
            lock.is_selftest_cert(certs.get(k) or {}) for k in REQUIRED if isinstance(certs, dict)
        )),
    }
    result.update(dispatch.map_dispatch_status(result, certs if isinstance(certs, dict) else {}))
    return result

def selftest():
    puc = _cert_mod()
    def mk(family, payload_schema, gate, *, kind="CAMPAIGN", run_id="genuine-run", out_h=None, in_h=None, status="PASS", nq=None, gate_name=None):
        out_h = out_h or hashlib_unique(family + run_id + "out")
        in_h = in_h or hashlib_unique(family + run_id + "in")
        c = puc.apply_certificate_envelope(
            {"family": family, "provenance_sha256": hashlib_unique(family + run_id + "prov")},
            certificate_kind=kind,
            producer=family,
            gate=gate_name or gate,
            payload_schema=payload_schema,
            gate_status=status,
            source_run_id=run_id,
            source_output_sha256=out_h,
            gate_input_sha256=in_h,
            numerical_qualification=nq or {"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
            synthetic_inputs=False,
        )
        return c
    def hashlib_unique(seed):
        import hashlib
        return hashlib.sha256(seed.encode()).hexdigest()
    good = {
        "geometry": mk("geometry", "SST-GEOMETRY-1.0", "geometry"),
        "mesh": mk("mesh", "SST-MESH-1.0", "mesh"),
        "admissibility": mk("A034", "SST-ADMISSIBILITY-1.0", "constrained_admissibility"),
        "symmetry": mk("A037", "SST-SYMMETRY-SELECTION-1.0", "symmetry_selection"),
    }
    g = upstream_gate(good)
    assert g["qualified"] and g["dispatch_status"] == "QUALIFIED_FOR_MODAL_ANALYSIS"
    missing = dict(good)
    missing.pop("mesh")
    r_missing = upstream_gate(missing)
    assert not r_missing["qualified"]
    fixture = dict(good)
    fixture["geometry"] = mk("geometry", "SST-GEOMETRY-1.0", "geometry", gate_name="fixture", run_id="fixture-run", out_h="c"*64, in_h="d"*64)
    r_fix = upstream_gate(fixture)
    assert not r_fix["qualified"]
    assert r_fix["dispatch_status"] == "BLOCKED_PROVENANCE"
    selftest_bundle = {
        "geometry": mk("geometry", "SST-GEOMETRY-1.0", "geometry", kind="SELFTEST", run_id="selftest"),
        "mesh": mk("mesh", "SST-MESH-1.0", "mesh", kind="SELFTEST", run_id="selftest"),
        "admissibility": mk("A034", "SST-ADMISSIBILITY-1.0", "constrained_admissibility", kind="SELFTEST", run_id="selftest"),
        "symmetry": mk("A037", "SST-SYMMETRY-SELECTION-1.0", "symmetry_selection", kind="SELFTEST", run_id="selftest"),
    }
    r_st = upstream_gate(selftest_bundle)
    assert not r_st["qualified"]
    assert r_st["dispatch_status"] != "QUALIFIED_FOR_MODAL_ANALYSIS"
    num = dict(good)
    num["symmetry"] = mk("A037", "SST-SYMMETRY-SELECTION-1.0", "symmetry_selection", nq={"temporal": "FAIL", "spatial": "PASS", "mesh": "PASS"})
    r2 = upstream_gate(num)
    assert not r2["qualified"]
    assert r2["primary_block"] == "BLOCKED_UPSTREAM_NUMERICAL_QUALIFICATION"
    assert r2["dispatch_status"] == "BLOCKED_NUMERICS"
    extra = dict(good)
    extra["A030"] = {"certificate_kind": "CAMPAIGN", "status": "FAIL"}
    extra["A035"] = {"certificate_kind": "CAMPAIGN", "status": "FAIL"}
    assert upstream_gate(extra)["qualified"]
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

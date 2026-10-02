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

REQUIRED_SCHEMA = "SST-GEOMETRIC-PHASE-1.0"

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

def dependency_guard(a030_certificate):
    puc = _cert_mod()
    if not isinstance(a030_certificate, dict):
        return {"migration_authorized": False, "required_schema": REQUIRED_SCHEMA, "reason": "not-object"}
    if a030_certificate.get("family") != "A030":
        return {"migration_authorized": False, "required_schema": REQUIRED_SCHEMA, "reason": "family"}
    ps = a030_certificate.get("payload_schema")
    if ps != REQUIRED_SCHEMA:
        return {"migration_authorized": False, "required_schema": REQUIRED_SCHEMA, "reason": "schema"}
    ok, why = puc.require_promotable(a030_certificate)
    return {
        "migration_authorized": bool(ok),
        "required_schema": REQUIRED_SCHEMA,
        "reason": why,
        "block": puc.blocked_reason_code(a030_certificate),
    }

def selftest():
    puc = _cert_mod()
    good = puc.apply_certificate_envelope(
        {"family": "A030"},
        certificate_kind="CAMPAIGN",
        producer="A030",
        gate="geometric_phase",
        payload_schema=REQUIRED_SCHEMA,
        gate_status="PASS",
        source_run_id="selftest",
        source_output_sha256="c" * 64,
        gate_input_sha256="d" * 64,
        numerical_qualification={"temporal": "PASS", "spatial": "PASS", "mesh": "PASS"},
        synthetic_inputs=False,
    )
    assert dependency_guard(good)["migration_authorized"]
    assert not dependency_guard({})["migration_authorized"]
    synth = puc.apply_certificate_envelope(
        {"family": "A030"},
        certificate_kind="SELFTEST",
        producer="A030",
        gate="geometric_phase",
        payload_schema=REQUIRED_SCHEMA,
    )
    assert not dependency_guard(synth)["migration_authorized"]
    return {"status": "PASS", "policy": "DEFERRED_UNTIL_A030_CERTIFIED"}

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

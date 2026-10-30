"""A075 v0.2.2: pre-freeze structural check against Framework v1.1.0.
This never writes files, creates blind material, freezes, runs physics, or changes status.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
load_framework()
from sst_falsifier.science_contract import validate_science_contract
from sst_falsifier.report import validate_report
from sst_falsifier.source_registry import validate_source_contract
from sst_falsifier.gates import validate_gate_plan

def main() -> int:
    checks=[
        ("science_contract.json",lambda p:validate_science_contract(json.loads(p.read_text(encoding="utf8")))),
        ("report/FALSIFIER_REPORT.tex",lambda p:validate_report(p,require_complete=True)),
        ("source_contract.json",lambda p:validate_source_contract(json.loads(p.read_text(encoding="utf8")))),
        ("gate_plan.json",validate_gate_plan),
    ]
    failures=0
    for rel,checker in checks:
        path=ROOT/rel
        try: errors=checker(path) if path.exists() else ["missing file"]
        except Exception as exc: errors=[f"{type(exc).__name__}: {exc}"]
        print(f"{rel}: {'PASS' if not errors else 'FAIL'}")
        for e in errors: print('  -',e)
        failures+=bool(errors)
    p=ROOT/'preregistration'/'FROZEN_PROTOCOL.json'
    if p.exists():
        print('FROZEN_PROTOCOL.json exists: DO NOT change protocol files or re-freeze after patch')
        failures+=1
    return 1 if failures else 0
if __name__=='__main__': raise SystemExit(main())

from pathlib import Path
import argparse,json
from sst_falsifier.science_contract import validate_science_contract,load_science_contract
from sst_falsifier.report import validate_report
from sst_falsifier.source_registry import validate_source_contract
from sst_falsifier.gates import validate_gate_plan
import json
p=argparse.ArgumentParser();p.add_argument("instance_root");p.add_argument("--allow-draft",action="store_true");a=p.parse_args();r=Path(a.instance_root)
errs=validate_science_contract(load_science_contract(r/"science_contract.json"))+validate_source_contract(json.loads((r/"source_contract.json").read_text(encoding="utf-8")))+validate_gate_plan(r/"gate_plan.json")+validate_report(r/"report"/"FALSIFIER_REPORT.tex",require_complete=not a.allow_draft)
print(json.dumps({"ok":not errs,"errors":errs},indent=2));raise SystemExit(0 if not errs else 1)

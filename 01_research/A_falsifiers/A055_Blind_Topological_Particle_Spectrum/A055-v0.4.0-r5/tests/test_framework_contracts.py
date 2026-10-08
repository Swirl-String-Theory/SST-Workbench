from pathlib import Path
import json

# Root conftest.py resolves the shared framework before test-module collection.
from sst_falsifier.science_contract import validate_science_contract, load_science_contract
from sst_falsifier.source_registry import validate_source_contract
from sst_falsifier.gates import validate_gate_plan
from sst_falsifier.report import validate_report

ROOT = Path(__file__).resolve().parents[1]


def test_framework_pin_and_contracts():
    pin=json.loads((ROOT/'FRAMEWORK_PIN.json').read_text())
    assert pin['version']=='1.0.4'
    assert pin['status']=='CANONICAL_FROZEN'
    errs=[]
    errs += validate_science_contract(load_science_contract(ROOT/'science_contract.json'))
    errs += validate_source_contract(json.loads((ROOT/'source_contract.json').read_text()))
    errs += validate_gate_plan(ROOT/'gate_plan.json')
    errs += validate_report(ROOT/'report'/'FALSIFIER_REPORT.tex',require_complete=True)
    assert not errs, errs


def test_public_tree_has_no_private_forbidden_terms():
    terms=[x.strip().lower() for x in (ROOT/'private'/'blind_forbidden_terms.txt').read_text().splitlines() if x.strip()]
    bad=[]
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT)
        if any(x.lower() in {'private','revealed','reveal_private'} for x in rel.parts): continue
        if any(x in {'__pycache__','.pytest_cache','.venv','build'} for x in rel.parts): continue
        if p.suffix.lower() in {'.pyd','.so','.dll','.pyc'}: continue
        txt=p.read_text(encoding='utf-8',errors='ignore').lower()
        for term in terms:
            if term in txt: bad.append((str(rel),term))
    assert not bad,bad

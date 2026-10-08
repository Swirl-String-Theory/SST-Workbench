from pathlib import Path
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[1]

def _load_validator():
    # On target Workbench, use the exact pinned Framework-v1.0.6 validator.
    loc=(ROOT/'.sst_framework_root').read_text(encoding='utf-8').strip()
    fw=(ROOT/loc).resolve()
    p=fw/'sst_falsifier'/'science_contract.py'
    if not p.is_file():
        return None
    spec=importlib.util.spec_from_file_location('a058_fw_science_contract',p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_science_contract_schema_complete():
    c=json.loads((ROOT/'science_contract.json').read_text(encoding='utf-8'))
    m=_load_validator()
    if m is not None:
        assert m.validate_science_contract(c)==[]
        return
    eq={e['id'] for e in c['equations']}
    assert eq
    for step in c['steps']:
        assert step['formula_refs']
        assert set(step['formula_refs']) <= eq

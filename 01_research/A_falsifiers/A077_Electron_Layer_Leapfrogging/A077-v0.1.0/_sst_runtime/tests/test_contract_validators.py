import json
from pathlib import Path
from sst_falsifier.source_registry import validate_source_contract
from sst_falsifier.gates import validate_gate_plan

def test_source_placeholder_rejected():
    c={"schema":"SST-SOURCE-CONTRACT-2","independent_unit":"REPLACE_BEFORE_FREEZE","sources":[]}
    assert validate_source_contract(c)

def test_gate_cycle_rejected(tmp_path):
    p=tmp_path/"g.json";p.write_text(json.dumps({"schema":"SST-GATE-PLAN-2","gates":[{"gate_id":"A","question":"a","requires":["B"]},{"gate_id":"B","question":"b","requires":["A"]}]}))
    assert any("cycle" in e for e in validate_gate_plan(p))

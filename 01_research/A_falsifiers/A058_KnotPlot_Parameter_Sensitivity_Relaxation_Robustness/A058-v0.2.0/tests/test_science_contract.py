import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_science_contract_references():
    c=json.loads((ROOT/'science_contract.json').read_text()); eq={x['id'] for x in c['equations']}; assert c['schema']=='SST-SCIENCE-CONTRACT-2'; assert all(s['formula_refs'] and set(s['formula_refs'])<=eq for s in c['steps'])
def test_gate_ids():
    g=json.loads((ROOT/'gate_plan.json').read_text()); assert [x['gate_id'] for x in g['gates']]==[f'G{i}' for i in range(10)]

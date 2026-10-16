from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_science_contract_refs():
    c=json.loads((ROOT/'science_contract.json').read_text());ids={e['id'] for e in c['equations']};assert all(s['formula_refs'] and set(s['formula_refs'])<=ids for s in c['steps'])

from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_only_g0_is_hard_science_dependency():
    g=json.loads((ROOT/'gate_plan.json').read_text())['gates']
    for x in g:
        if x['gate_id']=='G0': assert x['requires']==[]
        else: assert x['requires']==['G0']
def test_reveal_does_not_block_on_scientific_unresolved():
    p=json.loads((ROOT/'blind_policy.json').read_text());assert p['block_reveal_on_unresolved'] is False;assert p['reveal_requires_gate_status']==['PASS','FAIL']
def test_prediction_gate_is_reveal_prerequisite():
    p=json.loads((ROOT/'blind_policy.json').read_text());assert p['reveal_requires_gate']=='G17'

from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]

def test_locator_pins_canonical_104():
    s=(ROOT/'.sst_framework_root').read_text().strip().replace('\\','/');assert s.endswith('06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.4')

def test_gate6_is_nonblocking_side_branch():
    g=json.loads((ROOT/'gate_plan.json').read_text()); by={x['gate_id']:x for x in g['gates']}; assert by['G7']['requires']==['G5'] and 'G6' not in by['G7']['requires']

def test_output_adapter_contract_text():
    s=(ROOT/'run_instance.py').read_text(); assert 'A056-v0.2.3-outputs' in s and 'A056_v0.2.3-outputs' in s

def test_generated_report_adapter_is_local_and_page_safe():
    s=(ROOT/'run_instance.py').read_text(encoding='utf-8')
    assert '_safe_auto_results' in s
    assert 'p{0.365\\linewidth}' in s
    assert 'Full machine-readable provenance is preserved' in s

from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_locator_pins_canonical_106():
    s=(ROOT/'.sst_framework_root').read_text().strip().replace('\\','/')
    assert s.endswith('06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6')

def test_gate6_is_nonblocking_side_branch():
    g=json.loads((ROOT/'gate_plan.json').read_text())
    by={x['gate_id']:x for x in g['gates']}
    assert by['G7']['requires']==['G5'] and 'G6' not in by['G7']['requires']

def test_output_contract_is_v040_only():
    s=(ROOT/'run_instance.py').read_text()
    assert 'A056_v0.4.0-outputs' in s
    assert 'A056_v0.3.0-outputs' not in s

def test_generated_report_adapter_is_local_and_page_safe():
    s=(ROOT/'run_instance.py').read_text(encoding='utf-8')
    assert '_safe_auto_results' in s
    assert 'p{0.365\\linewidth}' in s
    assert 'Full machine-readable provenance is preserved' in s

def test_framework_v106_bootstrap_contract_is_used():
    s=(ROOT/'run_instance.py').read_text(encoding='utf-8')
    assert 'from framework_bootstrap import load_framework' in s
    assert 'FRAMEWORK_ROOT = load_framework()' in s
    assert 'REVEAL_IF_ALLOWED' not in s  # mode is delegated generically to canonical runner
    rp=(ROOT/'run_python.py').read_text(encoding='utf-8')
    assert 'load_framework' in rp

def test_real_launchers_use_framework_reveal_if_allowed():
    for name in ('run_e010_filament.cmd','run_e010_euler_smoke.cmd','run_e010_euler_convergence.cmd'):
        text=(ROOT/name).read_text(encoding='utf-8')
        assert 'run_python.cmd' in text
        assert 'REVEAL_IF_ALLOWED' in text
        assert '--require-framework-revealed' in text
        assert 'print_gate_summary.py' in text

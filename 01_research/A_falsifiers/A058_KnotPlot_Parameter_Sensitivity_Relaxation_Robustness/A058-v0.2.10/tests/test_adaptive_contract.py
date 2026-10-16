from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_adaptive_not_fixed_terminal_count():
    c=json.loads((ROOT/'configs/default.json').read_text())['adaptive_relaxation']
    assert c['command']=='go' and c['quantum_iterations']<=64 and c['stable_windows_required']>=3
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text().lower()
    assert 'ago 1000' not in s and 'ago 15000' not in s
    assert 'quantum_iterations' in s and "f'go {int(ad[" not in ''

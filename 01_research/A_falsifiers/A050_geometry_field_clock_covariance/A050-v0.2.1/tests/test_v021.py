import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_v021_is_horizon_only_extension():
    cfg=json.loads((ROOT/'config/default.json').read_text())
    frozen=json.loads((ROOT/'config/frozen_gate_thresholds_v0.2.0.json').read_text())
    assert cfg['observation_protocol']['policy']=='unresolved_gate_horizon_extension'
    assert cfg['observation_protocol']['gate_thresholds_retuned'] is False
    assert cfg['evolution_steps']==320
    assert cfg['field_gate_steps']==80
    assert cfg['floquet_gate']['search_steps']==640
    assert cfg['time_step']==0.02
    assert cfg['sample_every']==4
    assert cfg['temporal_memory_gate']==frozen['temporal_memory_gate']
    assert cfg['kelvin_gate']==frozen['kelvin_gate']
    for k,v in frozen['floquet_thresholds'].items():
        assert cfg['floquet_gate'][k]==v
    for k,v in frozen['spatial_thresholds'].items():
        assert cfg[k]==v

def test_floquet_window_covers_full_long_search():
    cfg=json.loads((ROOT/'config/default.json').read_text())
    assert cfg['floquet_gate']['max_return_steps']==cfg['floquet_gate']['search_steps']-1
    assert cfg['floquet_gate']['search_steps']>=2*cfg['evolution_steps']

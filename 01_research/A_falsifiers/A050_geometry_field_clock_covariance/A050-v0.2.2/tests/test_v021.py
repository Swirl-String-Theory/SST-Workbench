import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v021_legacy_threshold_source_retained():
    cfg=json.loads((ROOT/'config/default.json').read_text())
    frozen=json.loads((ROOT/'config/frozen_gate_thresholds_v0.2.0.json').read_text())
    assert cfg['observation_protocol']['parent_version']=='v0.2.1'
    assert cfg['observation_protocol']['legacy_gate_thresholds_retuned'] is False
    assert cfg['temporal_memory_gate']==frozen['temporal_memory_gate']
    assert cfg['kelvin_gate']==frozen['kelvin_gate']

def test_v021_floquet_result_is_provenance_only_in_v022():
    cfg=json.loads((ROOT/'config/default.json').read_text())
    assert cfg['floquet_policy']['active'] is False
    assert cfg['floquet_policy']['prior_status']=='INDETERMINATE_NO_RECURRENCE'

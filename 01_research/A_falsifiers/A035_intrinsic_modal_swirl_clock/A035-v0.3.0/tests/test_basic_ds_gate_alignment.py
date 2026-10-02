"""Basic config: analysis ds gate must not be stricter than stage_a hard stop."""

from pathlib import Path
import json


def test_gate_max_stage_a_ds_cv_aligned_with_hard_stop():
    cfg = json.loads((Path(__file__).resolve().parents[1] / 'config' / 'basic.json').read_text(encoding='utf-8'))
    hard = float(cfg['stage_a_hard_ds_cv'])
    gate = float(cfg['gate_max_stage_a_ds_cv'])
    assert gate >= hard - 1e-12
    assert cfg.get('gate_require_all_priority_carriers') is False
    assert float(cfg['gate_min_valid_carrier_fraction_for_global_fail']) <= 0.75

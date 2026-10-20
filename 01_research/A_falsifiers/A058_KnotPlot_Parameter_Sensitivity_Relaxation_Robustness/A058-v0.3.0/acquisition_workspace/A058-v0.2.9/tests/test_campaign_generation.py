from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_design_count_formula():
    assert 6+1+8*33==271
def test_config_axes():
    c=json.loads((ROOT/'configs/default.json').read_text());assert c['axes']==[f'S{i}' for i in range(8)];assert len(c['references'])==6


def test_activation_control_is_separate_from_sweep():
    c=json.loads((ROOT/'configs/default.json').read_text())
    controls=c['activation_controls']
    assert len(controls)==1
    assert controls[0]['reference_id']=='R2' and controls[0]['switch_state']=='off'


def test_public_campaign_excludes_real_switch_names():
    s=(ROOT/'tools/generate_campaign.py').read_text()
    assert "'resolved_sector_parameters':sectors" not in s
    assert "'resolved_sector_ids':sorted(sectors)" in s

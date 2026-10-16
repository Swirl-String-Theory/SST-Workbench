from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_private_map_has_8_axes_6_sectors():
    p=json.loads((ROOT/'private/axis_map.json').read_text());assert len(p['axes'])==8;assert len(p['sectors'])==6
    assert all(p['axes'][f'S{i}']['parameter'] for i in range(8))
def test_eighth_axis_has_dedicated_sixth_sector():
    p=json.loads((ROOT/'private/axis_map.json').read_text())
    assert p['axes']['S7']['sector_ref']=='R5'
    assert p['sectors']['R5']['switch_parameter']
    assert p['sectors']['R5']['axes']==['S7']

def test_s3_fixed_default_and_setter_acceptance():
    p=json.loads((ROOT/'private/axis_map.json').read_text()); a=p['axes']['S3']
    assert a['default_value']==1.4 and a['verification']=='setter_acceptance'
    assert p['sectors']['R2']['axes']==['S3','S4']


def test_r2_true_reset_default_separate_from_enabled_reference():
    p=json.loads((ROOT/'private/axis_map.json').read_text())
    r=p['sectors']['R2']
    assert r['reset_switch_state']=='off'
    assert r['sweep_reference_switch_state']=='on'
    assert p['axes']['S3']['verification']=='setter_acceptance'

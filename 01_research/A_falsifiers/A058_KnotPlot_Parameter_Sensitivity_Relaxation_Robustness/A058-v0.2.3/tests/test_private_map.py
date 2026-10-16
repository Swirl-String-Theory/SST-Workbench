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

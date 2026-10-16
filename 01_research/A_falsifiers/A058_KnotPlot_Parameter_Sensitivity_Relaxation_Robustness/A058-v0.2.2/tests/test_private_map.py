from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_private_map_has_7_axes_5_sectors():
    p=json.loads((ROOT/'private/axis_map.json').read_text());assert len(p['axes'])==7;assert len(p['sectors'])==5
    assert all(p['axes'][f'S{i}']['parameter'] for i in range(7))

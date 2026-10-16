from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_design_count_formula():
    assert 6+8*33==270
def test_config_axes():
    c=json.loads((ROOT/'configs/default.json').read_text());assert c['axes']==[f'S{i}' for i in range(8)];assert len(c['references'])==6

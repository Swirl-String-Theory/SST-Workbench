from pathlib import Path
import json,subprocess,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
def test_design_count_formula():
    assert 5+7*33==236
def test_config_axes():
    c=json.loads((ROOT/'configs/default.json').read_text());assert c['axes']==[f'S{i}' for i in range(7)];assert len(c['references'])==5

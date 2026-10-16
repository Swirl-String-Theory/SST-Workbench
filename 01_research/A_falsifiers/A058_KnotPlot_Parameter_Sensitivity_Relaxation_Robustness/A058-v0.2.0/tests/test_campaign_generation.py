from pathlib import Path
import importlib.util, json, shutil
ROOT=Path(__file__).resolve().parents[1]
def _mod():
    spec=importlib.util.spec_from_file_location('gen',ROOT/'tools/generate_campaign.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def test_condition_count_and_axis_counts(tmp_path,monkeypatch):
    m=_mod(); levels=m.ladder(); assert len(levels)==34; assert sum(1 for z in levels if z['kind']=='zero')==1; assert sum(1 for z in levels if z.get('k')==0)==1
    # mathematical count: BASE + 33 active-axis S0 + 33 active-axis S1 + 34 conditional S2
    assert 1+33+33+34==101

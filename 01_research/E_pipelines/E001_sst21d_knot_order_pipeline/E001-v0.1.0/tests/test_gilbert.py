from pathlib import Path
from sst21d.gilbert import parse_gilbert,sample_entry
ROOT=Path(__file__).resolve().parents[1]
def test_parse_mini():
    e=parse_gilbert(ROOT/'examples'/'ideal_mini.txt')
    assert [x.topology_key for x in e]==['0_1','3_1']
    assert sample_entry(e[0],128)[0].shape==(128,3)

from pathlib import Path
from a054_ntaf.prepare_v030 import KNOTS,SKELETONS,DIRECT_LINKS,MIXED,prepare_discovery

def test_v030_declared_count():
    assert len(KNOTS)==14
    assert len(SKELETONS)==4
    assert len(DIRECT_LINKS)==7
    assert len(KNOTS)*(1+len(SKELETONS))+len(MIXED)*len(SKELETONS)+len(DIRECT_LINKS)==101

def test_v030_prepare(tmp_path):
    root=Path(__file__).resolve().parents[1]
    m=prepare_discovery(tmp_path/'run',root,n=72)
    assert m['scientific_ready'] is True
    assert m['candidate_count']==101

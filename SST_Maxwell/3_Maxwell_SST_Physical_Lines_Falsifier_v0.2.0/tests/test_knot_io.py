from pathlib import Path
from sst_maxwell3_blind.knot_io import read_centerline_txt,resample_closed

def test_multicomponent(tmp_path:Path):
    p=tmp_path/'x.txt'
    p.write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n-1 1 0\n-1 0 0\n-1 -1 0\n0 -1 0\n\n0 0 1\n1 0 1\n1 1 1\n0 1 1\n-1 1 1\n-1 0 1\n-1 -1 1\n0 -1 1\n')
    c=read_centerline_txt(p)
    assert len(c)==2
    assert resample_closed(c[0],32).shape==(32,3)

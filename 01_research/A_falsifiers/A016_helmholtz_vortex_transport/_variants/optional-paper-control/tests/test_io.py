from pathlib import Path
from helmholtz_sst.io import load_centerline

def test_blank_line_components(tmp_path):
    p=tmp_path/'x.txt';p.write_text('0 0 0\n1 0 0\n0 1 0\n\n0 0 1\n1 0 1\n0 1 1\n');c=load_centerline(p);assert len(c)==2 and len(c[0])==3

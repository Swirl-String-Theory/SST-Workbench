from pathlib import Path
import numpy as np, tempfile
from a055_spectrum.providers import parse_vect_components,resample_closed
def test_multicomponent_vect_parser():
    s="VECT\n2 6 0\n-3 -3\n0 0\n0 0 0\n1 0 0\n0 1 0\n0 0 1\n1 0 1\n0 1 1\n"
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"x.vect"; p.write_text(s)
        c=parse_vect_components(p); assert len(c)==2
        assert resample_closed(c[0],16).shape==(16,3)

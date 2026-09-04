
from pathlib import Path
import numpy as np
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.ridgerunner import write_vect, read_vect, polygonal_length

DATA = Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_vect_roundtrip(tmp_path):
    link = parse_ideal_links(DATA)["L2a1"]
    curves = [sample_component(c, 256).r for c in link.components]
    path = write_vect(curves, tmp_path/"L2a1.vect")
    loaded = read_vect(path)
    assert len(loaded) == 2
    assert np.allclose(curves[0], loaded[0])
    assert abs(polygonal_length(loaded[0])-2*np.pi) < 1e-3

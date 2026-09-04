
from pathlib import Path
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.geometry import component_geometry

DATA = Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_refined_curvature_not_below_sampled_maximum():
    comp = parse_ideal_links(DATA)["L7a3"].components[0]
    result = component_geometry(sample_component(comp, 256), 8)
    assert result["refined_curvature_max_Dinv"] >= result["sampled_curvature_max_Dinv"]*(1-1e-10)

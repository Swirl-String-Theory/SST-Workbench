from pathlib import Path
import numpy as np
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.geometry import component_geometry
from sst_link_suite.topology import gauss_linking_matrix
from sst_link_suite.contacts import contact_summary

DATA = Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_hopf_exact_geometry():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 512) for c in link.components]
    lengths = [component_geometry(s)["numerical_length_D"] for s in samples]
    assert np.allclose(lengths, 2*np.pi, rtol=0, atol=1e-8)
    lk = gauss_linking_matrix([s.r for s in samples])
    assert abs(abs(lk[0,1])-1) < 2e-4
    contacts = contact_summary(samples, 1.0, 0.01)
    assert abs(contacts["mutual_pairs"][0]["refined_min_distance_D"]-1.0) < 1e-7

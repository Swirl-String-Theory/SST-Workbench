from pathlib import Path
import numpy as np
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import evaluate

DATA = Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_periodic_closure_and_derivatives():
    comp = parse_ideal_links(DATA)["L7n2"].components[0]
    t = np.array([0.0, 2*np.pi])
    for derivative in range(4):
        y = evaluate(comp, t, derivative)
        assert np.linalg.norm(y[0]-y[1]) < 1e-8

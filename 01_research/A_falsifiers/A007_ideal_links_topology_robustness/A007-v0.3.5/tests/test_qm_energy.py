from pathlib import Path
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.perturbations import build_reduced_normal_basis
from sst_link_suite.qm_energy import finite_difference_reduced_energy
from sst_link_suite.native_ext import BackendOptions

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"
PROFILES = {
    "hybrid": {"length": 0.25, "bending": 0.25, "tube_repulsion": 0.25, "neumann": 0.25}
}


def test_reduced_hessian_shapes_and_symmetry():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 24) for c in link.components]
    basis, _ = build_reduced_normal_basis(samples, mode_max=0)
    result, geometric = finite_difference_reduced_energy(
        samples, basis, np.array([-1.0, 1.0]), link.diameter, 0.1,
        BackendOptions(force_python=True), 0.004, PROFILES,
    )
    d = basis.vectors.shape[0]
    matrix = np.asarray(result["hessians"]["hybrid"]["matrix"])
    assert matrix.shape == (d, d)
    assert np.max(np.abs(matrix-matrix.T)) < 1e-10
    assert geometric["hessian"].shape[1:] == (d, d)

from pathlib import Path
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.perturbations import build_reduced_normal_basis
from sst_link_suite.symplectic import candidate_filament_symplectic_matrix, symplectic_diagnostics

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"


def test_reduced_basis_is_weight_orthonormal_and_even():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 48) for c in link.components]
    basis, holonomy = build_reduced_normal_basis(samples, mode_max=1)
    gram = np.einsum("aij,bij,i->ab", basis.vectors, basis.vectors, basis.weights)
    assert basis.vectors.shape[0] % 2 == 0
    assert np.max(np.abs(gram-np.eye(len(gram)))) < 1e-8
    assert len(holonomy) == 2


def test_candidate_symplectic_form_is_antisymmetric_and_even_rank():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 48) for c in link.components]
    basis, _ = build_reduced_normal_basis(samples, mode_max=1)
    omega = candidate_filament_symplectic_matrix(samples, basis, np.array([-1.0, 1.0]))
    diag = symplectic_diagnostics(omega)
    assert np.max(np.abs(omega+omega.T)) < 1e-10
    assert diag["rank_is_even"]

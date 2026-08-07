from pathlib import Path
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.native_ext import fallback

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data" / "idealLinks.txt"


def _energy(link_id: str, n: int, arc: float) -> float:
    link = parse_ideal_links(DATA)[link_id]
    curves = [sample_component(c, n).r for c in link.components]
    matrix = fallback.neumann_coupling_matrices_arc_exclusion(curves, np.asarray([0.1]), arc)[0]
    signs = -np.ones(len(curves))
    return float(signs @ matrix @ signs)


def test_fixed_arc_exclusion_is_resolution_stable_hopf():
    e64 = _energy("L2a1", 64, 0.20)
    e128 = _energy("L2a1", 128, 0.20)
    e256 = _energy("L2a1", 256, 0.20)
    # The final refinement should improve or at least remain comparable; this is a regression
    # guard against the old fixed-segment exclusion whose physical window shrank as N grew.
    d1 = abs(e128-e64)/max(abs(e128), 1e-12)
    d2 = abs(e256-e128)/max(abs(e256), 1e-12)
    assert d2 < 0.08
    assert d2 <= 1.25*d1 + 1e-12


def test_arc_exclusion_differs_from_legacy_segment_count_at_changed_resolution():
    link = parse_ideal_links(DATA)["L6a4"]
    curves = [sample_component(c, 256).r for c in link.components]
    arc = fallback.neumann_coupling_matrices_arc_exclusion(curves, np.asarray([0.1]), 0.20)[0]
    legacy = fallback.neumann_coupling_matrices(curves, np.asarray([0.1]), 2)[0]
    assert np.max(np.abs(arc-legacy)) > 1e-6

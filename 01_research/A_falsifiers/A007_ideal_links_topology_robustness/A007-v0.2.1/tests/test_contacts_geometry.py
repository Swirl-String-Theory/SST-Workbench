from pathlib import Path
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.contacts import contact_summary, contact_graph_summary
from sst_link_suite.geometry import (
    component_geometry,
    weighted_quantile,
    curvature_spectral_tail,
)
from sst_link_suite.models import FourierComponent

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"


def test_round_component_self_contact_uses_arclength_exclusion():
    """v0.2.0 index-fraction exclusion reported self_contact_coverage=1.0 on circles."""
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 512) for c in link.components]
    contacts = contact_summary(samples, link.diameter, 0.01, self_exclusion_D=2.0)
    for self_row in contacts["self_components"]:
        assert self_row["self_contact_coverage"] == 0.0
        # Chord length at arclength window w=2 on unit circle: 2*sin(w/2) = 2*sin(1).
        expected = 2.0 * np.sin(1.0)
        assert abs(self_row["sampled_nonlocal_min_distance_D"] - expected) < 5e-3
        # Window is 2 D, clipped by total_length/2.5 ≈ 2.513, so remains 2.
        assert abs(self_row["exclusion_window_D"] - 2.0) < 1e-6


def test_contact_graph_union_find_handles_long_chains():
    """Recursive find overflowed after ~991 frames at contact_n=1024 on L2a1."""
    n = 5000
    edges = [
        {
            "component_a": 1,
            "index_a": i,
            "component_b": 1,
            "index_b": i + 1,
            "distance_D": 1.0,
        }
        for i in range(n - 1)
    ]
    graph = contact_graph_summary(edges, [n])
    assert graph["contact_edge_count"] == n - 1
    assert graph["contact_graph_nodes"] == n
    assert graph["contact_graph_connected_components"] == 1
    assert graph["contact_graph_cycle_rank"] == 0


def test_weighted_quantile_uniform_matches_numpy():
    values = np.linspace(0.0, 1.0, 101)
    weights = np.ones_like(values)
    assert abs(weighted_quantile(values, weights, 0.5) - 0.5) < 1e-6
    assert abs(weighted_quantile(values, weights, 0.95) - float(np.quantile(values, 0.95))) < 2e-2


def test_weighted_quantile_shifts_with_mass():
    values = np.array([0.0, 1.0, 2.0, 3.0])
    low = weighted_quantile(values, np.array([10.0, 1.0, 1.0, 1.0]), 0.5)
    high = weighted_quantile(values, np.array([1.0, 1.0, 1.0, 10.0]), 0.5)
    assert low < 1.0
    assert high > 2.0


def test_weighted_quantile_zero_weight_is_nan():
    assert np.isnan(weighted_quantile(np.array([1.0, 2.0]), np.array([0.0, 0.0]), 0.5))


def test_curvature_spectral_tail_pure_circle_is_zero():
    # Unit circle in xy: A1=(1,0,0), B1=(0,1,0).
    A = np.zeros((16, 3))
    B = np.zeros((16, 3))
    A[1] = (1.0, 0.0, 0.0)
    B[1] = (0.0, 1.0, 0.0)
    component = FourierComponent(index=1, declared_length=2 * np.pi, A=A, B=B)
    assert curvature_spectral_tail(component) == 0.0


def test_curvature_spectral_tail_short_spectrum_is_zero():
    A = np.zeros((4, 3))
    B = np.zeros((4, 3))
    A[1] = (1.0, 0.0, 0.0)
    B[1] = (0.0, 1.0, 0.0)
    component = FourierComponent(index=1, declared_length=2 * np.pi, A=A, B=B)
    assert curvature_spectral_tail(component) == 0.0


def test_component_geometry_ropelength_scales_with_diameter():
    link = parse_ideal_links(DATA)["L2a1"]
    sample = sample_component(link.components[0], 256)
    geo_d1 = component_geometry(sample, diameter=1.0)
    geo_d2 = component_geometry(sample, diameter=2.0)
    assert abs(geo_d1["standard_ropelength_radius"] - 2.0 * geo_d1["numerical_length_D"]) < 1e-12
    assert abs(geo_d2["standard_ropelength_radius"] - geo_d1["standard_ropelength_radius"] / 2.0) < 1e-12
    assert "curvature_spectral_tail_fraction" in geo_d1
    assert "arclength_fraction_over_curvature_bound" in geo_d1

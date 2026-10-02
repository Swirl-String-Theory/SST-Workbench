from pathlib import Path
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.geometry import component_geometry
from sst_link_suite.contacts import contact_summary
from sst_link_suite.gates import thickness_gate, curvature_mode_convergence
from sst_link_suite.models import FourierComponent, IdealLink

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"


def _circle_link(diameter: float = 1.0) -> IdealLink:
    A = np.zeros((8, 3))
    B = np.zeros((8, 3))
    A[1] = (1.0, 0.0, 0.0)
    B[1] = (0.0, 1.0, 0.0)
    component = FourierComponent(index=1, declared_length=2 * np.pi, A=A, B=B)
    return IdealLink(
        link_id="circle",
        conway="",
        diameter=diameter,
        components=(component,),
    )


def test_thickness_gate_hopf_bound_by_mutual_contact():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 256) for c in link.components]
    geos = [component_geometry(s, link.diameter) for s in samples]
    contacts = contact_summary(samples, link.diameter, 0.01)
    gate = thickness_gate(geos, contacts, link.diameter)
    assert gate["binding_constraint"] == "mutual_contact"
    assert abs(gate["allowed_diameter_D"] - 1.0) < 1e-4
    assert gate["passes"] is True
    assert gate["kappa_max_Dinv"] < 1.01


def test_thickness_gate_curvature_binding():
    component_results = [{
        "curvature_max_Dinv": 10.0,
        "arclength_fraction_over_curvature_bound": 0.5,
        "curvature_spectral_tail_fraction": 0.1,
    }]
    contacts = {
        "self_components": [{"sampled_nonlocal_min_distance_D": 5.0}],
        "mutual_pairs": [{"refined_min_distance_D": 5.0}],
    }
    gate = thickness_gate(component_results, contacts, diameter=1.0)
    assert gate["binding_constraint"] == "curvature"
    assert abs(gate["allowed_diameter_D"] - 0.2) < 1e-12
    assert gate["passes"] is False


def test_curvature_mode_convergence_circle_within_bound():
    link = _circle_link(diameter=1.0)
    report = curvature_mode_convergence(link, cutoffs=(2, 4, 6), n=256)
    assert report["full_record_within_bound"] is True
    assert report["largest_cutoff_within_bound"] is not None
    assert all(row["within_thickness_bound"] for row in report["rows"])
    assert all(row["max_curvature_Dinv"] < 1.05 for row in report["rows"])

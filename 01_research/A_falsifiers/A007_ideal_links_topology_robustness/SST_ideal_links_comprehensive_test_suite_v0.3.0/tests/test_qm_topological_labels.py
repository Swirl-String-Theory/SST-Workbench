from pathlib import Path
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.topology import topology_summary
from sst_link_suite.topological_labels import build_topological_label_ledger
from sst_link_suite.native_ext import BackendOptions

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"


def test_hopf_sector_quotient_and_automorphism():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 128) for c in link.components]
    topo = topology_summary([s.r for s in samples], False, 128, BackendOptions(force_python=True))
    ledger = build_topological_label_ledger(
        np.asarray(topo["linking_matrix"]), [2*np.pi, 2*np.pi], integer_tolerance=0.03
    )
    assert ledger["integer_lock_pass"]
    assert ledger["component_automorphism_order_proxy"] == 2
    assert ledger["independent_circulation_sector_count"] == 2
    assert not ledger["higher_linking_invariant_required"]

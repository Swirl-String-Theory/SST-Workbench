import numpy as np
from sst_link_suite.topological_labels import build_topological_label_ledger


def test_borromean_catalog_and_all_eight_sectors():
    ledger=build_topological_label_ledger(np.zeros((3,3)), [1.0,1.0,1.0], link_id="L6a4", topology_sample_n=256)
    assert ledger["common_name"] == "Borromean rings"
    assert ledger["higher_linking_invariant_required"] is True
    assert ledger["higher_linking_invariant_computed"] is False
    assert ledger["all_circulation_sector_count"] == 8
    assert ledger["automorphism_quotient_applied"] is False


def test_two_component_pairwise_zero_also_requires_higher_invariant():
    ledger=build_topological_label_ledger(np.zeros((2,2)), [1.0,1.0], link_id="L5a1")
    assert ledger["higher_linking_invariant_required"] is True
    assert "Alexander" in ledger["higher_linking_required_family"]

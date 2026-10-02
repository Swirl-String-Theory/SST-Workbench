from sst_modal_clock.sources import canonical_cli_topology

def test_cli_topology_aliases():
    assert canonical_cli_topology("L2a1") == "L2.2.1"
    assert canonical_cli_topology("L2.2.1") == "L2.2.1"
    assert canonical_cli_topology("3_1") == "K3.1"
    assert canonical_cli_topology("K3.1") == "K3.1"

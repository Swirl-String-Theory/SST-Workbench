
from pathlib import Path
from sst_link_suite.contacts import contact_graph_summary
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.contacts import contact_summary

DATA = Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_iterative_union_find_handles_long_chain():
    edges = [
        {"kind":"mutual", "component_a":1, "index_a":i,
         "component_b":2, "index_b":i, "distance_D":1.0}
        for i in range(5000)
    ]
    result = contact_graph_summary(edges, [5000, 5000])
    assert result["contact_edge_count"] == 5000
    assert result["contact_graph_nodes"] == 10000


def test_hopf_continuous_contact_is_reported_without_recursion():
    link = parse_ideal_links(DATA)["L2a1"]
    samples = [sample_component(c, 1024) for c in link.components]
    result = contact_summary(samples, 1.0, 0.01, 3)
    assert result["contact_map"]["continuous_contact_patch_count"] >= 1
    assert result["graph"]["contact_edge_count"] >= 1024

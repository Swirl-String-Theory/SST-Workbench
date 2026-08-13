from pathlib import Path
from sst_link_suite.parser import parse_ideal_links, DEFAULT_TARGETS

DATA = Path(__file__).parents[1] / "data" / "idealLinks.txt"


def test_all_targets_present():
    links = parse_ideal_links(DATA)
    assert all(link_id in links for link_id in DEFAULT_TARGETS)
    assert len(DEFAULT_TARGETS) == 18
    assert len(links) == 130


def test_component_counts():
    links = parse_ideal_links(DATA)
    assert len(links["L2a1"].components) == 2
    assert len(links["L6a4"].components) == 3
    assert len(links["L6n1"].components) == 3

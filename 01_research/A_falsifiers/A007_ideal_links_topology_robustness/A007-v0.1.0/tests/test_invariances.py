from pathlib import Path
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.analysis import invariance_audit

DATA = Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_linking_invariances():
    link = parse_ideal_links(DATA)["L5a1"]
    audit = invariance_audit(link, 192)
    assert audit["rigid_transform_max_abs_error"] < 1e-10
    assert audit["mirror_sign_flip_max_abs_error"] < 1e-10
    assert audit["reverse_all_components_max_abs_error"] < 1e-10

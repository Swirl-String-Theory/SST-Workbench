from pklsa_builder.topology_db import (
    _labelish,
    _preferred_candidates,
    canonicalize_knot_label,
    canonicalize_link_label,
)


def test_numeric_rank_field_is_not_considered_for_identity():
    # Dot notation remains a supported legacy knot spelling (e.g. 3.1), but arbitrary
    # numeric rank columns are never scanned because admission is field-semantic.
    assert _preferred_candidates({'name_rank': '1.0'}, 'knot') == []
    assert _preferred_candidates({'name_rank': 355.0}, 'link') == []
    assert canonicalize_knot_label('3.1') == '3_1'


def test_knotinfo_name_beats_numeric_rank():
    row = {'name': '3_1', 'name_rank': '2', 'dt_name': '3a_1', 'crossing_number': 3.0}
    c = _preferred_candidates(row, 'knot')
    primary = min(c, key=lambda x: x['priority'])
    assert primary['field'] == 'name'
    assert primary['canonical'] == '3_1'


def test_linkinfo_unoriented_name_is_canonical():
    row = {'name_unoriented': 'L10a1', 'name': 'L10a1{0}', 'name_rank': 355.0, 'knot_atlas': 'L10a1'}
    c = _preferred_candidates(row, 'link')
    primary = min(c, key=lambda x: x['priority'])
    assert primary['field'] == 'name_unoriented'
    assert primary['canonical'] == 'L10a1'
    assert canonicalize_link_label('L10a1{1}') == 'L10a1'

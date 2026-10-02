from maxwell_sst_falsifier.ledger import taxonomy_guard


def test_writhe_double_count_guard():
    rows = [{"knot":"K", "mode_id":"wr", "family":"writhe", "independent_energy_channel":"true"}]
    r = taxonomy_guard(rows, finite_core_resolved=True, material_frame_resolved=True)
    assert r and r[0]["status"] == "FAIL"

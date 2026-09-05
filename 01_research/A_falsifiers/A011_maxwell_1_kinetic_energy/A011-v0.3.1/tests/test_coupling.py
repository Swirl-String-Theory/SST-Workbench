from maxwell_sst_falsifier.coupling import three_gate


def test_three_gate():
    r = three_gate(0.01, 0.5, 1e-3, 1.0, 1.0, 1e-4)
    assert r["active"] is True
    r = three_gate(0.01, 2.0, 1e-3, 1.0, 1.0, 1e-4)
    assert r["active"] is False

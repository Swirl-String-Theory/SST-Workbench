from maxwell_sst_falsifier.observables import orientation_Q


def test_axis_set_is_isotropic_second_rank():
    rows = []
    for i, t in enumerate([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]):
        rows.append({"knot":"K", "sample_id":str(i), "tx":str(t[0]), "ty":str(t[1]), "tz":str(t[2]), "weight":"1"})
    r = orientation_Q(rows)[0]
    assert r["Q_frobenius"] < 1e-14

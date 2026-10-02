from maxwell_sst_falsifier.thermo import Level, discrete_partition


def test_high_gap_heat_capacity_suppressed():
    r = discrete_partition([Level(2.0, 1)], 300.0)
    assert r["Cv_over_kB"] < 1e-20


def test_low_gap_heat_capacity_nonzero():
    r = discrete_partition([Level(0.025, 1)], 300.0)
    assert r["Cv_over_kB"] > 0.1

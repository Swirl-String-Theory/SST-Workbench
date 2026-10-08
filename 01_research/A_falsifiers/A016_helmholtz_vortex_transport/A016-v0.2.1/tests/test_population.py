from experiment.population import cauchy_population_control


def test_cauchy_population_exact_control():
    r = cauchy_population_control()
    assert r["zero_remains_zero"]
    assert r["nonzero_remains_nonzero"]
    assert r["cauchy_relative_error"] <= 1e-14
    assert r["jacobian_abs_error"] <= 1e-14
    assert r["flux_relative_error"] <= 1e-14

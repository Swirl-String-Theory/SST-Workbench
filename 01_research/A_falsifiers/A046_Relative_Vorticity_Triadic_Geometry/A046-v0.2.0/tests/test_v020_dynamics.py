import numpy as np
from sst_triadic.pipeline import reconstruct_velocity_gradient
from sst_triadic.reference import decompose_gradient
from sst_triadic.rotating import absolute_vorticity, matched_cyclonic_hemisphere_pair
from sst_triadic.delay import circulation_delay_control


def test_uws_reconstructs_full_velocity_gradient():
    rng = np.random.default_rng(1234)
    grad = rng.normal(size=(32, 3, 3))
    S, w, _ = decompose_gradient(grad)
    rec = reconstruct_velocity_gradient(S, w)
    np.testing.assert_allclose(rec, grad, rtol=0.0, atol=1e-14)


def test_absolute_vorticity_and_zero_rotation():
    w = np.array([0.2, -0.1, 0.7])
    O = np.array([0.0, 0.0, 0.3])
    np.testing.assert_allclose(absolute_vorticity(w, O), w + 2.0 * O)
    np.testing.assert_allclose(absolute_vorticity(w, np.zeros(3)), w)


def test_matched_cyclonic_hemisphere_pair():
    p = matched_cyclonic_hemisphere_pair()
    np.testing.assert_allclose(p["south_absolute"], -p["north_absolute"])
    assert np.isclose(np.linalg.norm(p["south_absolute"]), np.linalg.norm(p["north_absolute"]))


def test_delay_phase_and_zero_limit():
    d = circulation_delay_control(n=2048, mode=7, phase_rad=0.73)
    assert d["phase_error_rad"] < 1e-10
    assert d["zero_delay_memory_rms"] < 1e-14
    assert d["memory_rms"] > 1e-3

import numpy as np
from sst_triadic.reference import decompose_gradient, local_linear_controls
from sst_triadic.objectivity import objectivity_residual

def test_linear_pair_same_hwc_different_strain():
    p = local_linear_controls()
    assert np.allclose(p["uA"], p["uB"])
    assert np.allclose(p["omegaA"], p["omegaB"])
    assert abs(p["hA"] - p["hB"]) < 1e-14
    assert abs(p["GammaA"] - p["GammaB"]) < 1e-14
    assert np.linalg.norm(p["strainA"] - p["strainB"]) > 1e-3

def test_decomposition_rotation():
    O = 1.7
    grad = np.array([[0, -O, 0], [O, 0, 0], [0, 0, 0]], dtype=float)
    S, w, div = decompose_gradient(grad)
    assert np.linalg.norm(S) < 1e-14
    assert np.allclose(w, [0, 0, 2*O])
    assert abs(div) < 1e-14

def test_objectivity():
    u = np.array([0.3, -0.2, 0.7])
    grad = np.array([
        [0.2, -1.1, 0.3],
        [1.4, -0.4, 0.2],
        [-0.2, 0.1, 0.2],
    ])
    err, _ = objectivity_residual(u, grad)
    assert err < 1e-12

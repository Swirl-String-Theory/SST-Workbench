import os
import numpy as np
import pytest

from sst_triadic import reference
from sst_triadic import backend


def test_native_backend_is_real_when_requested():
    if os.environ.get("SST_BACKEND", "").lower() != "native":
        pytest.skip("native backend not requested")
    assert backend.backend_name() == "native"


def test_native_reference_parity_when_requested():
    if os.environ.get("SST_BACKEND", "").lower() != "native":
        pytest.skip("native backend not requested")

    grad = np.array([
        [[0.2, -1.1, 0.3], [1.4, -0.4, 0.2], [-0.2, 0.1, 0.2]],
        [[0.0, -1.7, 0.0], [1.7, 0.0, 0.0], [0.0, 0.0, 0.0]],
    ], dtype=float)

    s_ref, w_ref, d_ref = reference.decompose_gradient(grad)
    s_nat, w_nat, d_nat = backend.decompose_gradient(grad)

    np.testing.assert_allclose(s_nat, s_ref, rtol=0.0, atol=1e-14)
    np.testing.assert_allclose(w_nat, w_ref, rtol=0.0, atol=1e-14)
    np.testing.assert_allclose(d_nat, d_ref, rtol=0.0, atol=1e-14)

    u = np.array([[0.3, -0.2, 0.7], [1.0, 0.5, -0.25]], dtype=float)
    i_ref = reference.invariants(u, w_ref, s_ref)
    i_nat = backend.invariants(u, w_nat, s_nat)
    for key in i_ref:
        np.testing.assert_allclose(i_nat[key], i_ref[key], rtol=0.0, atol=1e-14)

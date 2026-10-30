"""Guard against the A077 Windows G5 flat-native vs 2D-Python mismatch.

Pure interface tests: do not certify any physical Euler or spin claims.
"""
import numpy as np
import pytest
from experiment.pipeline import _native_ring_trajectory


def test_g5_native_flat_vector_matches_python_time_major_matrix():
    python_ref = np.arange(401 * 4, dtype=np.float64).reshape(401, 4)
    native_return = python_ref.ravel().tolist()  # C++ std::vector<double>
    alt = _native_ring_trajectory(native_return, python_ref.shape)
    np.testing.assert_array_equal(alt, python_ref)
    assert alt.shape == (401, 4)


def test_g5_native_wrong_number_of_elements_rejected():
    with pytest.raises(ValueError, match="flat vector of length 1604"):
        _native_ring_trajectory(np.zeros(1603), (401, 4))


def test_g5_native_nonfinite_rejected():
    for bad in (float('nan'), float('inf'), -float('inf')):
        native = np.zeros(1604)
        native[100] = bad
        with pytest.raises(ValueError, match="nonfinite"):
            _native_ring_trajectory(native, (401, 4))


def test_g5_native_wrong_rank_rejected():
    with pytest.raises(ValueError, match="output shape"):
        _native_ring_trajectory(np.zeros((401,4)), (401, 4))

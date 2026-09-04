from __future__ import annotations

import numpy as np
import pytest

from native_ext.fallback import biot_savart as biot_py
from native_ext.fallback import circle, default_queries, min_abs as min_abs_py, vec_add as vec_add_py


def test_parity_vec_add(native_mod):
    if native_mod is None:
        pytest.skip("native extension not built")
    a = np.linspace(-1.0, 1.0, 32)
    b = np.linspace(2.0, 4.0, 32)
    got = np.asarray(native_mod.vec_add(a, b, False, False))
    assert np.allclose(got, vec_add_py(a, b))


def test_parity_min_abs(native_mod):
    if native_mod is None:
        pytest.skip("native extension not built")
    rng = np.random.default_rng(0)
    x = rng.normal(size=300)
    got = float(native_mod.min_abs(x, False, False))
    assert np.isclose(got, min_abs_py(x), rtol=0, atol=1e-12)


def test_parity_biot_savart(native_mod):
    if native_mod is None:
        pytest.skip("native extension not built")
    p = circle(64, 4.0)
    q = default_queries(32, 10.0)
    vc = np.asarray(native_mod.biot_savart(p, q, 1.0, 1.0, False, False))
    vp = biot_py(p, q, 1.0, 1.0)
    assert np.allclose(vc, vp, rtol=2e-12, atol=2e-13)

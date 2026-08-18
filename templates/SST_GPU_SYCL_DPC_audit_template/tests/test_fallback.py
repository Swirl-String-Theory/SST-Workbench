from __future__ import annotations

import numpy as np

from native_ext.fallback import biot_savart, circle, default_queries, min_abs, vec_add


def test_fallback_vec_add():
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([4.0, 5.0, 6.0])
    assert np.allclose(vec_add(a, b), [5.0, 7.0, 9.0])


def test_fallback_min_abs():
    x = np.array([-2.5, 0.5, 3.0])
    assert min_abs(x) == 0.5


def test_fallback_min_abs_empty():
    assert min_abs(np.array([])) == float("inf")


def test_fallback_biot_savart():
    p = circle(32, 4.0)
    q = default_queries(8, 10.0)
    vel = biot_savart(p, q, 1.0, 1.0)
    assert vel.shape == (8, 3)
    assert np.isfinite(vel).all()


def test_fallback_circle_closed_length():
    p = circle(400, 4.0)
    seg = np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1).sum()
    assert abs(seg - 2 * np.pi * 4.0) / (2 * np.pi * 4.0) < 2e-3

import numpy as np

from sstcbhf.geometry import compute_geometry, sampled_thickness_proxy


def test_unit_circle_geometry():
    n = 256
    t = 2.0 * np.pi * np.arange(n) / n
    points = np.column_stack([np.cos(t), np.sin(t), np.zeros(n)])
    geom = compute_geometry(points)
    thickness = sampled_thickness_proxy(geom, exclusion_fraction=0.10)
    assert abs(geom.length - 2.0 * np.pi) < 2e-3
    assert abs(np.mean(geom.curvature) - 1.0) < 2e-3
    assert abs(thickness["thickness_proxy"] - 1.0) < 2e-3

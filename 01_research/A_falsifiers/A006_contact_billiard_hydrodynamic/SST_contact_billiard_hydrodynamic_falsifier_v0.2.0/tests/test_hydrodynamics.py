import numpy as np

from sstcbhf.constants import R_C
from sstcbhf.geometry import compute_geometry, sampled_thickness_proxy
from sstcbhf.hydrodynamics import hydrodynamic_force_test


def test_regularized_vortex_ring_is_relative_equilibrium():
    n = 32
    t = 2.0 * np.pi * np.arange(n) / n
    points = np.column_stack([np.cos(t), np.sin(t), np.zeros(n)])
    geom = compute_geometry(points)
    thickness = sampled_thickness_proxy(geom, exclusion_fraction=0.10)["thickness_proxy"]
    result = hydrodynamic_force_test(
        geom,
        thickness=thickness,
        core_ratio=0.2,
        physical_thickness_m=R_C,
    )
    assert result.relative_equilibrium_residual < 1e-10
    assert result.fitted_shape_residual < 1e-6
    assert result.normal_alignment_cosine > 0.999999
    assert result.fitted_scale_N > 0.0
    assert result.tension_cv < 1e-6

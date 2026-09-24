import numpy as np
from sst_kelvin_workbench.measure import (
    block_measure,
    clenshaw_curtis_weights,
    cylindrical_weights,
    radial_grid,
    weighted_inner,
)


def test_clenshaw_curtis_integrates_constant():
    w = clenshaw_curtis_weights(17)
    assert abs(float(np.sum(w)) - 2.0) < 1e-12


def test_cylindrical_measure_integrates_r():
    rmax = 5.0
    r = radial_grid(36, rmax)
    w = cylindrical_weights(r, rmax)
    assert abs(float(np.sum(w)) - 0.5 * rmax * rmax) < 0.05


def test_weighted_inner_not_euclidean():
    r = radial_grid(16, 5.0)
    w = block_measure(cylindrical_weights(r, 5.0), 1)
    x = np.ones(16, dtype=complex)
    eucl = complex(np.vdot(x, x))
    meas = weighted_inner(x, x, w)
    assert abs(meas - eucl) > 1.0

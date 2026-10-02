import numpy as np

from sstcbhf.billiard import scan_billiard
from sstcbhf.contact import PeriodicLiftMap


def test_exact_period_n_shift_map():
    n = 9
    s = np.arange(256, dtype=float) / 256.0
    values = s + 1.0 / n
    contact_map = PeriodicLiftMap(s, values, winding=1)
    result = scan_billiard(contact_map, period=n, grid=2048)
    assert result.closure_residual < 1e-10
    assert result.min_lower_period_residual > 0.10
    assert result.unique_orbit_points == 9

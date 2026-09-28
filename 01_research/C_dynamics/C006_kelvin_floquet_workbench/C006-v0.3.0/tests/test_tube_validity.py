import numpy as np
from sst_kelvin_workbench.kelvin import make_ring
from sst_kelvin_workbench.tube_validity import evaluate_tube, max_curvature


def test_ring_curvature_is_one_over_radius():
    ring = make_ring(64, 1.0)
    assert abs(max_curvature(ring) - 1.0) < 0.05


def test_tube_fail_does_not_shrink_rmax():
    ring = make_ring(32, 1.0)
    rec = evaluate_tube(ring, a=0.4, rmax=5.0, c_kappa=0.30, c_d=1.0, label="tight")
    assert rec["status"] == "INDETERMINATE_TUBE_CHART_INVALID"
    assert rec["rmax_was_reduced"] is False
    assert rec["rmax"] == 5.0


def test_unit_ring_passes_frozen_factors():
    ring = make_ring(64, 1.0)
    rec = evaluate_tube(ring, a=0.05, rmax=5.0, c_kappa=0.30, c_d=1.0, label="ring")
    assert rec["kappa_ok"] is True
    assert rec["distance_ok"] is True
    assert rec["status"] == "TUBE_VALID"

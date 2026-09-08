import math
import numpy as np

from sst_threaded_hole_falsifier.hole_transport import (
    estimate_hole_axis,
    kelvin_mcfarlane_y2_over_a2,
    kelvin_oracle,
    kelvin_pair_translation,
    kelvin_point_vortex_pair_velocity,
)
from sst_threaded_hole_falsifier.model import CurveSet
from sst_threaded_hole_falsifier.workflow import decision


def test_kelvin_mcfarlane_oracle():
    r = kelvin_oracle()
    assert r['pass'] is True
    assert abs(r['stagnation_y_over_a_numeric'] - math.sqrt(3.0)) < 2e-10
    assert abs(r['separatrix_x_edge_over_a_numeric'] - 2.087253791) < 2e-8
    assert r['max_implicit_streamline_residual'] < 5e-10


def test_kelvin_removable_center_limit_is_three_without_nan():
    x = np.array([0.0, 1e-12, -1e-12])
    y2 = kelvin_mcfarlane_y2_over_a2(x)
    assert np.all(np.isfinite(y2))
    assert np.allclose(y2, 3.0, rtol=0.0, atol=1e-12)


def test_kelvin_stagnation_direct_velocity_check():
    y = math.sqrt(3.0)
    v = kelvin_point_vortex_pair_velocity(np.array([[0.0, y]]))[0]
    assert abs(v[1] - kelvin_pair_translation()) < 1e-13
    assert abs(v[0]) < 1e-13


def test_geometry_only_axis_finds_torus_hole():
    # A circular centerline in the x-y plane has its widest straight central
    # passage along +/-z.  The sign is canonicalized by the detector.
    t = 2.0 * math.pi * np.arange(128) / 128
    circle = np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])
    cs = CurveSet.from_components([circle])
    g = estimate_hole_axis(cs, n_dirs=512)
    axis = np.asarray(g['axis'])
    assert abs(axis[2]) > 0.985
    assert g['clearance_quantile'] > 0.95


def test_hole_blind_decision_uses_only_preregistered_costs():
    a = {
        'dynamic_status': 'PASS_FULL_HORIZON',
        'hole_robustness_cost': 0.1,
        'hole_geometry_collapse_cost': 0.1,
        'hole_class_instability_cost': 0.1,
        'hole_lagrangian_incoherence_cost': 0.1,
    }
    b = {
        'dynamic_status': 'PASS_FULL_HORIZON',
        'hole_robustness_cost': 0.8,
        'hole_geometry_collapse_cost': 0.8,
        'hole_class_instability_cost': 0.8,
        'hole_lagrangian_incoherence_cost': 0.8,
    }
    d = decision(a, b, {'decision_mode':'hole_robustness','pair_tie_log_margin':0.0})
    assert d['decision_basis'] == 'HOLE_ROBUSTNESS_COSTS'
    assert d['winner_anonymous'] == 'A'
    assert d['median_log_ratio_A_over_B'] < 0


def _unit_ring(n=72):
    t = 2.0 * math.pi * np.arange(n) / n
    return CurveSet.from_components([np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])])


def _ring_cfg(core):
    return {
        'carrier_n':72,
        'thread_n':16,
        'core':core,
        'core_model':'gp',
        'vortexlab_c0':0.1395,
        'hole_axis_directions':64,
        'hole_axis_clearance_quantile':0.02,
        'hole_seed_radius_fraction':0.58,
        'hole_seed_radius_scale_cap':0.38,
        'hole_gate_extent_scale':1.15,
        'hole_tracer_seeds':7,
        'hole_streamline_arclength_scale':8.0,
        'hole_streamline_ds_fraction':0.03,
        'hole_axis_stagnation_samples':49,
        'hole_through_fraction_pass':0.50,
        'hole_resident_fraction_pass':0.72,
        'hole_side_escape_max':0.35,
        'hole_pinch_center_speed_fraction':0.035,
        'hole_pinch_coherence_min':0.50,
        'hole_chi_min_translation_fraction':0.05,
    }


def test_frozen_ring_detector_distinguishes_captured_and_open_regimes():
    # This is a numerical detector regression, not a precision determination of
    # the Rankine thin-ring critical ratio.  Thick and very thin regularized
    # rings must land on opposite sides of the carried-fluid topology change.
    from sst_threaded_hole_falsifier.hole_transport import frozen_hole_metrics
    cs = _unit_ring()
    thick = frozen_hole_metrics(cs, np.array([1.0]), 1, _ring_cfg(0.035))
    thin = frozen_hole_metrics(cs, np.array([1.0]), 1, _ring_cfg(0.005))
    assert thick['transport_class'] == 'CAPTURED_ATMOSPHERE'
    assert thick['chi_hole_generic_valid'] is True
    assert thick['chi_hole_generic'] > 1.0
    assert thin['transport_class'] == 'OPEN_CHANNEL'
    assert thin['chi_hole_generic_valid'] is True
    assert thin['chi_hole_generic'] < 1.0
    assert thin['through']['through_fraction'] >= 0.5

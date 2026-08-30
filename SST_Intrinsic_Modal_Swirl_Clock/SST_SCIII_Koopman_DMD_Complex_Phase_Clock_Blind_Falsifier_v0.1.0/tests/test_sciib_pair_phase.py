import numpy as np

from sst_modal_clock.sciib import (
    _pair_discovery_metrics, _pair_discovery_gate,
    pair_phase_metrics, pair_phase_gates,
)


def cfg():
    return {
        'sciib_gate_min_pair_discovery_energy':0.05,
        'sciib_gate_min_energy_balance_ratio':0.35,
        'sciib_gate_min_pair_circularity':0.80,
        'sciib_gate_max_discovery_frequency_split':0.20,
        'sciib_gate_min_discovery_quadrature_plv':0.60,
        'sciib_gate_max_discovery_quadrature_error_rad':0.55,
        'sciib_gate_min_discovery_rotation_sign_fraction':0.80,
        'sciib_gate_min_radius_fraction_of_median':0.25,
        'sciib_gate_min_phase_wraps':4.0,
        'sciib_gate_min_monotonic_fraction':0.90,
        'sciib_gate_min_rotation_sign_fraction':0.90,
        'sciib_gate_min_phase_linearity_r2':0.90,
        'sciib_gate_max_period_cv':0.15,
        'sciib_gate_max_instantaneous_omega_cv':0.50,
        'sciib_gate_max_phase_diffusion_rms_rad':0.75,
        'sciib_gate_max_radius_cv':0.60,
        'sciib_gate_min_radius_retention_ratio':0.40,
        'sciib_gate_max_radius_retention_ratio':2.50,
        'sciib_gate_min_radius_reliable_fraction':0.95,
        'sciib_phase_calibration_fraction':0.40,
        'sciib_gate_max_phase_prediction_rms_rad':1.0,
        'sciib_gate_max_phase_prediction_terminal_error_rad':1.57,
        'sciib_gate_max_basis_gauge_rel_spread':1e-6,
        'sciib_gate_max_basis_gauge_phase_diffusion_rel_spread':1e-5,
    }


def test_clean_quadrature_pair_passes_all_primary_gates():
    c=cfg(); w=2*np.pi/2.7
    td=np.linspace(0,6,500); ad=np.cos(w*td); bd=np.sin(w*td)
    d=_pair_discovery_metrics(td,ad,bd,.44,.43,c)
    assert _pair_discovery_gate(d,c)
    th=np.linspace(6,30,1600); amp=1+.03*np.sin(.07*th)
    ah=amp*np.cos(w*th+.2); bh=amp*np.sin(w*th+.2)
    p=pair_phase_metrics(th,ah,bh,d['trend_t0'],d['trend_a'],d['trend_b'],d['orientation'],c)
    gates=pair_phase_gates(d,p,c,'natural')
    assert all(gates)
    assert p['phase_wraps']>8
    assert p['rotation_sign_fraction']>.99
    assert p['basis_gauge_frequency_rel_spread']<1e-9


def test_collinear_pair_fails_discovery_quadrature():
    c=cfg(); t=np.linspace(0,8,600); a=np.cos(2*t); b=.9*np.cos(2*t+.05)
    d=_pair_discovery_metrics(t,a,b,.45,.42,c)
    assert not _pair_discovery_gate(d,c)
    assert d['discovery_quadrature_error_rad']>c['sciib_gate_max_discovery_quadrature_error_rad']


def test_frequency_split_pair_fails_discovery():
    c=cfg(); t=np.linspace(0,12,800); a=np.cos(2*t); b=np.sin(2.7*t)
    d=_pair_discovery_metrics(t,a,b,.45,.40,c)
    assert d['discovery_frequency_split']>c['sciib_gate_max_discovery_frequency_split']
    assert not _pair_discovery_gate(d,c)


def test_odd_channel_cannot_be_primary_candidate():
    c=cfg(); w=2.1; td=np.linspace(0,8,600); d=_pair_discovery_metrics(td,np.cos(w*td),np.sin(w*td),.45,.44,c)
    th=np.linspace(8,32,1600); p=pair_phase_metrics(th,np.cos(w*th),np.sin(w*th),d['trend_t0'],d['trend_a'],d['trend_b'],d['orientation'],c)
    g=pair_phase_gates(d,p,c,'odd')
    assert all(g[:-1]) and not g[-1]


def test_pair_phase_is_invariant_under_mode_sign_and_swap_gauge():
    c=cfg(); w=1.8; td=np.linspace(0,8,500); d=_pair_discovery_metrics(td,np.cos(w*td),np.sin(w*td),.45,.44,c)
    th=np.linspace(8,35,1700); p=pair_phase_metrics(th,np.cos(w*th),np.sin(w*th),d['trend_t0'],d['trend_a'],d['trend_b'],d['orientation'],c)
    assert p['basis_gauge_period_rel_spread']<1e-9
    assert p['basis_gauge_phase_linearity_range']<1e-10

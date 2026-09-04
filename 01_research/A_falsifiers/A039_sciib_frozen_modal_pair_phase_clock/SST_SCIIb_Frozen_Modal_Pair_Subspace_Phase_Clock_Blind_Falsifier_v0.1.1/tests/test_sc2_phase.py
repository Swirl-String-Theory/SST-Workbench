import numpy as np
from sst_modal_clock.sc2 import phase_clock_metrics, phase_clock_gates

CFG={
 'sc2_gate_min_discovery_energy':.03,'sc2_gate_min_holdout_amplitude':1e-5,
 'sc2_gate_min_phase_wraps':4,'sc2_gate_min_monotonic_fraction':.90,
 'sc2_gate_min_phase_linearity_r2':.90,'sc2_gate_max_period_cv':.15,
 'sc2_gate_min_spectral_power':.30,'sc2_gate_min_harmonic_r2':.50,
 'sc2_gate_max_phase_diffusion_rms_rad':.75,'sc2_gate_max_envelope_cv':.60,
 'sc2_gate_min_envelope_retention_ratio':.40,'sc2_gate_max_envelope_retention_ratio':2.5,
 'sc2_gate_min_envelope_reliable_fraction':.95,'sc2_gate_max_phase_prediction_rms_rad':1.0,
 'sc2_gate_max_phase_prediction_terminal_error_rad':1.57,
}

def test_clean_phase_clock_passes():
    t=np.linspace(0,24,2401); y=.2*np.cos(2*np.pi*t/3.0+.4)
    m=phase_clock_metrics(t,y,CFG); g=phase_clock_gates(m,.8,CFG,'natural')
    assert m['phase_wraps']>7
    assert all(g)

def test_ringdown_fails_envelope_gate():
    t=np.linspace(0,24,2401); y=.2*np.exp(-t/4)*np.cos(2*np.pi*t/3.0)
    m=phase_clock_metrics(t,y,CFG); g=phase_clock_gates(m,.8,CFG,'natural')
    assert not g[3]

def test_odd_never_primary_candidate():
    t=np.linspace(0,24,2401); y=.2*np.cos(2*np.pi*t/3.0)
    m=phase_clock_metrics(t,y,CFG); g=phase_clock_gates(m,.8,CFG,'odd')
    assert g[-1] is False

def test_frequency_chirp_fails_predictive_clock():
    t=np.linspace(0,24,2401); phase=2*np.pi*(t/3 + .015*t*t); y=.2*np.cos(phase)
    m=phase_clock_metrics(t,y,CFG); g=phase_clock_gates(m,.8,CFG,'natural')
    assert not (g[2] and g[4])

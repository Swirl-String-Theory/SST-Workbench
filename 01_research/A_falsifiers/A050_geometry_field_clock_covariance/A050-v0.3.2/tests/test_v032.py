import numpy as np
from sst_gfcc_blind.nonstationary import phase_drift_from_series, branch_identity_metrics, branch_retained


def cfg():
    return {
      'minimum_branch_identity_checkpoint_fraction':0.8,'maximum_branch_mode_switches':1,
      'amplitude_floor_fraction':0.15,'minimum_active_fraction':0.5,'minimum_active_samples':128,
      'minimum_total_path_cycles':0.25,'segment_count':8,'minimum_segment_samples':64,
      'segment_linear_r2_min':0.55,'minimum_locally_coherent_segment_fraction':0.75,'piecewise_nrmse_max':0.18,
      'stationary_linear_r2_min':0.85,'stationary_segment_angular_rate_cv_max':0.15,
      'quadratic_r2_min':0.80,'quadratic_delta_bic_min':10.0,'quadratic_nrmse_max':0.25,
      'drift_relative_change_min':0.25,'significant_segment_rate_fraction':0.20,'minimum_significant_rate_segments':4
    }


def test_stationary_phase_classification():
    t=np.linspace(0,100,2049); z=np.exp(1j*(0.12*t+0.3))
    r=phase_drift_from_series(t,z,cfg())
    assert r['classification']=='STATIONARY_COHERENT'
    assert r['angular_rate_sign_reversal_count']==0


def test_coherent_chirp_classification():
    t=np.linspace(0,100,2049); ph=0.04*t+0.0012*t*t; z=np.exp(1j*ph)
    r=phase_drift_from_series(t,z,cfg())
    assert r['classification']=='COHERENT_DRIFTING'
    assert r['delta_bic_quadratic_over_linear']>10


def test_coherent_reversal_classification():
    t=np.linspace(0,100,2049); ph=0.20*t-0.0020*t*t; z=np.exp(1j*ph)
    r=phase_drift_from_series(t,z,cfg())
    assert r['classification']=='COHERENT_REVERSING'
    assert r['positive_rate_segment_count']>0 and r['negative_rate_segment_count']>0


def test_incoherent_random_phase_rejected():
    rng=np.random.default_rng(32026); t=np.linspace(0,100,2049); ph=np.cumsum(rng.normal(0,0.45,len(t))); z=np.exp(1j*ph)
    r=phase_drift_from_series(t,z,cfg())
    assert r['classification']=='INCOHERENT_OR_UNRESOLVED'


def test_branch_retention_is_independent_of_parent_pass():
    p={'pass':False,'checkpoints':[{'selected_mode':3},{'selected_mode':3},{'selected_mode':3},{'selected_mode':3},{'selected_mode':3}]}
    b=branch_identity_metrics(p,cfg()); h=branch_identity_metrics(p,cfg())
    assert b['stable'] is True and b['persistence_gate_pass'] is False
    assert branch_retained(b,h) is True

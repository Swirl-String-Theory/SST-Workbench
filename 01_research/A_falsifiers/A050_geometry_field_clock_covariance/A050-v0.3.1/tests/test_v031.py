import numpy as np
from sst_gfcc_blind.nonstationary import phase_drift_from_series

CFG={
 'amplitude_floor_fraction':0.15,'minimum_active_fraction':0.50,'minimum_active_samples':128,
 'minimum_phase_cycles':0.10,'stationary_linear_r2_min':0.90,
 'stationary_segment_frequency_relative_span_max':0.15,
 'quadratic_r2_min':0.90,'quadratic_delta_bic_min':6.0,
 'segment_count':4,'minimum_segment_samples':32,
 'instantaneous_frequency_sign_consistency_min':0.90,
 'residual_acf_lags':8,'residual_acf_sigma':2.5,
}

def test_stationary_phase_is_classified_stationary():
 t=np.linspace(0.0,40.0,2049); z=np.exp(1j*(0.7*t+0.2))
 r=phase_drift_from_series(t,z,CFG)
 assert r['classification']=='STATIONARY_COHERENT'
 assert r['segmented_frequency']['relative_span']<1e-10

def test_quadratic_phase_is_classified_drifting():
 t=np.linspace(0.0,40.0,2049); z=np.exp(1j*(0.35*t+0.012*t*t+0.1))
 r=phase_drift_from_series(t,z,CFG)
 assert r['classification']=='COHERENT_DRIFTING'
 assert r['delta_bic_quadratic_over_linear']>CFG['quadratic_delta_bic_min']
 assert r['quadratic_frequency_relative_change']>CFG['stationary_segment_frequency_relative_span_max']

def test_random_phase_is_not_promoted_to_coherent():
 rng=np.random.default_rng(31031); t=np.linspace(0.0,40.0,2049); z=np.exp(1j*rng.uniform(-np.pi,np.pi,len(t)))
 r=phase_drift_from_series(t,z,CFG)
 assert r['classification']=='INCOHERENT_OR_UNRESOLVED'

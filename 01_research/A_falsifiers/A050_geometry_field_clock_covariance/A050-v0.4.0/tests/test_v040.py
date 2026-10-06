import numpy as np
from sst_gfcc_blind.mechanisms import two_tone_metrics,instantaneous_rate_metrics,phase_slip_metrics,quotient_recurrence_metrics,smooth_chirp_metrics,mechanism_discrimination

def cfg():
    return {'spectral_candidate_count':8,'spectral_peak_separation_bins':1.5,'spectral_refine_points':9,'two_tone_delta_bic_min':20.0,'two_tone_nrmse_max':0.35,'two_tone_secondary_amplitude_ratio_min':0.10,'two_tone_min_beat_cycles':0.5,'envelope_modulation_depth_min':0.08,'envelope_beat_relative_error_max':0.35,'instantaneous_rate_smoothing_samples':33,'instantaneous_rate_abs_floor':1e-4,'instantaneous_rate_significance_fraction':0.20,'minimum_reversal_separation_samples':64,'reversal_amplitude_ratio_max':0.70,'minimum_reversals_at_amplitude_dips_fraction':0.60,'amplitude_rate_correlation_max_lag_samples':96,'amplitude_rate_correlation_abs_min':0.55,'phase_slip_background_window_samples':31,'phase_slip_absolute_jump_min':0.35,'phase_slip_mad_multiplier':8.0,'phase_slip_minimum_separation_samples':32,'phase_slip_amplitude_ratio_max':0.45,'phase_slip_reversal_match_window_samples':96,'phase_slip_minimum_event_count':1,'phase_slip_minimum_low_amplitude_fraction':0.75,'phase_slip_minimum_reversal_match_fraction':0.50,'smooth_chirp_quadratic_r2_min':0.85,'smooth_chirp_delta_bic_min':20.0,'smooth_chirp_nrmse_max':0.20,'smooth_chirp_relative_change_min':0.25,'smooth_chirp_max_sign_reversals':0,'recurrence_sample_every':8,'recurrence_min_lag_steps':128,'recurrence_max_lag_steps':1024,'recurrence_lag_stride_samples':1,'recurrence_distance_max':0.30,'recurrence_min_pair_count':24,'recurrence_min_repeat_count':2,'rpo_group_phase_advance_concentration_min':0.75}

def test_two_tone_beating_detected():
    t=np.linspace(0,200,4097); z=np.exp(1j*0.22*t)+0.85*np.exp(1j*0.16*t); tone=two_tone_metrics(t,z,cfg()); inst=instantaneous_rate_metrics(t,z,cfg()); assert tone['support']

def test_smooth_chirp_gate():
    phase={'coherent':True,'angular_rate_sign_reversal_count':0,'quadratic_fit':{'r2':0.97,'nrmse':0.08},'delta_bic_quadratic_over_linear':55.0,'quadratic_angular_rate_relative_change':0.6}; assert smooth_chirp_metrics(phase,cfg())['support']

def test_two_tone_does_not_look_like_smooth_chirp_proxy():
    phase={'coherent':True,'angular_rate_sign_reversal_count':2,'quadratic_fit':{'r2':0.95,'nrmse':0.10},'delta_bic_quadratic_over_linear':60.0,'quadratic_angular_rate_relative_change':1.0}; assert not smooth_chirp_metrics(phase,cfg())['support']

def test_phase_slip_detected_at_low_amplitude_event():
    t=np.linspace(0,100,2049); ph=0.08*t; amp=np.ones_like(t); j=len(t)//2; ph[j:]+=1.2; amp[j-2:j+3]=0.05; z=amp*np.exp(1j*ph); inst=instantaneous_rate_metrics(t,z,cfg()); r=phase_slip_metrics(t,z,inst.get('reversal_indices',[]),cfg()); assert r['support']; assert r['event_count']>=1

def test_periodic_symmetry_quotient_gives_rpo_candidate():
    t=np.linspace(0,160,3201); modes=np.array([2,3,4]); theta=0.11*t; per=2*np.pi*t/20
    C=np.column_stack([(0.4+0.08*np.cos(per))*np.exp(1j*(2*theta+0.2)),(1.0+0.15*np.sin(per))*np.exp(1j*3*theta),(0.3+0.05*np.cos(per+0.4))*np.exp(1j*(4*theta-0.5))])
    r=quotient_recurrence_metrics(t,C,modes,3,cfg()); assert r['quotient_recurrence']; assert r['rpo_candidate']

def test_nonperiodic_quotient_rejected():
    rng=np.random.default_rng(7); t=np.linspace(0,160,3201); modes=np.array([2,3,4]); C=np.cumsum(rng.normal(size=(len(t),3))+1j*rng.normal(size=(len(t),3)),axis=0); r=quotient_recurrence_metrics(t,C,modes,3,cfg()); assert not r['rpo_candidate']

import numpy as np
from sst_trpl.observables import chi_t,gauge_rotate,time_reverse_conjugate,phase_lock_metrics

def test_chi_gauge_and_time_odd():
    rng=np.random.default_rng(1); eta=rng.normal(size=(100,2))+1j*rng.normal(size=(100,2))
    c=chi_t(eta); assert np.max(np.abs(c-chi_t(gauge_rotate(eta,0.37))))<1e-12
    assert np.max(np.abs(c+chi_t(time_reverse_conjugate(eta))))<1e-12

def test_locked_phase():
    t=np.linspace(0,10,1001); eta=np.column_stack([np.ones_like(t)/np.sqrt(2),np.exp(1j*(np.pi/2+0.02*np.sin(t)))/np.sqrt(2)])
    m=phase_lock_metrics(t,eta); assert m['coherence']>0.99; assert m['chi_mean']>0.99

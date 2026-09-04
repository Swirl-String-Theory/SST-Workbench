import numpy as np
from sst_modal_clock.modal import recurrence_metrics

def test_chirp_is_not_stationary_clock():
    t=np.linspace(0,50,1200); y=np.sin(1.2*t+0.035*t*t)
    r=recurrence_metrics(t,y,4)
    assert r['valid']
    assert r['period_cv']>.08 or r['multi_return_closure_median']>.35

def test_amplitude_growth_is_detected():
    t=np.linspace(0,50,1200); y=(1+.035*t)*np.sin(1.35*t)
    r=recurrence_metrics(t,y,4)
    assert r['valid']
    assert r['amplitude_cv']>.12 or r['cycle_mean_drift_fraction']>.25

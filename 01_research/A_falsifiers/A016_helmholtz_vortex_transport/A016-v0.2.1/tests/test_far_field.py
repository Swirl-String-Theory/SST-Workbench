import numpy as np
from experiment.metrics import far_field_decay


def circle(n=384):
    a=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.column_stack([np.cos(a),np.sin(a),np.zeros_like(a)])


def test_circle_far_field_is_dipolar():
    r=far_field_decay([circle()],[4.0,6.0,8.0,12.0],32)
    assert r["eligible"]
    assert r["fit_r2"] > 0.97
    assert 2.4 < r["velocity_decay_exponent"] < 3.6

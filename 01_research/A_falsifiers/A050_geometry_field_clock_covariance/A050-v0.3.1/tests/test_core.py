import numpy as np
from sst_gfcc_blind.geometry import make_curve
from sst_gfcc_blind.field import normalized_velocity_on_grid, pressure_like, divergence_rms, gradient_rms
from sst_gfcc_blind.analysis import variance_scaling_scalar, fit_power

def test_curve_and_field_finite():
    p=make_curve("G0001",32,1)
    u,dx=normalized_velocity_on_grid(p,12,3.0,0.12,1024)
    assert np.isfinite(u).all()
    ratio=divergence_rms(u,dx)/max(gradient_rms(u,dx),1e-30)
    assert ratio < 1e-10
    q,_=pressure_like(u,dx)
    assert np.var(q)>0

def test_scaling_fit():
    rng=np.random.default_rng(2)
    q=rng.normal(size=(20,20,20))
    r=[1,2,3,4,5]
    v=variance_scaling_scalar(q,r)
    f=fit_power(r,v,2)
    assert np.isfinite(f["exponent"])
    assert f["exponent"]>1.0

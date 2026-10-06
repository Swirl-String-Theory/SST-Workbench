import numpy as np
from sst_finite_core_falsifier.lagrangian_certification import (
    core_area_mean, complex_overlap, phase_align_series,
    quadratic_power_exponent, richardson_zero_from_two,
)


def test_core_area_mean_constant():
    r=np.linspace(0,2,101); y=np.ones((len(r),9),complex)*(2+3j)
    assert np.allclose(core_area_mean(r,y),2+3j)


def test_phase_align_series():
    x=np.exp(1j*np.linspace(0,1,40)); y=x*np.exp(1j*.73)
    yy,_,ov=phase_align_series(x,y)
    assert ov>0.999999999999
    assert complex_overlap(x,yy)>0.999999999999


def test_quadratic_power():
    d=np.array([.4,.2,.1,.05]); q=7*d*d
    assert abs(quadratic_power_exponent(d,q)-2.0)<1e-12


def test_richardson_zero():
    # C(d)=3+5 d^2 exactly.
    d1=.2; d2=.1
    c1=np.array([3+5*d1*d1+2j]); c2=np.array([3+5*d2*d2+2j])
    c0=richardson_zero_from_two(c1,d1,c2,d2)
    assert np.allclose(c0,3+2j)

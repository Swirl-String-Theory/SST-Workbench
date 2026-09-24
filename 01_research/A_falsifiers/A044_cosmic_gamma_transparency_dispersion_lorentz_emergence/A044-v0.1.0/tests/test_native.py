\
import math
from sst_cgtdlef import _native

def test_intersection():
    x=_native.intersect_bounds([1.22e20,1.21e20],[1.22e21])
    assert x["nonempty"] and x["lower"]==1.22e20 and x["upper"]==1.22e21

def test_birefringent_n1_rejected():
    x=_native.intersect_bounds([3.6e34],[1.22e21])
    assert not x["nonempty"]

def test_poisson_threshold_identity():
    lam=-math.log(0.95)
    assert abs(_native.poisson_at_least_one(lam)-0.05)<1e-14

def test_dispersion_dimensionless():
    eps=_native.dispersion_epsilon(3e5,1.22e21,1)
    assert 2.4e-16 < eps < 2.5e-16

def test_krc():
    x=_native.k_times_length(1.0e12,2.0e-15)
    assert 1.0e4 < x < 1.1e4

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pytest
from holonomy import gauss_link,hopf_pair,unlink_pair,interference_visibility,meridian

@pytest.mark.parametrize('order',[2,4,6])
def test_hopf(order):
    a,b=hopf_pair(48)
    assert abs(abs(gauss_link(a,b,order=order))-1)<.02

@pytest.mark.parametrize('order',[2,4])
def test_unlink(order):
    a,b=unlink_pair(48)
    assert abs(gauss_link(a,b,order=order))<.02

def test_invariance():
    a,b=hopf_pair(48); x=gauss_link(a,b)
    assert abs(gauss_link(a,b[::-1])+x)<1e-8
    assert abs(gauss_link(b,a)-x)<1e-8
    assert abs(gauss_link(a+4,b+4)-x)<1e-8
    assert abs(gauss_link(np.roll(a,5,axis=0),b)-x)<1e-8

def test_meridian():
    a,_=hopf_pair(48)
    assert abs(abs(gauss_link(a,meridian(a),order=4))-1)<.03

def test_toy_interference():
    assert abs(interference_visibility(0,.5)[0]-1)<1e-12
    assert abs(interference_visibility(1,.5)[0])<1e-12
    assert abs(interference_visibility(1,0.)[0]-1)<1e-12

def test_core_regularization_breaks_quantization():
    a,b=hopf_pair(48)
    exact=abs(gauss_link(a,b,core=0.))
    c=abs(gauss_link(a,b,core=.3))
    assert c < exact

def test_clearance_control():
    from holonomy import polygon_pair_min_clearance
    a,b=hopf_pair(48)
    assert polygon_pair_min_clearance(a,b) > 0.01
    a,b=unlink_pair(48)
    assert polygon_pair_min_clearance(a,b) > 1.

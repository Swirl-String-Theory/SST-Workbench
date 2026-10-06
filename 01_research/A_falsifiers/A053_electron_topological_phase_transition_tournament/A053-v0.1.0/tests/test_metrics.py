import math
from a053_etptf.metrics import circular_order, closest_link_class

def test_circular_order_locked():
    assert circular_order([0.2]*20) > 0.999

def test_link_classes():
    assert closest_link_class(1.02)=='L2a1_like'
    assert closest_link_class(1.97)=='L4a1_like'

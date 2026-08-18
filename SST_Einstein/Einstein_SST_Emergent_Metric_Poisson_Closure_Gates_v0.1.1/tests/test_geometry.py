import numpy as np
from einstein_sst_gates.synthetic import circle
from einstein_sst_gates.geometry import resample_closed_py,closed_length_py,estimate_thickness_py

def test_resample_circle_length():
    p=circle(400,4.0);q=resample_closed_py(p,800);assert abs(closed_length_py(q)-2*np.pi*4)/(2*np.pi*4)<2e-4

def test_thickness_positive():
    d=estimate_thickness_py(circle(200,4.0),8);assert d['thickness']>0

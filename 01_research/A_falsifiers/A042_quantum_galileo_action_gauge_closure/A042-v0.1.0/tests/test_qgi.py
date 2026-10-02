import math, unittest
import numpy as np
from sst_qgi.constants import HBAR_SI, h_sst, H_SI
from sst_qgi.qgi import (
    ideal_phase, generalized_phase, finite_pulse_phase,
    lab_action_analytic, lab_action_numeric, freefall_boundary_action, fit_power_law
)

class QGITests(unittest.TestCase):
    def setUp(self):
        self.m=1.44316060e-25
        self.g=9.81
        self.T=8.0e-4

    def test_h_sst_reference(self):
        self.assertAlmostEqual(h_sst(), 6.626069515681023e-34, places=44)
        self.assertLess(abs(h_sst()/H_SI-1.0), 1e-6)

    def test_generalized_a_equals_g(self):
        a=generalized_phase(self.g,self.T,self.m,self.g,HBAR_SI)
        b=ideal_phase(self.T,self.m,self.g,HBAR_SI)
        self.assertLess(abs((a-b)/b),1e-14)

    def test_finite_zero_limit_magnitude(self):
        a=finite_pulse_phase(self.T,0.0,0.0,self.m,self.g,HBAR_SI)
        b=ideal_phase(self.T,self.m,self.g,HBAR_SI)
        self.assertLess(abs(abs(a/b)-1.0),1e-14)

    def test_lab_action(self):
        a=lab_action_analytic(self.T,self.m,self.g)
        n=lab_action_numeric(self.T,self.m,self.g,8193)
        self.assertLess(abs((n-a)/a),1e-6)

    def test_frame_boundary(self):
        a=lab_action_analytic(self.T,self.m,self.g)
        b=freefall_boundary_action(self.T,self.m,self.g)
        self.assertLess(abs((b-a)/a),1e-14)

    def test_cubic_fit(self):
        T=np.array([2,3,4,5,6,8,10],float)*1e-4
        p,_=fit_power_law(T,ideal_phase(T,self.m,self.g,HBAR_SI))
        self.assertLess(abs(p-3.0),1e-12)

if __name__=="__main__":
    unittest.main()

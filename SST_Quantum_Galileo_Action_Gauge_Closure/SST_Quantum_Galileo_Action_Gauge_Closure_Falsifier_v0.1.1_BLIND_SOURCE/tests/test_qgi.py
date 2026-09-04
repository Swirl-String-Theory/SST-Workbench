import unittest
import numpy as np
from sst_qgi.constants import provenance_audit
from sst_qgi.qgi import (
    ideal_action, generalized_action, finite_pulse_action,
    lab_action_analytic, lab_action_numeric, freefall_boundary_action,
    fit_power_law
)

class QGITests(unittest.TestCase):
    def setUp(self):
        self.m=1.44316060e-25
        self.g=9.81
        self.T=8.0e-4

    def test_legacy_echo_is_not_independent(self):
        a=provenance_audit()
        self.assertFalse(a["independent_prediction"])
        self.assertEqual(a["classification"],"ALGEBRAIC_ECHO_CONTROL")

    def test_generalized_a_equals_g(self):
        a=generalized_action(self.g,self.T,self.m,self.g)
        b=ideal_action(self.T,self.m,self.g)
        self.assertLess(abs((a-b)/b),1e-14)

    def test_finite_zero_limit_magnitude(self):
        a=finite_pulse_action(self.T,0.0,0.0,self.m,self.g)
        b=ideal_action(self.T,self.m,self.g)
        self.assertLess(abs(abs(a/b)-1.0),1e-14)

    def test_lab_action(self):
        a=lab_action_analytic(self.T,self.m,self.g)
        n=lab_action_numeric(self.T,self.m,self.g,8193)
        self.assertLess(abs((n-a)/a),1e-6)

    def test_frame_boundary(self):
        a=lab_action_analytic(self.T,self.m,self.g)
        b=freefall_boundary_action(self.T,self.m,self.g)
        self.assertLess(abs((b-a)/a),1e-14)

    def test_cubic_fit_action(self):
        T=np.array([2,3,4,5,6,8,10],float)*1e-4
        p,_=fit_power_law(T,ideal_action(T,self.m,self.g))
        self.assertLess(abs(p-3.0),1e-12)

if __name__=="__main__":
    unittest.main()

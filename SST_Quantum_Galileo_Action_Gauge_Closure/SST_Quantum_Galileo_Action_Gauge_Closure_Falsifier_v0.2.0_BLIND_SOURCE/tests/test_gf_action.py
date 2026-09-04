import math, unittest
from sst_qgi.gf_action import (
    rankine_specific_action, geometry_action_coefficients, absolute_rankine_action
)

class GFActionTests(unittest.TestCase):
    def test_rankine_specific_action(self):
        gamma=1.234e-8
        r=rankine_specific_action(gamma)
        self.assertAlmostEqual(r["h_over_m_m2_s"],gamma/2.0)
        self.assertAlmostEqual(r["hbar_over_m_m2_s"],gamma/(4.0*math.pi))
        self.assertLess(r["two_pi_identity_rel"],1e-15)

    def test_geometry_coefficients(self):
        g=geometry_action_coefficients(20.0,0.5)
        self.assertTrue(g["qualified"])
        self.assertAlmostEqual(g["Lhat_radius"],40.0)
        self.assertAlmostEqual(g["h_coeff_rho_Gamma_a3"],20.0*math.pi)
        self.assertAlmostEqual(g["hbar_coeff_rho_Gamma_a3"],10.0)

    def test_absolute_action_matches_specific(self):
        gamma=8.0e-9
        rho=1000.0
        a=1.0e-3
        Lhat=30.0
        r=absolute_rankine_action(rho,gamma,a,Lhat)
        self.assertAlmostEqual(r["h_over_M_m2_s"],gamma/2.0)
        self.assertAlmostEqual(r["hbar_over_M_m2_s"],gamma/(4.0*math.pi))

if __name__=="__main__":
    unittest.main()

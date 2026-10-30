import unittest
import numpy as np
from sttc import checks,hopf_pair,gauss_link,affine_matrix,trefoil,affine_flux_volume

class STTCAnalyticControls(unittest.TestCase):
    def test_all_analytic_controls(self):
        rows,_=checks()
        self.assertGreaterEqual(len(rows),10)
        self.assertEqual([x for x in rows if x['status']!='PASS_ANALYTIC_CONTROL'],[])
    def test_oriented_hopf_link(self):
        a,da,b,db=hopf_pair(96)
        lk=gauss_link(a,da,b,db)
        self.assertAlmostEqual(abs(lk),1,places=6)
    def test_affine_trefoil_local_cauchy_flux(self):
        _,t=trefoil(256)
        x=affine_flux_volume(t,affine_matrix(0.3,1.25),0.1,2.5)
        self.assertLess(x['max_flux_relative_error'],1e-12)
        self.assertLess(x['volume_relative_error'],1e-12)

if __name__=='__main__':unittest.main()

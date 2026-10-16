import json, math, unittest
from pathlib import Path
import numpy as np
from microgravity import models as m
from microgravity import runner as run

class TestPhysics(unittest.TestCase):
    def test_newton_article(self):
        self.assertAlmostEqual(m.newton_force(.0012,.1,.042)/4.54e-12, 1, delta=.002)
        self.assertAlmostEqual(m.newton_gradient(.0012,.1,.042)*1.4e-6/3.02e-16,1,delta=.01)
    def test_newton_small_step(self):
        v=m.newton_gradient(.0012,.1,.042)
        for h in [1e-4,1e-5,1e-6]:
            self.assertAlmostEqual(m.finite_difference_newton(.0012,.1,.042,h)/v,1,delta=2e-5)
    def test_pure_SI_dimensions(self):
        self.assertTrue(m.dims_consistency()['source_matches'])
        self.assertTrue(m.dims_consistency()['force_matches'])
    def test_energy_mass_analytic_vs_quadrature(self):
        a=.003;rho=m.RHO_F; om=m.vortex_omega(a)
        # integrate |v|^2 in 3D via separate Gaussian at 56^3 resolution
        _,xx,yy,zz,h=m.quadrature_grid(a,56)
        E=.5*rho*np.sum(om**2*(xx*xx+yy*yy)*np.exp(-(xx*xx+yy*yy+zz*zz)/a**2))*h**3
        self.assertAlmostEqual(E/(m.energy_mass(a)*m.LIGHT**2),1,delta=1e-7)
    def test_pressure_source_monopole(self):
        s=m.quadrature_grid(.003,56)
        residual=abs(m.source_integral_monopole_discrete(s))/float(np.sum(abs(s[0]))*s[-1]**3)
        self.assertLess(residual,1e-9)
    def test_gradient_nonzero_orientation(self):
        for ax in ('x','z'):
            f=m.pressure_force_component(.042,ax,a=.003,n=40)
            self.assertTrue(np.isfinite(f))
            self.assertNotEqual(f,0)
    def test_zero_swirl_invalid(self):
        with self.assertRaises(ValueError):m.vortex_omega(.003,vmax=0)
    def test_protocol_source_integrity(self):
        self.assertEqual(len(run.protocol_manifest()),len(run.SOURCE_FILES))

if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from experiment.science import AffineVortex,integrate_tracer,rotating_frame_decomposition,analytical_suite,validate_e011_admission,refuse_legacy_inputs

class Tests(unittest.TestCase):
    def test_affine_euler(self):
        for a in (-0.3,0.0,0.25):
            f=AffineVortex(strain=a)
            for t in (0,0.2,2,3):
                r=f.residuals(t)
                self.assertLess(max(r.values()),2e-12)
    def test_kelvin_expansion(self):
        f=AffineVortex(strain=-.2, omega0=1.2)
        self.assertAlmostEqual(f.circulation(0),f.circulation(3),places=13)
        self.assertAlmostEqual(f.omega(3)/f.omega(0),(f.radius(0)/f.radius(3))**2,places=13)
    def test_rotating_frames(self):
        for q in (-3,0,8):
            self.assertLess(rotating_frame_decomposition(1.3,q)['reconstruction_error'],1e-14)
    def test_tracer_integrators(self):
        f=AffineVortex(strain=.2)
        self.assertLess(integrate_tracer(f,2,320,'rk4')['phase_abs_error'],1e-7)
        self.assertLess(integrate_tracer(f,2,1600,'midpoint')['phase_abs_error'],2e-5)
    def test_exact_suite(self):
        self.assertEqual(analytical_suite()['status'],'PASS')
    def test_legacy_exclusion(self):
        self.assertEqual(refuse_legacy_inputs(['dataset/KnotPlot/knots/final/knot_3.1.vect'])['status'],'FAIL')
        self.assertEqual(refuse_legacy_inputs(['E011-v0.3.0/STATIC_READY_INDEX.json'])['status'],'PASS')
    def test_static_is_not_dynamic(self):
        record={'static_status':'STATIC_READY','provider_status':'CROSS_PROVIDER_ROBUST',
                'source_stage':'PRIMARY_REFERENCE','provider_family':'independent_one',
                'raw_sha256':'a'*64,'geometry_sha256':'b'*64}
        result=validate_e011_admission(record,True,False)
        self.assertFalse(result['admitted_for_dynamic_clock'])
        self.assertIn('DYNAMICS_READY_not_certified',result['reasons'])
        self.assertTrue(validate_e011_admission(record,True,True)['admitted_for_dynamic_clock'])
    def test_missing_hash(self):
        record={'static_status':'STATIC_READY','provider_status':'CROSS_PROVIDER_ROBUST',
                'source_stage':'PRIMARY_REFERENCE','provider_family':'independent_one'}
        self.assertFalse(validate_e011_admission(record,True,True)['admitted_for_dynamic_clock'])
    def test_not_static(self):
        self.assertFalse(validate_e011_admission({},True,True)['admitted_for_dynamic_clock'])

if __name__=='__main__':unittest.main()

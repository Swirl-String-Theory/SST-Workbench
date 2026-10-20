import json, math, sys, unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from benchmark import kelvin_hollow_core_omega, kelvin_longwave_omega, inertial_omega, sha256

class AnalyticalRegressions(unittest.TestCase):
    def test_source_checksum(self):
        src=json.loads((ROOT/'configs'/'source_contract.json').read_text())['sources']
        for s in src:
            self.assertEqual(sha256(ROOT/'sources'/s['filename']),s['sha256'])
    def test_kelvin_core_angular_scale(self):
        gamma=0.018;a0=0.00147
        self.assertAlmostEqual(gamma/(2*np.pi*a0**2),1325.7388012652673,places=8)
    def test_kelvin_hollow_longwave_asymptotic(self):
        a0=.00147
        for ka in [1e-3,1e-2]:
            k=ka/a0
            actual=kelvin_hollow_core_omega(np.array([k]))[0]
            approx=kelvin_longwave_omega(np.array([k]))[0]
            self.assertLess(abs((actual-approx)/approx),.0003)
            self.assertLess(actual,0)
    def test_kelvin_units_quadratic_scale_near_zero(self):
        a0=.00147
        vals=kelvin_hollow_core_omega(np.array([.001/a0,.002/a0]))
        self.assertGreater(abs(vals[1]/vals[0]),3)
        self.assertLess(abs(vals[1]/vals[0]),4.01)
    def test_kelvin_domain_checks(self):
        for k in ([0],[1],[-1]):
            if k==[1]:continue
            with self.assertRaises(ValueError):kelvin_hollow_core_omega(k)
    def test_inertial_band_and_limit(self):
        for rpm in [3,6,9,12]:
            fmax=inertial_omega(0,rpm)/(2*np.pi)
            self.assertAlmostEqual(fmax,rpm/30,places=12)
            self.assertAlmostEqual(inertial_omega(np.pi/3,rpm)/(2*np.pi),rpm/60,places=12)
            self.assertAlmostEqual(inertial_omega(np.pi/2,rpm),0.,places=12)
    def test_two_times_rotation_scales(self):
        self.assertAlmostEqual(inertial_omega(0,12),2*12*2*np.pi/60,places=12)
    def test_no_experimental_points_passed_off_as_data(self):
        res=json.loads((ROOT/'results'/'gate_results.json').read_text())
        self.assertEqual(res['experiment_points_used'],0)
        for gate in res['gates'][4:]: self.assertNotEqual(gate['status'],'PASS')
    def test_reported_core_radius_context_not_mixed(self):
        src=json.loads((ROOT/'configs'/'source_contract.json').read_text())
        self.assertIn('1.3 mm',src['reported_parameters']['kelvin_turbulence']['warning'])

if __name__=='__main__':unittest.main()

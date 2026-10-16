from __future__ import annotations
import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import find_branches,harmonic_action,rotor_action,euler_scaling_check,integrate_phase,TAU
class NumericTests(unittest.TestCase):
    def test_free_no_delay(self):
        r=find_branches(TAU,0);self.assertEqual(len(r),1)
    def test_branch_stability(self):
        r=find_branches(TAU,12);self.assertGreater(len(r),3)
        self.assertTrue(any(x['stability']=='STABLE_SUFFICIENT' for x in r))
        self.assertTrue(any(x['stability']=='UNSTABLE_SUFFICIENT' for x in r))
    def test_locked_center(self):
        r=find_branches(TAU,12)
        self.assertTrue(any(abs(x['theta']-TAU)<1e-10 for x in r))
    def test_residual(self):
        self.assertLess(max(x['root_residual'] for x in find_branches(4*TAU,40)),1e-9)
    def test_harmonic_action(self):
        res=harmonic_action(2.3,0.7,3.2);self.assertLess(res['relative_error'],1e-12)
    def test_quadratic_amplitude(self):
        j1=harmonic_action(2.3,0.7,3.2)['J_num_Js'];j2=harmonic_action(2.3,1.4,3.2)['J_num_Js']
        self.assertAlmostEqual(j2/j1,4.)
    def test_rotor_action(self):
        self.assertAlmostEqual(rotor_action(2.,3.),12*math.pi)
    def test_scale_null(self):
        r=euler_scaling_check(1,2,3,1.3);self.assertAlmostEqual(r['measured_ratio'],1.3)
    def test_phase_numerical(self):
        d=integrate_phase(TAU,12,TAU,step=.005,duration=30);self.assertLess(d['abs_error'],.02)
if __name__=='__main__':unittest.main()

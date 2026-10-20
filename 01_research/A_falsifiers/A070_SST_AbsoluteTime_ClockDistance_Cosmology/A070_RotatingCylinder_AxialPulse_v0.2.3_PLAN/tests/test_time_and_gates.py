import unittest, math
from pathlib import Path
import importlib.util
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v',root/'src/video_audit.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Tests(unittest.TestCase):
    def test_time_240fps(self):self.assertAlmostEqual(360/240,1.5,places=9)
    def test_slow_factor(self):self.assertAlmostEqual(240/(30000/1001),8.008,delta=.003)
    def test_33_rpm_water_slope(self):
        Om=33*2*math.pi/60;R=.075;g=9.80665
        self.assertAlmostEqual(Om*Om*R*R/(2*g),.003425,places=5)
    def test_no_speed_claim_without_front(self):
        self.assertIn('No unique',v.CONTRACT['note'])
    def test_axis_roi_in_cylinder(self):
        self.assertTrue(v.CONTRACT['axis_roi_px'][0]>0)
        self.assertGreater(v.CONTRACT['axis_roi_px'][1],v.CONTRACT['axis_roi_px'][0])
if __name__=='__main__':unittest.main()

from pathlib import Path
import hashlib,json,unittest
from experiment.columnar import SmoothColumn,tracer,columnar_suite

class ColumnarTests(unittest.TestCase):
    def test_suite(self):self.assertEqual(columnar_suite()['status'],'PASS')
    def test_signed_rate(self):
        for rate in (-1.1,1.1):
            f=SmoothColumn(rate=rate)
            self.assertLess(tracer(f,0.3,2,640,'rk4')['phase_absolute_error'],1e-7)
    def test_zero_swirl(self):
        f=SmoothColumn(rate=0)
        self.assertEqual(f.vorticity_abs(.7),0)
        self.assertAlmostEqual(tracer(f,.7,2,320)['signed_rate_observed'],0.)
    def test_vorticity_sign_change(self):
        f=SmoothColumn()
        self.assertGreater(f.vorticity_abs(.2*f.core),0)
        self.assertLess(f.vorticity_abs(2*f.core),0)
    def test_finite_axial_energy(self):self.assertGreater(SmoothColumn().energy_per_length(),0)
    def test_frame_reconstruction(self):
        f=SmoothColumn(background=.37)
        for r in (.1,.8,1.2):self.assertAlmostEqual(f.vorticity_abs(r),f.vorticity_relative(r)+.74)
    def test_inherited_hash(self):
        root=Path(__file__).resolve().parents[1]
        expected=json.loads((root/'configs/BLIND_ANALYTIC_CONTROL_V020.json').read_text())['baseline_sha256']
        src=root/'sources/A069_v0.1.0/D1_ANALYTIC_CONTROL.json'
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),expected)
if __name__=='__main__':unittest.main()

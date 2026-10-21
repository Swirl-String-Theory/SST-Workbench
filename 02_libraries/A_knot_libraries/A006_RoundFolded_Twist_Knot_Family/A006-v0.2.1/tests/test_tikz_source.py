import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tikz_roundfold import dense_xyz,resample3,xy_curve,projected_crossings,EXPECTED
from knotplot_io import encode,decode
class GeometryTests(unittest.TestCase):
    def test_knot_identity(self):
        for label,(n,p,d) in EXPECTED.items():
            with self.subTest(label=label):
                src,meta=dense_xyz(label,density=100)
                self.assertEqual(meta['crossings'],n)
                self.assertEqual(meta['alexander_coefficients'],p)
                self.assertEqual(meta['determinant'],d)
    def test_repeated_knotplot_bytes(self):
        for label in EXPECTED:
            src,_=dense_xyz(label,density=80)
            xyz=resample3(src,256)*12
            self.assertTrue(np.array_equal(xyz,decode(encode([xyz]))[0]))
    def test_5_2_unregularized_is_degenerate(self):
        # P3 == P10: input points coincide, needing documented generic perturbation
        from tikz_roundfold import POINTS
        self.assertEqual(POINTS['5_2'][2],POINTS['5_2'][9])
if __name__=='__main__':unittest.main()

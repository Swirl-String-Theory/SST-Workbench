import sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from roundfold import fourplat,resample_closed,fox_determinant,alexander_coefficients,expected_alexander,name
from knotplot_io import encode,decode
from measure import projection_crossings,lengths,min_nonlocal
from borromean import make

class TestRoundFolded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={m:fourplat(m,density=50,cap_pts=40) for m in (3,4,5,6)}
    def test_01_plat_closed_and_one_component(self):
        for m,(p,d) in self.cases.items():
            with self.subTest(m=m):
                self.assertEqual(len(d['orientation']),4)
                self.assertTrue(np.isfinite(p).all())
    def test_02_fox_determinants(self):
        for m,(p,d) in self.cases.items():
            with self.subTest(m=m):self.assertEqual(fox_determinant(d['traversal'],m+2),2*m+1)
    def test_03_alexander_polynomials(self):
        for m,(p,d) in self.cases.items():
            with self.subTest(m=m):self.assertEqual(alexander_coefficients(d),expected_alexander(m))
    def test_04_projection_crossing_counts(self):
        for m,(p,d) in self.cases.items():
            with self.subTest(m=m):self.assertEqual(len(projection_crossings(p)),m+2)
    def test_05_resampling_crossing_counts(self):
        for m,(p,d) in self.cases.items():
            with self.subTest(m=m):
                q=resample_closed(p,512)
                self.assertEqual(len(projection_crossings(q)),m+2)
    def test_06_crossing_height(self):
        for m,(p,d) in self.cases.items():
            with self.subTest(m=m):
                q=resample_closed(p,512)*2
                self.assertGreater(min(abs(v['dz']) for v in projection_crossings(q)),0.2)
    def test_07_kpt_roundtrip(self):
        q=resample_closed(self.cases[3][0],512)
        blob=encode([q]);got=decode(blob)
        self.assertTrue(np.array_equal(q,got[0]))
    def test_08_clearance(self):
        q=resample_closed(self.cases[4][0],512)*2
        self.assertGreater(min_nonlocal(q,neighbor_skip=5)['distance'],0.12)
    def test_09_arclength_sampling(self):
        q=resample_closed(self.cases[3][0],1024)
        self.assertLess(lengths(q)['edge_cv'],0.04)
    def test_10_mirror_invariance(self):
        q=resample_closed(self.cases[3][0],512)
        z=q.copy();z[:,2]*=-1
        self.assertTrue(np.allclose(np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1),np.linalg.norm(np.roll(z,-1,axis=0)-z,axis=1)))
    def test_11_borromean_structure(self):
        cs,record=make((3,3,4),n=768,scale=10)
        self.assertEqual(len(cs),3)
        self.assertTrue(all(abs(x)<.03 for x in record['pairwise_linking_numerical'].values()))
        self.assertTrue(all(x>.12 for x in record['intercomponent_segment_clearance'].values()))
        self.assertTrue(all(x>.12 for x in record['self_segment_clearance_screen']))
    def test_12_invalid_m(self):
        with self.assertRaises(ValueError):fourplat(0)

if __name__=='__main__':unittest.main()

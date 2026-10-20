import math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from seedproduction import historical,arc_sample,projected_crossings,tilt,kpt_bytes,decode_kpt,length_and_cv
class TestSeeds(unittest.TestCase):
    def test_historical_lengths(self):
        for f,L in [('A',19.976521977),('B',31.898600620)]:
            _,calc=arc_sample(f,256)
            self.assertAlmostEqual(calc,L,places=5)
    def test_crossing_delta_z_corrects_written_typo(self):
        d=math.acos(1/3)
        self.assertAlmostEqual(0.7*abs(math.sin(3*d)),7*math.sqrt(2)/27,places=13)
    def test_fixed_projection_writhe_and_exact_reflection(self):
        for fam,wr in [('A',3),('B',-3)]:
            p,_=arc_sample(fam,512)
            for s in (1,-1):
                q=p*np.array([1,1,s]);c=projected_crossings(tilt(q))
                self.assertEqual(len(c),3)
                self.assertEqual(sum(x[2] for x in c),wr*s)
    def test_binary_roundtrip(self):
        p,_=arc_sample('B',128)
        self.assertTrue(np.array_equal(decode_kpt(kpt_bytes(p)),p))
    def test_arclength_uniformity(self):
        for f in 'AB':
            for n in (128,512,1024):
                p,_=arc_sample(f,n);_,cv,_=length_and_cv(p)
                self.assertLess(cv,.02)
if __name__=='__main__':unittest.main()

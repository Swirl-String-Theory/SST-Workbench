import unittest, tempfile, csv
from pathlib import Path
import numpy as np
from sst_maxwell_blind.numerics import scalar_fit_through_origin, cosine_median, nrmse
from sst_maxwell_blind.blind import canonical_commit

class CoreTests(unittest.TestCase):
    def test_scalar_fit(self):
        x=np.array([[1.,2.,3.],[2.,-1.,4.]])
        y=7.5*x
        self.assertAlmostEqual(scalar_fit_through_origin(x,y),7.5,places=12)
        self.assertLess(nrmse(y,7.5*x),1e-14)
        self.assertGreater(cosine_median(x,y),0.999999)
    def test_commit_stable(self):
        e={"name":"x","value":1.25,"unit":"1","role":"test","tolerance_rel":0.1,"salt":"abc"}
        self.assertEqual(canonical_commit(e),canonical_commit(dict(e)))
if __name__=="__main__": unittest.main()

import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from geometry import parse_xyz,arclength_resample,normalized,perimeter,shape_error,q_curvature,perturb_shape,pair_linking

class TestGeometry(unittest.TestCase):
    def ring(self,n=48,r=1.,z=0.):
        t=np.arange(n)*2*np.pi/n
        return np.stack((r*np.cos(t),r*np.sin(t),t*0+z),axis=1)
    def test_parse_three_components(self):
        s='\n\n'.join('\n'.join(' '.join(map(str,p)) for p in self.ring(12)) for _ in range(3))
        self.assertEqual(len(parse_xyz(s)),3)
    def test_rigid_shape(self):
        x=self.ring();a=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
        self.assertLess(shape_error(x@a+np.array([2.,0.,1.]),x),1e-12)
    def test_resample_closed(self):
        self.assertEqual(len(arclength_resample(self.ring(96),25)),25)
    def test_curvature_circle(self):
        self.assertAlmostEqual(q_curvature(self.ring(1024)),1,places=3)
    def test_perturb(self):
        x=self.ring(40);self.assertGreater(np.linalg.norm(perturb_shape(x,.01)-x),0)
    def test_unlinked_gauss(self):
        self.assertLess(abs(pair_linking(self.ring(96),self.ring(96,z=3))),1e-9)

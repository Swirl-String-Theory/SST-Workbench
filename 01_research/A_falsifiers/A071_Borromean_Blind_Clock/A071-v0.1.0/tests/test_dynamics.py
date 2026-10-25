import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import dynamics
from dynamics import velocity,rk4,evolve,run_controls,clock_diagnostic,perturbation_growth

class TestDynamics(unittest.TestCase):
    def ring(self,n=24,r=1,z=0):
        th=2*np.pi*np.arange(n)/n
        return np.stack((r*np.cos(th),r*np.sin(th),th*0+z),axis=1)
    def test_native_python_velocity_parity(self):
        if not dynamics.native_available():self.skipTest('native acceleration absent')
        coords=[self.ring(24,z=0),self.ring(24,z=2.8),self.ring(24,z=5.6)]
        vn=velocity(coords,[1,-1,1],.17)
        handle=dynamics._NATIVE
        try:
            dynamics._NATIVE=None
            vp=velocity(coords,[1,-1,1],.17)
        finally:dynamics._NATIVE=handle
        for a,b in zip(vn,vp):self.assertLess(np.max(np.abs(a-b)),1e-12)
    def test_zero_circulation_static(self):
        x=self.ring(); v=velocity([x],[0.],.1)[0]
        self.assertTrue(np.allclose(v,0))
        y=evolve([x],[0.],.1,.01,2,record=False)['final'][0]
        self.assertTrue(np.array_equal(x,y))
    def test_direction_flip(self):
        x=self.ring();a=velocity([x],[1.],.1)[0];b=velocity([x],[-1.],.1)[0]
        self.assertTrue(np.allclose(a,-b,rtol=1e-12,atol=1e-12))
    def test_circular_ring_axial(self):
        v=velocity([self.ring()],[1.],.1)[0]
        self.assertGreater(v[:,2].mean(),0)
        self.assertLess(abs(v[:,0]).max(),1e-12)
    def test_separate_controls(self):
        x=[self.ring(24,z=i*2.8) for i in range(3)]
        r=run_controls(x,[1,1,1],.1,.001,1)
        self.assertIn('single_0',r)
        self.assertIn('pair_12',r)
        self.assertIn('triple',r)
        self.assertEqual(len(r['comparison']['shape_retention_ratio_triple_to_single']),3)
    def test_growth_method(self):
        x=[self.ring(24,z=i*2.8) for i in range(3)]
        g=perturbation_growth(x,[1,1,1],.1,.001,1,.001)
        self.assertEqual(len(g['per_component']),3)
        self.assertEqual(g['stabilization_claim'].split('_')[0],'UNRESOLVED')
    def test_short_clock_fails_closed(self):
        x=self.ring();r=evolve([x],[1],.1,.001,2)
        from dynamics import result_metrics
        self.assertTrue(clock_diagnostic(result_metrics(r,[x]))['status'].startswith('UNRESOLVED'))

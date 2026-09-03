import unittest, numpy as np
from sst_wp.native_ext import NATIVE_AVAILABLE
from sst_wp.geometry import normalize_components
from sst_wp.kernels import velocity_python,energy_sum_python
class TestNative(unittest.TestCase):
 @unittest.skipUnless(NATIVE_AVAILABLE,'native extension not built in this environment')
 def test_parity(self):
  from sst_wp.native_ext import velocity,energy_sum
  t=np.linspace(0,2*np.pi,32,endpoint=False);p,o=normalize_components([np.column_stack([np.cos(t),np.sin(t),.1*np.sin(3*t)])],40)
  a=velocity_python(p,o,1,.05);b=np.asarray(velocity(p,o,1,.05));self.assertLess(np.linalg.norm(a-b)/np.linalg.norm(a),1e-12);self.assertAlmostEqual(energy_sum_python(p,o,.05),energy_sum(p,o,.05),places=10)
if __name__=='__main__':unittest.main()

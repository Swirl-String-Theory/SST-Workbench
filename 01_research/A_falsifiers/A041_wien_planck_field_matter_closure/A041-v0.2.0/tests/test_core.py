import unittest, math, tempfile
import numpy as np
from sst_wp.geometry import normalize_components,spacing_metrics
from sst_wp.kernels import velocity_python,energy_sum_python
from sst_wp.relative_equilibrium import fit_relative_equilibrium
from sst_wp.provenance import audit
from sst_wp import constants as C

class TestCore(unittest.TestCase):
 def setUp(self):
  t=np.linspace(0,2*np.pi,40,endpoint=False);c=np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)]);self.p,self.o=normalize_components([c],48)
 def test_geometry(self): self.assertLess(spacing_metrics(self.p,self.o)['ds_cv'],0.002)
 def test_velocity_finite(self): self.assertTrue(np.isfinite(velocity_python(self.p,self.o,1,.05)).all())
 def test_energy_finite(self): self.assertTrue(math.isfinite(energy_sum_python(self.p,self.o,.05)))
 def test_provenance_echo(self): self.assertLess(abs(audit()['numeric']['ratio']-1),2e-6)
 def test_action_path_excludes_rho_core(self): self.assertIn('rho_core',C.CONTAMINATED_FOR_ACTION)
if __name__=='__main__':unittest.main()

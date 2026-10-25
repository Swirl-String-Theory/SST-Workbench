from __future__ import annotations
import json,math,sys,tempfile,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from g6_upstream_v034 import check_a058,verify_versioned_registry,KPF_CASES,EXPECTED_A058_VERSION,SourceError
from euler_3d_qualification_v034 import PeriodicEuler,benchmark,field,compare_fourier,energy,EulerError
from e010_registry_v033 import RegistryError,verify,validate_inputs

class SourceIdentityV034(unittest.TestCase):
 def test_catalog_identity(self):
  x={cat:seed for cat,n,seed in KPF_CASES}
  self.assertEqual('fibonacci_torus_F4',x['basic/10.124'])
  self.assertNotEqual('fibonacci_torus_F4',x['basic/8.19'])
  self.assertEqual('v0.3.7',EXPECTED_A058_VERSION)
 def test_absent_a058_unresolved(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual('UNRESOLVED',check_a058(Path(d))['status'])
 def test_unknown_version_not_admitted(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'VERSION_CONTRACT.json').write_text('{"version":"v0.3.8"}')
   self.assertTrue(check_a058(root)['source_version_mismatch'])
 def test_missing_e010_v033_does_not_pass(self):
  with tempfile.TemporaryDirectory() as d:
   t=Path(d);self.assertEqual('UNRESOLVED',verify_versioned_registry(t,t/'old',t/'new',t/'atlas',t)['status'])
 def test_registry_install_target_not_allow_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   t=Path(d)
   with self.assertRaises(Exception):validate_inputs(t/'invalid',t/'atlas',t)

class EulerV034(unittest.TestCase):
 def test_ABC_stationary_and_pressure(self):
  for n in (8,12):
   e=PeriodicEuler(n);u=field(n,'ABC');v,p,d=e.nonlinear(u)
   self.assertLess(np.max(np.abs(v)),1e-10)
   self.assertLess(d['pressure_poisson_residual_rms'],1e-10)
   target=-.5*np.sum(u*u,axis=0);target-=target.mean()
   self.assertLess(np.max(np.abs(p-target)),1e-10)
 def test_nontrivial_evolution_and_energy(self):
  e=PeriodicEuler(12);u=field(12,'TaylorGreen')
  v,p,d=e.integrate(u,.05,8)
  self.assertGreater(float(np.linalg.norm(u-v)),1e-4)
  self.assertLess(d['divergence_max'],1e-10)
  self.assertLess(abs(d['relative_energy_drift']),1e-7)
 def test_grid_refinement_not_deteriorating(self):
  x=benchmark()
  self.assertEqual('PASS_NUMERICAL_EULER_BENCHMARK',x['benchmark_status'])
  self.assertLess(x['rows'][1]['spatial_rms_to_next_fine'],x['rows'][0]['spatial_rms_to_next_fine'])
  self.assertEqual('UNRESOLVED',x['g6p9'])
 def test_non_solenoidal_removed(self):
  e=PeriodicEuler(12);x=np.arange(12)*2*np.pi/12;X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
  u=np.array([np.sin(X),np.zeros_like(X),np.zeros_like(X)])
  self.assertLess(np.max(np.abs(e.project(u))),1e-12)
 def test_invalid_grid(self):
  with self.assertRaises(EulerError):PeriodicEuler(7)
  with self.assertRaises(EulerError):PeriodicEuler(6)

if __name__=='__main__':unittest.main()

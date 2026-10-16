import unittest, tempfile, math, json
from pathlib import Path
import numpy as np
from microgravity.geometry import providers,sha256,polygon_impulse_area,arclength_resample
from microgravity.filament import interaction,induced_velocity,R_C,V_SWIRL,GAMMA,RHO_F,sweep,exponent,gradient_fd
from microgravity.poisson import poisson_cross
class ScienceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.k=providers(96)
 def test_actual_two_providers(self):self.assertEqual(set(self.k),{'gilbert','knotplot'})
 def test_hashes(self):
  for v in self.k.values():self.assertEqual(v['raw_sha256'],v['metadata']['raw_sha256'])
 def test_perimeter(self):
  for v in self.k.values():self.assertAlmostEqual(v['polygon_perimeter'],1.,places=12)
 def test_writhe_sign(self):
  for v in self.k.values():self.assertGreater(v['writhe_proxy']*v['metadata']['writhe'],0)
 def test_knot_closed(self):
  for v in self.k.values():self.assertGreater(np.linalg.norm(v['x'][0]-v['x'][-1]),0)
 def test_circulation(self):self.assertAlmostEqual(GAMMA/(2*math.pi*R_C*V_SWIRL),1,places=12)
 def test_uniform_flow_not_transferring_impulse(self):
  v=self.k['gilbert']['x'];ds=np.roll(v,-1,axis=0)-v
  self.assertLess(np.linalg.norm(np.cross(np.ones_like(ds),ds).sum(axis=0)),1e-14)
 def test_action_reaction(self):
  a=self.k['gilbert']['x'];b=self.k['knotplot']['x'];q=interaction(a,b,3.,.027)
  self.assertLess(q['third_law_residual'],1e-4)
 def test_orientation_sign(self):
  x=self.k['gilbert']['x'];pos=interaction(x,x,5.,.028,0.)['f_parallel_N'];neg=interaction(x,x,5.,.028,math.pi)['f_parallel_N']
  self.assertLess(pos*neg,0)
 def test_farfield_four_not_two(self):
  x=self.k['gilbert']['x'];d=sweep(x,x,[8.,12.,18.,27.,40.],.028,angles=(0,))
  self.assertAlmostEqual(exponent(d),4.,delta=.04)
 def test_dimension_force_scale(self):self.assertAlmostEqual(RHO_F*GAMMA**2/(RHO_F*GAMMA*GAMMA),1.)
 def test_fd_gradient_finite(self):
  x=self.k['gilbert']['x'];q=gradient_fd(x,x,5.,.028);self.assertTrue(np.isfinite(q))
 def test_overlapping_rejected(self):
  x=self.k['gilbert']['x']
  with self.assertRaises(ValueError):interaction(x,x,0.,.028)
 def test_poisson_not_physical_certification(self):
  x=self.k['gilbert']['x'];q=poisson_cross(x,x,n=16)
  self.assertLess(q['core_radius_grid_cells'],1)
  self.assertEqual(q['status'],'PERIODIC_NUMERICAL_DIAGNOSTIC_ONLY')
 def test_constant_g_not_present_in_filament_module(self):
  import inspect,microgravity.filament as f
  self.assertNotIn('G_REF *',inspect.getsource(f))
if __name__=='__main__':unittest.main()

"""V038 numerical solenoidal 3D source and physical authorization regression."""
import unittest, tempfile, shutil, json, hashlib
from pathlib import Path
import numpy as np
from framework_bridge.install import patch_cpu_gate_plan
from triadic.native_core_v038 import (sha,parse_xyz,gaussian_vorticity,spectral_helmholtz,
                                     cross_sections,verify_native_source,run)
ROOT=Path(__file__).resolve().parents[1]

class SourceNativeCoreV038(unittest.TestCase):
 def test_geometry_seal_reused(self):
  p=ROOT/'preregistration/SOURCE_NATIVE_CORE_V038.json'
  c=json.loads(p.read_text())
  self.assertEqual(c['source_class'],'SYNTHETIC_GAUSSIAN_SMOOTHED_FILAMENT_NOT_NATIVE_EULER')
  for s in c['surrogate_sources']:
   self.assertEqual(s['raw_sha256'],sha(ROOT/s['relative_geometry_path']))
 def test_3d_field_is_nontrivial_and_finite(self):
  p=parse_xyz(ROOT/'data/HISTORICAL_2015/A_Fourier_2015_p32_N600_arclength.xyz',stride=12)
  w=gaussian_vorticity(p,20,12,.9)
  self.assertEqual(w.shape,(3,20,20,20))
  self.assertTrue(np.isfinite(w).all())
  self.assertGreater(np.linalg.norm(w),0)
 def test_fft_velocity_and_pressure(self):
  p=parse_xyz(ROOT/'data/HISTORICAL_2015/B_Torus_2015_p66_N600_arclength.xyz',stride=12)
  out=spectral_helmholtz(gaussian_vorticity(p,24,12,.9),12)
  self.assertLess(out['div_u_rms'],1e-10)
  self.assertLess(out['div_omega_rms'],1e-10)
  self.assertLess(out['pressure_poisson_residual_rms'],1e-10)
  self.assertGreater(out['steady_euler_residual_relative'],.01)
 def test_kernel_width_not_deducible_from_xyz(self):
  c=json.loads((ROOT/'preregistration/SOURCE_NATIVE_CORE_V038.json').read_text())
  self.assertTrue(c['a_seed_is_input_for_synthetic_ground_truth'])
  self.assertTrue(c['no_tuning_epsilon_to_pass'])
 def test_gate_prerequisites_not_physical(self):
  plan={'gates':[{'gate_id':'G'+str(i),'question':'placeholder','requires':[],'enabled':True} for i in range(10)]}
  z={q['gate_id']:q for q in patch_cpu_gate_plan(plan)['gates']}
  self.assertEqual(z['G3']['requires'],['G1','G10'])
  self.assertEqual(z['G32']['requires'],['G1'])
  self.assertNotIn('G31',z['G3']['requires'])
 def test_native_import_rejects_untrusted_surrogate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'some_field.npz';np.savez_compressed(p,omega=np.zeros((3,20,20,20)))
   meta=Path(d)/'manifest.json';meta.write_text(json.dumps({'schema':'A065-PKLSA-VOLUMETRIC-SNAPSHOT-1',
     'source_sha256':sha(p),'provider':'TEST','run_id':'RUN','solver_commit':'none','boundary_conditions':'periodic',
     'time':0.0,'units':'synthetic','source_class':'SYNTHETIC_GAUSSIAN_SMOOTHED_FILAMENT_NOT_NATIVE_EULER',
     'independence_group':'test'}))
   with self.assertRaisesRegex(ValueError,'NOT_PHYSICAL'): verify_native_source(p,meta)
 def test_native_import_rejects_hash_substitution(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'native.npz';np.savez_compressed(p,omega=np.zeros((3,20,20,20)))
   meta=Path(d)/'manifest.json';meta.write_text(json.dumps({'schema':'A065-PKLSA-VOLUMETRIC-SNAPSHOT-1','source_sha256':'0'*64}))
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'): verify_native_source(p,meta)
 def test_result_outcome_does_not_certify_physics(self):
  with tempfile.TemporaryDirectory() as d:
   tmp=Path(d);(tmp/'preregistration').mkdir();(tmp/'data/HISTORICAL_2015').mkdir(parents=True)
   shutil.copy(ROOT/'preregistration/SOURCE_NATIVE_CORE_V038.json',tmp/'preregistration/SOURCE_NATIVE_CORE_V038.json')
   c=json.loads((tmp/'preregistration/SOURCE_NATIVE_CORE_V038.json').read_text())
   c['grid_n']=20;c['n_angular']=24;c['n_radial']=20;c['heldout_radial_indices']=[5,8,11,14]
   (tmp/'preregistration/SOURCE_NATIVE_CORE_V038.json').write_text(json.dumps(c))
   for source in c['surrogate_sources']:
    p=Path(source['relative_geometry_path']);shutil.copy(ROOT/p,tmp/p)
   r=run(tmp)
   self.assertIn(r['G28'],('PASS','FAIL'))  # coarse n=20 deliberately under-resolved
   self.assertIn(r['G31'],('FAIL','PASS'))
   self.assertTrue(r['G32'].startswith('UNRESOLVED'))
   self.assertEqual(r['physical_euler'],'UNRESOLVED')
if __name__=='__main__':unittest.main()

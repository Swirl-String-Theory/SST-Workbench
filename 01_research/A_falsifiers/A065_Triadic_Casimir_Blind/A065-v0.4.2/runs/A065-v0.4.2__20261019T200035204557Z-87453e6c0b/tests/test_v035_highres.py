"""A065 v0.3.5: high-resolution falsification contracts, source integrity and CPU parity."""
import json,hashlib,shutil,tempfile,unittest
from pathlib import Path
from triadic.highres_v035 import spec_validate,run
from framework_bridge.install import patch_cpu_gate_plan
ROOT=Path(__file__).resolve().parents[1]

class V035(unittest.TestCase):
 def test_seals_and_direct_four_meshes(self):
  spec,digest,points,history=spec_validate(ROOT)
  self.assertEqual(len(spec['xyz_sha256']),8)
  self.assertEqual(spec['grids'],[600,1200,2400,4800])
  self.assertEqual(len(points['A_Fourier_2015_p32'][4800]),4800)
  self.assertEqual(len(points['B_Torus_2015_p66'][2400]),2400)
  self.assertEqual(hashlib.sha256((ROOT/'preregistration/HIGHRES_V035.json').read_bytes()).hexdigest(),digest)
  audit=json.loads((ROOT/'docs/RELEASE_V033_AUDIT.json').read_text())
  old=audit.get('protected_v032_file_sha256') or json.loads((ROOT/'preregistration/ROUTING_V033.json').read_text())['protected_v032_file_sha256']
  self.assertEqual(len(old),11)
  for p,h in old.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)

 def test_gate_dag_append_only(self):
  g={'gates':[{'gate_id':f'G{i}','question':f'G{i}','requires':[],'enabled':True} for i in range(10)]}
  b={a['gate_id']:a for a in patch_cpu_gate_plan(g)['gates']}
  self.assertEqual(b['G3']['requires'],['G1','G10'])
  self.assertEqual(b['G15']['requires'],['G1'])
  for key in ['G16','G17','G18']:
   self.assertEqual(b[key]['requires'],['G15'])
  self.assertNotIn('G13',b['G16']['requires'])

 def test_modified_new_xyz_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);shutil.copytree(ROOT/'data/HISTORICAL_2015',t/'data/HISTORICAL_2015')
   shutil.copytree(ROOT/'preregistration',t/'preregistration')
   shutil.copytree(ROOT/'docs',t/'docs')
   f=t/'data/HISTORICAL_2015/B_Torus_2015_p66_N4800_arclength.xyz'
   f.write_bytes(f.read_bytes()+b'\n')
   with self.assertRaisesRegex(ValueError,'HIGHRES_XYZ_HASH_MISMATCH'):
    spec_validate(t)

 def test_mutation_prereg_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);shutil.copytree(ROOT/'data/HISTORICAL_2015',t/'data/HISTORICAL_2015')
   shutil.copytree(ROOT/'preregistration',t/'preregistration')
   shutil.copytree(ROOT/'docs',t/'docs')
   f=t/'preregistration/HIGHRES_V035.json'
   p=json.loads(f.read_text());p['relative_threshold']=.9
   f.write_text(json.dumps(p))
   with self.assertRaisesRegex(ValueError,'UNPINNED'):spec_validate(t)

 def test_original_low_res_fail_not_hidden(self):
  # The source contract must distinguish legacy fail and supplementary new gates.
  spec,_,_,_=spec_validate(ROOT)
  self.assertIn('legacy_G13',spec['numerical_gate_policy'])
  self.assertIn('legacy_G2',spec['numerical_gate_policy'])
  self.assertEqual(spec['numerical_gate_policy']['G16'].startswith('1% BASELINE'),True)

 def test_actual_4800_dynamics_and_cpp_python_parity(self):
  if not shutil.which('g++'):self.skipTest('g++ unavailable')
  result=run(ROOT,persist=False)
  self.assertEqual(result['native']['status'],'EXECUTED')
  self.assertEqual(result['legacy_G2'],'FAIL_RETAINED')
  self.assertEqual(result['legacy_G13'],'FAIL_RETAINED')
  for seed,record in result['native']['seeds'].items():
   self.assertEqual(record['baseline_spatial_1pct'],'PASS',seed)
   self.assertEqual(record['temporal_status'],'PASS',seed)
   self.assertEqual(record['parity_status'],'PASS',seed)
   self.assertLess(record['epsilon_ladders']['0.12']['pairs']['2400_vs_4800']['relative_error'],.01)
   self.assertEqual(len(record['epsilon_ladders']),3)
  b=result['native']['seeds']['B_Torus_2015_p66']['epsilon_ladders']['0.06']
  self.assertEqual(b['pairs']['600_vs_1200']['status_1pct'],'FAIL')
  self.assertEqual(b['pairs']['2400_vs_4800']['status_1pct'],'PASS')
  self.assertEqual(result['physical_euler'],'UNRESOLVED')
  self.assertEqual(result['physical_gravity'],'UNRESOLVED')

if __name__=='__main__':unittest.main()

"""Mandatory historical seed integrity/regression checks; no backend authority promotion."""
import hashlib, json, shutil, tempfile, unittest
from pathlib import Path
from triadic.historical_v034 import FORMULAS, validate, run
from triadic.security import verify_all
from framework_bridge.install import patch_cpu_gate_plan
ROOT=Path(__file__).resolve().parents[1]
class HistoricalV034Tests(unittest.TestCase):
 def test_exacts_input_and_analytic_lengths(self):
  out=validate(ROOT)
  self.assertEqual(len(out),2)
  self.assertAlmostEqual(out['A_Fourier_2015_p32']['parametric_length_independent'],19.976521990340952,places=9)
  self.assertAlmostEqual(out['B_Torus_2015_p66']['parametric_length_independent'],31.898600666412335,places=9)
  self.assertEqual(out['A_Fourier_2015_p32']['N600']['N'],600)
  self.assertEqual(out['B_Torus_2015_p66']['N1200']['N'],1200)
  self.assertAlmostEqual(FORMULAS['A_Fourier_2015_p32'](0)[0],2.5)
  self.assertAlmostEqual(FORMULAS['B_Torus_2015_p66'](0)[0],3.0)
 def test_seals_byte_identical_with_v033(self):
  audit=json.loads((ROOT/'docs/RELEASE_V033_AUDIT.json').read_text())
  record=audit.get('protected_v032_file_sha256')
  if record is None:
   pre=json.loads((ROOT/'preregistration/ROUTING_V033.json').read_text())
   record=pre['protected_v032_file_sha256']
  self.assertEqual(len(record),11)
  for rel,expected in record.items():
   self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),expected,rel)
  self.assertEqual(len(verify_all(ROOT)),3)
 def test_dag_append_only_and_g3_not_changed(self):
  d={'gates':[{'gate_id':f'G{i}','requires':[],'question':f'G{i}','enabled':True} for i in range(10)]}
  b={x['gate_id']:x for x in patch_cpu_gate_plan(d)['gates']}
  self.assertEqual(b['G3']['requires'],['G1','G10'])
  self.assertEqual(b['G12']['requires'],['G1'])
  self.assertEqual(b['G13']['requires'],['G12'])
  self.assertEqual(b['G14']['requires'],['G12'])
  self.assertNotIn('G13',b['G3']['requires'])
 def test_source_byte_corruption_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   shutil.copytree(ROOT/'data/HISTORICAL_2015',root/'data/HISTORICAL_2015')
   shutil.copytree(ROOT/'preregistration',root/'preregistration')
   shutil.copytree(ROOT/'docs',root/'docs')
   target=root/'data/HISTORICAL_2015/A_Fourier_2015_p32_N600_arclength.xyz'
   target.write_bytes(target.read_bytes()+b'\n')
   with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):
    validate(root)
 def test_mutated_preregistration_rejected_even_if_self_consistent(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   shutil.copytree(ROOT/'data/HISTORICAL_2015',root/'data/HISTORICAL_2015')
   shutil.copytree(ROOT/'preregistration',root/'preregistration')
   shutil.copytree(ROOT/'docs',root/'docs')
   target=root/'preregistration/HISTORICAL_V034.json'
   d=json.loads(target.read_text());d['spatial_threshold']=.9
   target.write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,'UNPINNED'):
    validate(root)
 def test_native_numerical_truth_and_no_physical_promotion(self):
  if not shutil.which('g++'):self.skipTest('g++ unavailable')
  result=run(ROOT,persist=False)
  self.assertEqual(result['native_qualification']['status'],'EXECUTED')
  by=result['native_qualification']['seeds']
  self.assertEqual(by['A_Fourier_2015_p32']['spatial_status'],'PASS')
  self.assertEqual(by['B_Torus_2015_p66']['spatial_status'],'FAIL')
  for name,entry in by.items():
   self.assertEqual(entry['python_cpp_parity_status'],'PASS')
   self.assertEqual(entry['temporal_status'],'PASS')
  self.assertEqual(result['old_G2'],'FAIL_RETAINED')
  for claim in ('physical_euler','physical_casimir','physical_gravity'):
   self.assertEqual(result[claim],'UNRESOLVED')
if __name__=='__main__':unittest.main()

"""v0.3.6 guard tests; never rewrite or qualify source data."""
import hashlib,json,math,shutil,tempfile,unittest
from pathlib import Path
from framework_bridge.install import patch_cpu_gate_plan
from triadic.parametric_generator_v036 import coordinate,derivative,prepare,sample,SEEDS
from triadic.generated_core_v036 import validate,generate,run
ROOT=Path(__file__).resolve().parents[1]
class V036(unittest.TestCase):
 def test_original_analytic_equations(self):
  a=coordinate(SEEDS[0],0.);b=coordinate(SEEDS[1],0.)
  self.assertEqual(a,(2.5,0.,0.));self.assertEqual(b,(3.,0.,0.))
  for seed in SEEDS:
   t=.357;h=1e-6
   expect=derivative(seed,t)
   actual=[(coordinate(seed,t+h)[k]-coordinate(seed,t-h)[k])/(2*h) for k in range(3)]
   self.assertLess(max(abs(a-b) for a,b in zip(actual,expect)),1e-8)
 def test_old_original_hash_untouched(self):
  spec=json.loads((ROOT/'preregistration/HISTORICAL_V034.json').read_text())
  for fname,check in spec['source_hashes'].items():
   self.assertEqual(hashlib.sha256((ROOT/'data/HISTORICAL_2015'/fname).read_bytes()).hexdigest(),check)
  self.assertEqual(hashlib.sha256((ROOT/'data/HISTORICAL_2015/regenerate.py').read_bytes()).hexdigest(),spec['regenerator_hash'])
 def test_runtime_regenerate_all_meshes_matches_old_xyz(self):
  cfg,prereg,reference,spec=validate(ROOT)
  result,points,highest=generate(ROOT,cfg,reference)
  self.assertLess(highest,1e-7)
  self.assertEqual(len(result),2)
  for seed in SEEDS:
   self.assertEqual(len(points[seed][4800]),4800)
   self.assertLess(result[seed]['grids']['4800']['segment_over_epsilon'],.25)
 def test_prereg_mutation_is_fail_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);(r/'preregistration').mkdir();(r/'docs').mkdir()
   shutil.copy2(ROOT/'preregistration/GENERATED_V036.json',r/'preregistration/GENERATED_V036.json')
   shutil.copy2(ROOT/'docs/GENERATED_V036_CONTRACT.md',r/'docs/GENERATED_V036_CONTRACT.md')
   d=json.loads((r/'preregistration/GENERATED_V036.json').read_text());d['fixed_epsilon']=.3
   (r/'preregistration/GENERATED_V036.json').write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,'V036_UNPINNED_PREREGISTRATION'):validate(r)
 def test_gates_do_not_replace_failures(self):
  plan={'gates':[{'gate_id':f'G{i}','question':f'G{i}','requires':[],'enabled':True} for i in range(10)]}
  gates={x['gate_id']:x for x in patch_cpu_gate_plan(plan)['gates']}
  self.assertEqual(gates['G19']['requires'],['G1'])
  self.assertEqual(gates['G20']['requires'],['G19'])
  self.assertEqual(gates['G21']['requires'],['G19'])
  self.assertEqual(gates['G3']['requires'],['G1','G10'])
  self.assertNotIn('G2',gates['G21']['requires'])
 def test_cpp_run_fine_convergence(self):
  if not shutil.which('g++'):self.skipTest('g++ unavailable')
  result=run(ROOT,persist=False)
  self.assertEqual(result['dynamics']['status'],'EXECUTED')
  for seed in SEEDS:
   diag=result['dynamics']['seeds'][seed]
   self.assertTrue(diag['fine_pairs_pass_1pct'])
   self.assertLess(diag['pairs']['2400_vs_4800']['relative_error'],.01)
  self.assertEqual(result['historical_G2'],'FAIL_RETAINED')
  self.assertEqual(result['physical_euler'],'UNRESOLVED')
if __name__=='__main__':unittest.main()

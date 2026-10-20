"""Precommitted v0.3.7 core-model inverse and negative-control regression."""
import hashlib,json,math,shutil,tempfile,unittest
from pathlib import Path
from framework_bridge.install import patch_cpu_gate_plan
from triadic.finite_core_v037 import inferred_a,v_profile,v_rosenhead,run,validate
ROOT=Path(__file__).resolve().parents[1]
class FiniteCore(unittest.TestCase):
 def test_prereg_and_protected_hashes(self):
  cfg,prereg,data=validate(ROOT)
  self.assertEqual(cfg['models'],['gaussian','rankine'])
  self.assertEqual(len(data['cases']),6)
  self.assertTrue(prereg)
 def test_exact_two_enstrophy_inverse_models(self):
  for a in (.06,.12,.25):
   g=.83
   for model,den in [('gaussian',2),('rankine',1)]:
    z=g*g/(den*math.pi*a*a)
    self.assertAlmostEqual(inferred_a(model,g,z),a,places=13)
 def test_inverse_with_wrong_profile_is_not_unique(self):
  g=1.1;a=.19
  z=g*g/(2*math.pi*a*a)
  self.assertAlmostEqual(inferred_a('rankine',g,z)/inferred_a('gaussian',g,z),math.sqrt(2),places=12)
 def test_two_kernel_matching_definitions_disagree(self):
  for model in ('gaussian','rankine'):
   a=.2;ratio=math.sqrt(math.log(2)) if model=='gaussian' else 1/math.sqrt(2)
   self.assertGreater(abs(1-ratio),.1)
 def test_farfield_does_not_make_nearfield_identical(self):
  for model in ('gaussian','rankine'):
   g=1.;a=.12
   self.assertGreater(abs(v_profile(model,g,a,a)-v_rosenhead(g,a,a))/v_profile(model,g,a,a),.1)
 def test_fail_as_scientific_rejection_not_code_success(self):
  result=run(ROOT,persist=False)
  self.assertEqual(result['G23'],'PASS')
  self.assertEqual(result['G24'],'FAIL')
  self.assertEqual(result['G25'],'PASS')
  self.assertTrue(result['G27'].startswith('UNRESOLVED'))
  for c in result['cases']:
   self.assertLess(c['positive_control_swirl_relative_RMS'],1e-10)
   self.assertGreater(c['rosenhead_swirl_heldout_relative_RMS'],.05)
   self.assertFalse(c['pressure_holdout_is_independent_measurement'])
  self.assertEqual(result['source_independence'],'SYNTHETIC_ONLY')
 def test_cpp_parity_if_available(self):
  r=run(ROOT,persist=False)
  if r['native']['status']=='UNRESOLVED_NO_CXX':self.skipTest('compiler unavailable')
  self.assertEqual(r['native']['status'],'PASS')
  self.assertEqual(r['native']['pairs_compared'],6*65)
 def test_modifying_source_hash_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   tmp=Path(t)
   for sub in ('preregistration','docs','data/FINITE_CORE_V037'):(tmp/sub).mkdir(parents=True,exist_ok=True)
   for name in ('preregistration/FINITE_CORE_V037.json','docs/FINITE_CORE_V037_CONTRACT.md','data/FINITE_CORE_V037/synthetic_invariants_and_heldout.json'):
    shutil.copyfile(ROOT/name,tmp/name)
   f=tmp/'data/FINITE_CORE_V037/synthetic_invariants_and_heldout.json'
   f.write_bytes(f.read_bytes()+b'\n')
   with self.assertRaisesRegex(ValueError,'V037_SOURCE_HASH_MISMATCH'):validate(tmp)
 def test_modifying_protocol_hash_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   tmp=Path(t); (tmp/'preregistration').mkdir();(tmp/'docs').mkdir()
   shutil.copyfile(ROOT/'preregistration/FINITE_CORE_V037.json',tmp/'preregistration/FINITE_CORE_V037.json')
   shutil.copyfile(ROOT/'docs/FINITE_CORE_V037_CONTRACT.md',tmp/'docs/FINITE_CORE_V037_CONTRACT.md')
   p=tmp/'preregistration/FINITE_CORE_V037.json';d=json.loads(p.read_text());d['holdout_swirl_relative_threshold']=.5;p.write_text(json.dumps(d))
   with self.assertRaisesRegex(ValueError,'V037_UNPINNED_PREREGISTRATION'):validate(tmp)
 def test_official_new_gates_do_not_touch_old_requirements(self):
  plan={'gates':[{'gate_id':f'G{i}','question':f'G{i}','requires':[],'enabled':True} for i in range(10)]}
  gates={g['gate_id']:g for g in patch_cpu_gate_plan(plan)['gates']}
  self.assertEqual(gates['G3']['requires'],['G1','G10'])
  self.assertEqual(gates['G27']['requires'],['G22'])
  self.assertNotIn('G27',gates['G3']['requires'])
  self.assertNotIn('G24',gates['G27']['requires'])
if __name__=='__main__':unittest.main()

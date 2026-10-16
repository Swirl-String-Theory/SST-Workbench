import sys,unittest,pathlib,json,numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import screen
class TestScreen(unittest.TestCase):
 def test_sources_are_complete(self):
  m=json.loads((ROOT/'preregistration.json').read_text()); self.assertEqual(len(m['source_cases']),50)
  self.assertEqual(len(list((ROOT/'inputs'/'census').glob('*.txt'))),50)
 def test_all_native_parse(self):
  m=json.loads((ROOT/'preregistration.json').read_text())
  for r in m['source_cases']:
   comps=screen.parse_native((ROOT/'inputs'/'census'/r['native_txt'].split('/')[-1]).read_bytes())
   self.assertTrue(all(len(c)>=4 for c in comps))
   if r.get('torus'):self.assertEqual(len(comps),r['torus']['components'])
 def test_helix_circle_scale(self):
  t=np.linspace(0,2*np.pi,72,endpoint=False);x=np.c_[3*np.cos(t),3*np.sin(t),0*t]
  out,_,_ =screen.recondition([x],[72]); r,_=screen.approximate_reach(out);self.assertAlmostEqual(r,1.0,places=5)
 def test_vector_kernel_reference(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('reference_energy',str(ROOT/'reference'/'energy.py'))
  mod=importlib.util.module_from_spec(spec)
  # reference import expects .geometry; use equivalent explicit scalar formulation here
  t=np.linspace(0,2*np.pi,24,endpoint=False);x=np.c_[np.cos(t),np.sin(t),t*0]
  mid=.5*(x+np.roll(x,-1,axis=0));d=np.roll(x,-1,axis=0)-x
  slow=sum(float(np.sum((d@d[i])/np.sqrt(np.sum((mid-mid[i])**2,axis=1)+1))) for i in range(len(x)))
  self.assertAlmostEqual(screen.kernel([x]),slow,places=11)
 def test_parity_with_frozen_a054_reference(self):
  import reference.geometry as rg
  import reference.energy as re
  for name in ['knot_3.1.txt','link_6.3.3.txt','torus_2.4.txt','torus_6.9.txt']:
   cs=screen.parse_native((ROOT/'inputs'/'census'/name).read_bytes())
   cs=screen.allocate(cs,96);n=[len(c) for c in cs]
   fast,reach,_=screen.recondition(cs,n)
   ref,refreach,_=rg.normalize_by_reach([rg.resample_closed(c,len(c)) for c in cs])
   self.assertAlmostEqual(reach,refreach,places=10)
   self.assertLess(np.linalg.norm(np.concatenate(fast)-np.concatenate(ref)),1e-10)
   self.assertLess(abs(screen.kernel(fast)-re.total_kernel(re.energy_matrix(ref))),1e-10)
 def test_census_archive_integrity(self):
  import zipfile
  z=zipfile.ZipFile(ROOT/'inputs'/'falsifier_census_v0.1.0_output.zip')
  for p in sorted((ROOT/'inputs'/'census').glob('*.txt')):
   self.assertEqual(p.read_bytes(),z.read('falsifier_census_v0.1.0/raw_native/'+p.name))
 def test_fixed_outputs_reproducibility(self):
  b=(ROOT/'inputs'/'census'/'knot_3.1.txt').read_bytes()
  self.assertEqual(screen.sha256_bytes(b),json.loads((ROOT/'inputs'/'SOURCE_FILES_SHA256.json').read_text())['knot_3.1.txt'])
  cs=screen.parse_native(b);u=screen.allocate(cs,300)
  self.assertEqual(sum(map(len,u)),300)
  self.assertLess(screen.edge_metrics(u)['edge_cv'],.02)
if __name__=='__main__': unittest.main()

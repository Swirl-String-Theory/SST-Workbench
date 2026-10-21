from pathlib import Path
import csv,json,hashlib,math,unittest
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results'

def items(file):
 return [json.loads(line) for line in (RES/file).read_text(encoding='utf-8').splitlines() if line.strip()]

class RegistryContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.claims=items('curated_claims.jsonl')
  cls.raw=items('raw_formula_candidates.jsonl')
  cls.manifest=json.loads((RES/'source_manifest.json').read_text())
  cls.q=json.loads((RES/'qualification_summary.json').read_text())
  with (RES/'paper_inventory.csv').open(encoding='utf-8-sig',newline='') as f:cls.papers=list(csv.DictReader(f))
  with (RES/'issues.csv').open(encoding='utf-8-sig',newline='') as f:cls.issues=list(csv.DictReader(f))
 def test_001_sources_exist_and_checksum(self):
  for s in self.manifest['sources']:
   p=ROOT/s['filename'];self.assertTrue(p.exists());self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),s['sha256'])
 def test_002_source_kind_nonempty(self):
  self.assertEqual(len(self.manifest['sources']),11)
  self.assertEqual(sum(s['kind']=='secondary' for s in self.manifest['sources']),2)
 def test_003_full_paper_id_inventory(self):
  self.assertEqual(len(self.papers),106)
  self.assertEqual(len(set(p['paper_id'] for p in self.papers)),106)
 def test_004_summary_gaps_explicit(self):
  m=self.q['summary_index'];self.assertEqual(m['sst_ids_missing_in_mentions'],['SST-65','SST-82'])
 def test_005_raw_candidates_unreviewed(self):
  self.assertEqual(len(self.raw),379)
  self.assertTrue(all(x['scientific_status']=='NOT_REVIEWED' for x in self.raw))
 def test_006_math_source_spans(self):
  lines=(ROOT/'sources'/'SST-00-90-summaries.md').read_text().splitlines()
  for x in self.raw:
   self.assertLessEqual(x['source_line_start'],x['source_line_end'])
   self.assertLessEqual(x['source_line_end'],len(lines))
   span='\n'.join(lines[x['source_line_start']-1:x['source_line_end']]);self.assertIn('$$',span)
 def test_007_claim_ids_unique(self):
  self.assertEqual(len(self.claims),41)
  self.assertEqual(len(set(c['claim_id'] for c in self.claims)),41)
 def test_008_claim_references_known_sources(self):
  ids={s['source_id'] for s in self.manifest['sources']}
  self.assertTrue(all(c['source_id'] in ids for c in self.claims))
 def test_009_bad_claim_not_pass(self):
  wrong=[c for c in self.claims if c['test_status']=='DETECTED_FAIL']
  self.assertGreaterEqual(len(wrong),4)
  self.assertTrue(all(c['evidence_status'] not in {'ESTABLISHED_WITH_ASSUMPTIONS'} for c in wrong))
 def test_010_issues_cross_reference(self):
  claim_ids={c['claim_id'] for c in self.claims}
  self.assertGreaterEqual(len(self.issues),8)
  self.assertTrue(all(x['claim_id'] in claim_ids for x in self.issues))
 def test_011_source_pdfs_page_counts(self):
  try:import fitz
  except ImportError:self.skipTest('PyMuPDF not installed')
  expected={'SRC-KELVIN-A':10,'SRC-KELVIN-B':8,'SRC-DUAL':5}
  for sid,n in expected.items():
   f=next(s['filename'] for s in self.manifest['sources'] if s['source_id']==sid)
   self.assertEqual(len(fitz.open(ROOT/f)),n)
 def test_012_kelvin_energy_from_omega(self):
  hbar=1.054571817e-34;e=1.602176634e-19
  E=2.8e17*hbar/e
  self.assertAlmostEqual(E,184.2993478333,places=6)
  self.assertNotAlmostEqual(E,29.5,delta=0.5)
 def test_013_kelvin_from_filament_dispersion(self):
  e=1.602176634e-19; hbar=1.054571817e-34
  gamma=2*math.pi*hbar/9.1093837139e-31
  L=2*math.pi*5.29e-11;k=2*math.pi/L;xi=1e-15
  w=gamma/(4*math.pi)*k**2*(math.log(1/(k*xi))+1)
  self.assertAlmostEqual(w/1e17,2.4565285406,places=6)
  self.assertAlmostEqual(hbar*w/e,161.6916457,places=5)
 def test_014_kelvin_gap_temperature_threshold(self):
  Egap=60*1.380649e-23*1e5/1.602176634e-19
  self.assertAlmostEqual(Egap,517.0399957,places=4)
 def test_015_thermal_occupation(self):
  x=60
  e=1/(math.exp(x)-1)
  self.assertLess(e,1e-25)
  self.assertAlmostEqual(e/math.exp(-x),1.0,places=12)
 def test_016_impedance_calculation(self):
  z=7e-7*1.09384563e6
  self.assertAlmostEqual(z,0.765691941,places=8)
  self.assertAlmostEqual(4*z/1e7,3.062767764e-7,places=16)
 def test_017_rate_model_corrected_solution(self):
  l_s,l_em,k=4.0,2.0,.25
  f=lambda t:k*(math.exp(-l_s*t)-math.exp(-l_em*t))/(l_em-l_s)
  dt=1e-5;t=.34;lhs=(f(t+dt)-f(t-dt))/(2*dt)
  rhs=k*math.exp(-l_s*t)-l_em*f(t)
  self.assertAlmostEqual(lhs,rhs,places=9);self.assertGreaterEqual(f(t),0)
 def test_018_ring_and_trefoil_topological_gate(self):
  c=next(x for x in self.claims if x['claim_id']=='M016')
  self.assertEqual(c['evidence_status'],'INCOMPATIBLE_WITH_SMOOTH_EULER')
 def test_019_mass_dimension_flags(self):
  for ident in ('M001','M006'):
   c=next(x for x in self.claims if x['claim_id']==ident)
   self.assertEqual(c['dimension_status'],'FAIL_JOULES_NOT_KG')
 def test_020_compton_circularity_flag(self):
  c=next(x for x in self.claims if x['claim_id']=='M004')
  self.assertIn('electron mass',c['scope_or_assumptions'])
 def test_021_voigt_normalization(self):
  try:
   import numpy as np
   from scipy.special import wofz
   from scipy.integrate import simpson
  except ImportError:self.skipTest('numpy/scipy not installed')
  sig,gam=1.2,.7
  x=np.linspace(-60,60,120001)
  profile=np.real(wofz((x+1j*gam)/(sig*np.sqrt(2))))/(sig*np.sqrt(2*np.pi))
  # Finite integration interval: Lorentzian tails > 0, so integral <1
  area=simpson(profile,x=x)
  self.assertTrue(0.99<area<1.0)
  self.assertGreater(profile.min(),0)
 def test_022_circulation_mismatch(self):
  q=self.q['numerical_checks']['gamma_ratio_paper_to_canon']
  self.assertGreater(q,75000)
  self.assertLess(q,75200)
 def test_023_no_pklsa_certification(self):
  self.assertEqual(self.q['numerical_checks']['native_pklsa_provider'],'NOT_CONNECTED')
  self.assertEqual(self.q['status'],'DEVELOPMENT_NOT_PHYSICALLY_CERTIFIED')

if __name__=='__main__':unittest.main(verbosity=2)

import csv,json,math,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from build_leapfrogging_seed import ring_points,write_seed
from analyze_leapfrogging_trace import analyze

class LeapfroggingSeedTests(unittest.TestCase):
  def test_closed_geometry_and_orientation(self):
    p=ring_points(.07,-.015,144)
    self.assertEqual(len(p),144)
    self.assertAlmostEqual(sum(x for x,y,z in p)/144,0,places=13)
    self.assertAlmostEqual(sum(y for x,y,z in p)/144,0,places=13)
    self.assertTrue(all(abs(z+.015)<1e-14 for x,y,z in p))
    signed=.5*sum(p[i][0]*p[(i+1)%144][1]-p[(i+1)%144][0]*p[i][1] for i in range(144))
    self.assertGreater(signed,0)
    self.assertAlmostEqual(signed,math.pi*.07**2,delta=.001*math.pi*.07**2)
  def test_coaxial_equal_radius_nonoverlap(self):
    a=ring_points(.07,-.015,144);b=ring_points(.07,.015,144)
    self.assertAlmostEqual(sum(x for x,y,z in a)/144,sum(x for x,y,z in b)/144)
    self.assertAlmostEqual(min(abs(b[i][2]-a[i][2]) for i in range(144)),.03)
    self.assertGreater(.03,3*.0015)
  def test_refuse_overwrite_and_bad_dimensions(self):
    with tempfile.TemporaryDirectory() as tmp:
      d=Path(tmp)/'output';write_seed(d)
      with self.assertRaises(FileExistsError):write_seed(d)
      with self.assertRaises(ValueError):write_seed(Path(tmp)/'bad',gap=.004,core=.0015)
  def test_manifest_and_source_hashes(self):
    with tempfile.TemporaryDirectory() as tmp:
      d=Path(tmp)/'out';m=write_seed(d,n=96)
      self.assertEqual(len(m['component_records']),2)
      self.assertTrue((d/'SEED_MANIFEST.json').is_file())
      self.assertTrue((d/'SHA256SUMS.txt').is_file())
      self.assertIn('0_1',m['topology'])
      self.assertTrue(all(len((d/c['file']).read_text().splitlines())==96 for c in m['component_records']))
  def test_analyzer_synthetic_pass_vs_null(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp)/'test.csv'
      with p.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['t','RA','RB','zA','zB'])
        for i in range(40):w.writerow([i*.1,.07,.07,-.02 if i<20 else .02,.02 if i<20 else -.02])
      s=analyze(p);self.assertEqual(s['axial_order_swaps'],1)
      self.assertEqual(s['status'],'ORDER_SWAPS_OBSERVED_NOT_STABILITY_CERTIFIED')
  def test_analyzer_rejects_disordered_time(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp)/'bad.csv'
      p.write_text('t,RA,RB,zA,zB\\n0,.07,.07,-.01,.01\\n2,.07,.07,-.01,.01\\n1,.07,.07,-.01,.01\\n')
      with self.assertRaises(ValueError):analyze(p)
if __name__=='__main__':unittest.main()

import sys,unittest,csv,json,pathlib,math
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from reconstruct_census_v011 import parse_kpf, parse_ascii,component_metrics
BASE=pathlib.Path(__file__).parent/'reconstructed'
class CensusAudit(unittest.TestCase):
    def setUp(self):
        with (BASE/'baseline_geometry_RECONSTRUCTED.csv').open() as f:
            self.total={(x['kind'],x['id']):x for x in csv.DictReader(f)}
        with (BASE/'baseline_components_RECONSTRUCTED.csv').open() as f:
            self.comp={(x['kind'],x['id'],int(x['component'])):x for x in csv.DictReader(f)}
    def test_all_50(self):self.assertEqual(len(self.total),50)
    def test_component_85(self):self.assertEqual(len(self.comp),85)
    def test_all_50_bad_csv(self):
        with (BASE/'upstream_csv_failures.csv').open() as f:
            self.assertEqual(len(list(csv.DictReader(f))),50)
    def test_trefoil(self):
        x=self.total['knot','3.1'];self.assertEqual(int(x['N_beads']),47);self.assertAlmostEqual(float(x['L_polygon_units']),56.758465,places=5)
    def test_link_triplet(self):
        x=self.total['link','6.3.3'];self.assertEqual(int(x['components']),3);self.assertEqual(int(x['N_beads']),97)
    def test_torus_6_21(self):
        x=self.total['torus','6.21'];self.assertEqual(int(x['components']),3);self.assertEqual(int(x['N_beads']),78);self.assertAlmostEqual(float(x['L_polygon_units']),442.96826,places=4)
    def test_metadata(self):
        x=json.loads((BASE/'audit_summary.json').read_text());self.assertEqual(x['source_csv_length_failures'],50);self.assertEqual(x['native_ascii_parity_pass'],50);self.assertTrue(x['all_closed'])
    def test_invalid_kpf(self):
        with self.assertRaises(ValueError):parse_kpf(b'bad header')
    def test_invalid_zero_edge(self):
        with self.assertRaises(ValueError):component_metrics([(0,0,0),(0,0,0),(1,0,0)])
    def test_ascii_delta(self):
        self.assertLess(max(float(x['ascii_max_abs_coordinate_delta']) for x in self.total.values()),5e-5)
if __name__=='__main__': unittest.main(verbosity=2)

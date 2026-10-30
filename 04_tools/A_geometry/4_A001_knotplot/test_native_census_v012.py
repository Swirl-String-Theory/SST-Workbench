import csv
import io
import json
import math
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
import audit_native_census_v012 as census

ROOT=Path(__file__).resolve().parent


class KnotPlotCensusFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=census.Source(archive=ROOT/'falsifier_census_v0.1.0_output.zip')
        cls.native=census.parse_kpf(cls.src.read('raw_native/knot_3.1.kpf'))
    @classmethod
    def tearDownClass(cls):
        cls.src.close()
    def test_closed_loop_length(self):
        m=census.component_metrics(self.native[0]['points'])
        self.assertEqual(m['N_beads'],47)
        self.assertAlmostEqual(m['L_polygon_units'],56.758465014671586,places=6)
    def test_ascii_matches(self):
        a=census.parse_ascii(self.src.read('raw_native/knot_3.1.txt'))
        self.assertEqual(len(a),1)
        self.assertEqual(len(a[0]),47)
        self.assertLess(max(abs(x-y) for p,q in zip(a[0],self.native[0]['points']) for x,y in zip(p,q)),5e-5)
    def test_torus_link_component_split(self):
        c=census.parse_kpf(self.src.read('raw_native/torus_6.21.kpf'))
        self.assertEqual(len(c),3)
        self.assertEqual([len(i['points']) for i in c],[26,26,26])
    def test_short_segment_guard(self):
        with self.assertRaises(ValueError):
            census.component_metrics([(0,0,0),(1,0,0),(1,0,0)])
    def test_missing_end_guard(self):
        b=self.src.read('raw_native/knot_3.1.kpf')
        with self.assertRaises(ValueError):
            census.parse_kpf(b[:b.rfind(b'endf')])
    def test_invalid_position_guard(self):
        with self.assertRaises(ValueError):
            census.component_metrics([(0,0,0),(1,0,0),(math.nan,0,0)])
    def test_audit_length_not_from_bad_csv(self):
        with tempfile.TemporaryDirectory() as td:
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                status=census.audit(self.src,Path(td))
            self.assertEqual(status,0)
            with open(Path(td)/'baseline_geometry_v012.csv',newline='',encoding='utf-8') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),50)
            x=next(r for r in rows if r['kind']=='knot' and r['id']=='3.1')
            self.assertGreater(float(x['L_total_polygon_units']),50)
            self.assertEqual(x['legacy_csv_status'],'LEGACY_LENGTH_INVALID')
            summary=json.loads((Path(td)/'AUDIT_SUMMARY.json').read_text())
            self.assertEqual(summary['objects_parsed'],50)
            self.assertEqual(summary['components_parsed'],85)
            self.assertEqual(summary['legacy_zero_or_bad_csv_count'],50)
            self.assertEqual(summary['KnotPlot_catalogue_identity'],'UNVERIFIED')
            self.assertNotIn('SHA256SUMS.txt',(Path(td)/'SHA256SUMS.txt').read_text())
    def test_new_scripts_do_not_mutate(self):
        scripts=ROOT/'Build_Knot_Link_Torus_KnotPlot_Scripts'/'falsifier_census_v0.1.2'/'scripts'
        ls=list(scripts.glob('census_*.kpc'))
        self.assertEqual(len(ls),50)
        for p in ls:
            commands=[ln.lower().strip() for ln in p.read_text().splitlines() if ln.strip() and not ln.startswith('%')]
            self.assertEqual(commands[0],'reset all')
            self.assertTrue(commands[1].startswith('load ') or commands[1].startswith('torus '))
            self.assertFalse(any(ln.startswith(('data ', 'data', 'scale ', 'fitto ', 'refine ', 'ago ', 'go ', 'centre ', 'split ', 'nbeads ')) for ln in commands))
            self.assertEqual(sum(ln.startswith('save ') for ln in commands),2)
    def test_tarball_crc(self):
        self.assertIsNone(self.src.archive.testzip())
    def test_scale_invariance_on_polygon(self):
        pts=self.native[0]['points']
        orig=census.component_metrics(pts)
        scaled=census.component_metrics([tuple(3*v for v in p) for p in pts])
        self.assertEqual(orig['N_beads'],scaled['N_beads'])
        self.assertAlmostEqual(scaled['L_polygon_units']/orig['L_polygon_units'],3.0)
        self.assertAlmostEqual(scaled['ds_max_over_min'],orig['ds_max_over_min'])

if __name__=='__main__':unittest.main()

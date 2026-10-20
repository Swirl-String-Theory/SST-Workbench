import json, unittest, sys, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import build,legacy_build as l

class TestGeometries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r={t:json.loads((ROOT/f'candidate_report_{t}.json').read_text()) for t in ('SMOKE','BASIC')}
    def test_sources_unchanged(self):
        for k in ('5_2','6_1'):
            path=ROOT/'source_native'/f'{k}__knotplot_final.txt'
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),self.r['BASIC']['source_sha256'][k])
    def test_components(self):
        for t,d in self.r.items():
            self.assertEqual(len(d['N_points_per_component']),3)
            self.assertTrue(all(n>100 for n in d['N_points_per_component']))
    def test_smoke_smaller_than_basic(self):
        self.assertLess(sum(self.r['SMOKE']['N_points_per_component']),sum(self.r['BASIC']['N_points_per_component']))
    def test_pairwise_gauss_near_zero(self):
        for t,d in self.r.items():self.assertTrue(all(abs(x)<.03 for x in d['pairwise_gauss_linking_integrals']))
    def test_cross_clearance(self):
        for t,d in self.r.items():self.assertGreater(min(d['minimum_cross_segment_clearances'].values()),.12)
    def test_self_clearance(self):
        for t,d in self.r.items():self.assertGreater(min(d['minimum_nonlocal_self_clearances'].values()),.01)
    def test_binary_roundtrip_and_hash(self):
        for t,d in self.r.items():
            b=(ROOT/'geometry'/f'borromean_5_2_5_2_6_1_{t}.kpt').read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),d['geometries_sha256'])
            self.assertEqual([len(x) for x in l.decode_kpt(b)],d['N_points_per_component'])
    def test_no_go_in_load_only(self):
        for t in self.r:
            content=(ROOT/f'borromean_{t}_load_only.kpc').read_text()
            self.assertFalse(any(x.strip().startswith('go ') for x in content.splitlines()))
    def test_go_in_diagnostics(self):
        d=ROOT/'diagnostic'
        for name in ('00_solver_trefoil_smoke.kpc','01_borromean_SMOKE_go1.kpc','02_borromean_BASIC_go1.kpc'):
            self.assertIn('go 1',(d/name).read_text())
if __name__=='__main__':unittest.main()

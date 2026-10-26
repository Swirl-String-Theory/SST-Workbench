from __future__ import annotations
import json
import math
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from build_ruban_family import sample_ruban, validate_torus, geometric_diagnostics, build, read_active_baseline, ruban_inspired_perturbation


class TestRuban(unittest.TestCase):
    def test_periodicity_and_normalized_major_radius(self):
        for p,q in [(2,3),(3,2),(2,5),(3,4),(4,3),(5,4)]:
            v=sample_ruban(p,q,0.14,512)
            self.assertEqual(v.shape,(512,3))
            self.assertTrue(np.isfinite(v).all())
            radial=np.sqrt(v[:,0]**2+v[:,1]**2)
            self.assertTrue(np.all(radial>0))
            self.assertAlmostEqual(float(np.max(np.abs(radial-1))),0.14,delta=0.0005)

    def test_analytic_closure_at_2pi(self):
        for p,q in [(2,3),(3,2),(4,3),(5,2)]:
            b=0.17; beta=2*math.pi
            r=(1+b*math.sin(q*beta))
            endpoint=np.array([r*math.cos(p*beta),r*math.sin(p*beta),b*math.cos(q*beta)])
            np.testing.assert_allclose(endpoint,sample_ruban(p,q,b,256)[0],rtol=0,atol=1e-13)

    def test_perturbed_child_is_distinct_and_not_an_independent_provider(self):
        a=sample_ruban(3,2,.14,512)
        ap=ruban_inspired_perturbation(a,3,2)
        self.assertFalse(np.allclose(a,ap))
        self.assertTrue(np.isfinite(ap).all())
        self.assertGreater(float(np.max(np.abs(ap[:,2]-a[:,2]))),0)

    def test_invalid_non_knot(self):
        for pq in [(2,4),(1,3),(3,3),(0,3)]:
            with self.assertRaises(ValueError):sample_ruban(*pq,.15,256)
        for b in [-0.1,0,1,2]:
            with self.assertRaises(ValueError):sample_ruban(2,3,b,256)

    def test_distinct_trefoil_embeddings_and_single_independence(self):
        a=sample_ruban(2,3,.15,512)
        b=sample_ruban(3,2,.15,512)
        self.assertFalse(np.allclose(a,b))
        cfg=json.loads((HERE/'configs/ruban_family.json').read_text())
        f=[r for r in cfg['families'] if r['topology_id']=='3_1']
        self.assertEqual(len(f),2)
        self.assertEqual(cfg['source_independence_group'],'ruban_analytic_parametrization_2018')

    def test_no_fake_geometry_stability_claims(self):
        d=geometric_diagnostics(sample_ruban(2,3,.15,256))
        self.assertIsNone(d['ropelength_diameter'])
        self.assertIsNone(d['ruban_lifetime'])
        self.assertFalse(d['qualified_for_active_atlas'])

    def test_readonly_42_topology_baseline_and_no_overwrite(self):
        cfg=json.loads((HERE/'configs/ruban_family.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            baseline=root/'base.zip'
            topo={'count':42,'topologies':['3_1']+[f'topo_{j}' for j in range(41)]}
            with zipfile.ZipFile(baseline,'w') as z:z.writestr('v034/ACTIVE_TOPOLOGY_SET.json',json.dumps(topo))
            previous=baseline.read_bytes()
            out=root/'newoutputs'
            summary=build(cfg,out,'pilot',baseline)
            self.assertEqual(summary['shape_count'],len(cfg['families'])*len(cfg['pilot_B0']))
            self.assertEqual(previous,baseline.read_bytes())
            self.assertTrue((out/'FAMILY_INDEX.json').is_file())
            idx=json.loads((out/'FAMILY_INDEX.json').read_text())
            self.assertEqual(idx['independent_source_count'],1)
            self.assertEqual(idx['perturbed_child_count'],len(idx['seeds']))
            self.assertTrue(all((out/i['perturbed_xyz_path']).is_file() for i in idx['seeds']))
            self.assertTrue(any(i['topology_id']=='3_1' and i['is_member_of_active_v034'] for i in idx['seeds']))
            self.assertTrue(any(i['topology_id'] is None and i['is_member_of_active_v034'] is False for i in idx['seeds']))
            self.assertTrue(all(i['status']=='RESEARCH_SEED_NOT_PASSED_PKLSA_ADMISSION_OR_DYNAMICS' for i in idx['seeds']))
            with self.assertRaises(FileExistsError):build(cfg,out,'pilot',baseline)

    def test_fine_grid_is_not_a_claimed_stability_window(self):
        from build_ruban_family import select_b0
        cfg=json.loads((HERE/'configs/ruban_family.json').read_text())
        vals=select_b0(cfg,'fine')
        self.assertAlmostEqual(vals[0],0.08)
        self.assertAlmostEqual(vals[-1],0.22)
        self.assertLessEqual(max(np.diff(vals)),.002500001)
        self.assertEqual(cfg['dynamics_run'],'NOT_EXECUTED')
        self.assertIn('NOT digitized'.lower(),cfg['scan_note'].lower())

if __name__=='__main__':unittest.main()

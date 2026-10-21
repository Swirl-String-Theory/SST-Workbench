"""v0.2.5: immutable v0.2.4 F3 regression + fail-closed projection diagnostics.

The actual pyKnotid run on the user's Windows environment is preserved as
an excerpt fixture. A deterministic provider stub simulates those observations;
tests of the stub are NOT evidence that pyKnotid has been repaired.
"""
from __future__ import annotations
import hashlib,json,sys,unittest
from pathlib import Path

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fourier_atlas_adapter as adapter
import g5_extended as g5

ROOT=Path(__file__).resolve().parents[1]
ATLAS=adapter.DEFAULT_ATLAS_ROOT
GOLDEN=json.loads((ROOT/'tests'/'fixtures'/'g5_v024_f3_f4_golden.json').read_text())


class TestHistoricalRegression(unittest.TestCase):
    def test_golden_is_exact_v024_failure(self):
        self.assertEqual(GOLDEN['source_report_adapter_version'],'0.2.4')
        self.assertEqual(GOLDEN['source_report_g5_status'],'FAIL_INVARIANT_SCREEN')
        f3=next(x for x in GOLDEN['seed_results'] if x['id']=='fibonacci_torus_F3')
        bad=[x for x in f3['observations'] if x['N']==2400 and x['projection']==1]
        self.assertEqual(len(bad),2)
        self.assertEqual({tuple(x['alexander_coefficients']) for x in bad},{(1,)})
        self.assertEqual({x['vassiliev_3'] for x in bad},{0})
    def test_v024_failure_never_promoted(self):
        f3=next(x for x in GOLDEN['seed_results'] if x['id']=='fibonacci_torus_F3')
        r=g5.summarize_invariant_observations(f3['observations'],f3['expected_polynomial_coefficients'])
        self.assertEqual(r['G5a_polynomial'],'MISMATCH')
        self.assertEqual(r['G5b_mirror_odd'],'UNRESOLVED_ZERO_V3_WITNESS')
        self.assertEqual(r['G5d_projection_resolution'],'FAIL')
        self.assertEqual(r['status'],'INVARIANT_MISMATCH')
        self.assertEqual(r['zero_v3_witness_count'],1)
        self.assertIn({'N':2400,'projection':1,'kind':'ALEXANDER_MISMATCH',
                       'observed_polynomial':[1],'expected_polynomial':[1,-1,1]},r['primary_case_issues'])
    def test_v024_f4_control_still_good(self):
        f4=next(x for x in GOLDEN['seed_results'] if x['id']=='fibonacci_torus_F4')
        r=g5.summarize_invariant_observations(f4['observations'],f4['expected_polynomial_coefficients'])
        self.assertEqual(r['G5a_polynomial'],'MATCH')
        self.assertEqual(r['G5b_mirror_odd'],'PASS_NONZERO_MIRROR_ODD_DIAGNOSTIC_ONLY')
        self.assertEqual(r['G5d_projection_resolution'],'PASS')
        self.assertEqual(r['status'],'MULTI_INVARIANT_MATCH_NOT_CERTIFIED')
    def test_stably_zero_v3_not_chirality_witness(self):
        obs=[{'N':n,'projection':i,'mirror':mir,'alexander_coefficients':[1,-1,1],
              'vassiliev_3':0} for n in (1200,2400) for i in (0,1) for mir in (False,True)]
        r=g5.summarize_invariant_observations(obs,[1,-1,1])
        self.assertEqual(r['status'],'ZERO_V3_UNRESOLVED')
        self.assertEqual(r['G5d_projection_resolution'],'FAIL')
        self.assertEqual(r['G5b_mirror_odd'],'UNRESOLVED_ZERO_V3_WITNESS')
        self.assertEqual(r['chirality_evidence'],'UNRESOLVED')
    def test_predeclared_primary_not_modified(self):
        self.assertEqual(g5.PROJECTION_ANGLES[:2],((.37,.71),(.63,1.17)))
        self.assertEqual(g5.DIAGNOSTIC_PROJECTIONS,(2,3))
        self.assertFalse('CERTIFIED' in g5.summarize_invariant_observations(
            next(x for x in GOLDEN['seed_results'] if x['id']=='fibonacci_torus_F3')['observations'],
            [1,-1,1])['status'])


@unittest.skipUnless(ATLAS.is_file() or (ATLAS/'manifest.json').is_file(),'Atlas unavailable')
class TestActualGeometry(unittest.TestCase):
    def test_f3_primary_crossing_count_geometrically_converges(self):
        root=ATLAS/'xyz'
        results=[]
        for n in (1200,2400):
            p=np.loadtxt(root/f'fibonacci_torus_F3_uniform_t_N{n}.xyz')
            pair=[]
            for idx in (0,1):
                r=g5.projected_crossing_diagnostics(p@g5.rotation_for_projection(idx).T)
                self.assertEqual(r['geometry_status'],'GENERIC_BY_HEURISTIC')
                self.assertGreater(r['min_abs_depth_separation_over_diameter'],1e-5)
                pair.append(r['crossing_count'])
            results.append(pair)
        self.assertEqual(results,[[3,4],[3,4]])
    def test_mock_extra_projections_cannot_rescue_known_failure(self):
        manifest,_=adapter.load_manifest(ATLAS)
        records=[r for r in manifest['records'] if r['id']=='fibonacci_torus_F3'
                 and r['sampling']=='uniform_t' and r['points'] in (1200,2400)]
        keys={}
        def signature(a):return hashlib.sha256(np.ascontiguousarray(np.round(a[:12],11)).tobytes()).hexdigest()
        for n in (1200,2400):
            p=np.loadtxt(ATLAS/'xyz'/f'fibonacci_torus_F3_uniform_t_N{n}.xyz')
            for idx in range(4):
                orig=p@g5.rotation_for_projection(idx).T
                for mirror,coords in ((False,orig),(True,orig*np.array([-1.,1.,1.]))):
                    keys[signature(coords)]=(n,idx,mirror)
        def stub(p):
            n,idx,mirror=keys[signature(p)]
            if n==2400 and idx==1:
                return {'alexander_coefficients':[1],'vassiliev_3':0}
            return {'alexander_coefficients':[1,-1,1],'vassiliev_3':1 if mirror else -1}
        report={'gate_results':{}}
        r=g5.extended_g5_screen({'records':records},report,ATLAS,enabled=True,
                               geometry_provider=stub,projection_diagnostics=True)
        self.assertEqual(r['status'],'FAIL_INVARIANT_SCREEN')
        self.assertEqual(r['subgates']['G5b'],'PARTIAL_UNRESOLVED')
        self.assertEqual(r['subgates']['G5d'],'PARTIAL_UNRESOLVED')
        self.assertEqual(report['gate_results']['G5_EXTENDED'],'FAIL_INVARIANT_SCREEN')
        row=r['seed_results'][0]
        self.assertEqual(row['G5b_mirror_odd'],'UNRESOLVED_ZERO_V3_WITNESS')
        self.assertEqual(row['G5d_projection_resolution'],'FAIL')
        diag=row['projection_robustness_diagnostics']
        self.assertEqual(len(diag['baseline_crossings']),4)
        self.assertEqual(diag['supplementary']['case_count'],2)
        self.assertTrue(diag['decision_uses_primary_projections_only'])
        self.assertFalse(diag['supplementary']['promotion_to_primary_evidence'])
        self.assertEqual(diag['supplementary']['cases'][0]['original']['alexander_coefficients'],[1,-1,1])
        self.assertIn('INVARIANT_DISAGREEMENT',diag['interpretation'])
        self.assertFalse(r['independent_topology_certified'])


if __name__=='__main__':unittest.main()

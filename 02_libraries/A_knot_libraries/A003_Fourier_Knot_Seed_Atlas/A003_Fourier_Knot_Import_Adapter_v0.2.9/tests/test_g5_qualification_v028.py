from __future__ import annotations
import json, pathlib, sys, tempfile, unittest, os
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from g5_qualification_v028 import (fixture_read, obs_map, compare_reference,
    validate_observations, check_four_level_symmetry, expected_keys,
    run_campaign, TARGET_SEEDS, RESOLUTIONS)
from g5_extended import extended_g5_screen
from fourier_atlas_adapter import validate_atlas

class TestG5QualificationV028(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hist,cls.ref=fixture_read()

    def expanded(self):
        rows={}
        for sid in TARGET_SEEDS:
            for n in RESOLUTIONS:
                for proj in (0,1):
                    for mirror in (False,True):
                        baseline=self.ref[(sid,2400 if n in (4800,9600) else n,proj,mirror)]
                        rows[(sid,n,proj,mirror)]={**baseline,'N':n}
        return rows

    def test_fixture_complete_and_source_trace(self):
        self.assertEqual(len(self.ref),16)
        self.assertEqual(len(self.hist['source_v027_output_archive_sha256']),64)
        self.assertEqual(set(self.ref),expected_keys((1200,2400)))

    def test_new_high_res_have_16_cases(self):
        m=self.expanded()
        self.assertEqual(len(m),32)
        self.assertEqual(compare_reference(m,self.ref,(4800,9600))['matched'],16)
        self.assertEqual(compare_reference(m,self.ref,(1200,2400))['matched'],16)

    def test_high_res_single_mismatch_is_fail(self):
        m=self.expanded()
        m[('fibonacci_torus_F3',9600,1,False)]['alexander_coefficients']=[1]
        got=compare_reference(m,self.ref,(4800,9600))
        self.assertEqual(got['status'],'FAIL')
        self.assertEqual(got['matched'],15)

    def test_missing_one_case_unresolved(self):
        m=self.expanded();m.pop(('fibonacci_torus_F4',4800,0,True))
        self.assertEqual(compare_reference(m,self.ref,(4800,9600))['status'],'UNRESOLVED')

    def test_duplicate_cases_raise(self):
        x=list(self.expanded().values())
        with self.assertRaisesRegex(ValueError,'duplicate'):
            obs_map(x+[dict(x[0])])

    def test_four_level_mirror_and_polynomial(self):
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').exists():self.skipTest('full atlas missing')
        registry,_=validate_atlas(atlas)
        res=check_four_level_symmetry(self.expanded(),registry)
        self.assertEqual(res['status'],'PASS')
        self.assertEqual(len(res['checks']),16)

    def test_mirror_violation_fail(self):
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').exists():self.skipTest('full atlas missing')
        reg,_=validate_atlas(atlas)
        m=self.expanded()
        m[('fibonacci_torus_F4',9600,0,True)]['vassiliev_3']=-1
        self.assertEqual(check_four_level_symmetry(m,reg)['status'],'FAIL')

    def test_all_32_corrected_provider_double_still_not_certified(self):
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').exists():self.skipTest('full atlas missing')
        registry,report=validate_atlas(atlas)
        selected={'records':[r for r in registry['records'] if r['id'] in TARGET_SEEDS]}
        call=iter(self.expanded().values()) # arranged insertion seed then n then proj then mirror
        def fake(_coords):
            o=next(call)
            return {'alexander_coefficients':o['alexander_coefficients'],'vassiliev_3':o['vassiliev_3']}
        ext=extended_g5_screen(selected,report,atlas,enabled=True,
            resolutions=RESOLUTIONS,max_crossings=12,geometry_provider=fake,
            projection_diagnostics=False)
        self.assertEqual(ext['checked_polygon_projection_cases'],32)
        self.assertEqual(ext['successful_multi_invariant_seeds'],2)
        self.assertEqual(ext['status'],'MULTI_INVARIANT_SCREEN_ONLY_NOT_CERTIFIED')
        self.assertEqual(ext['provider'],'test-double')
        self.assertEqual(validate_observations(ext)['status'],'UNRESOLVED')
        self.assertEqual(compare_reference(obs_map([dict(o,id=r['id']) for r in ext['seed_results'] for o in r['observations']]),self.ref,(4800,9600))['status'],'PASS')

    def test_framework_continues_unresolved_without_provider(self):
        fw=os.environ.get('SST_FRAMEWORK_ROOT')
        atlas=ROOT.parent/'A003-v0.1.2'
        if not fw or not (atlas/'manifest.json').exists():self.skipTest('requires pinned framework and atlas')
        with tempfile.TemporaryDirectory() as d:
            rc,folder,summ=run_campaign(atlas=atlas,framework=pathlib.Path(fw),
                 out_root=pathlib.Path(d),run_provider=False)
            ledger=json.loads((folder/'GATE_LEDGER.json').read_text())
            rows={x['gate_id']:x for x in ledger['records']}
            self.assertEqual(rc,3)
            self.assertEqual(rows['G5Q1']['status'],'UNRESOLVED')
            self.assertEqual(rows['G5Q5']['status'],'PASS')
            self.assertEqual(rows['G5Q6']['status'],'PASS')
            self.assertEqual(rows['G5Q7']['status'],'UNRESOLVED')
            self.assertEqual(rows['G5Q7']['qualification'],'DIAGNOSTIC_ONLY')
            self.assertEqual(len(json.loads((folder/'g5q_independent_diagram_summary.json').read_text())['cases']),16)
            self.assertEqual(len(json.loads((folder/'g5q_provider_diagram_comparison.json').read_text())['cases']),32)
            self.assertEqual(rows['G6']['execution_status'],'NOT_EXECUTED')
            self.assertFalse(summ['knot_topology_certified'])
            self.assertTrue((folder/'G5_QUALIFICATION_REPORT.tex').is_file())

if __name__=='__main__':unittest.main()

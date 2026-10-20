from __future__ import annotations
import json, pathlib, sys, tempfile, unittest
from unittest.mock import patch
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from crossing_trace import crossing_trace, bareiss_det
from a003_diagnostic_v027 import run_diagnostic, status_extended
from g5_extended import rotation_for_projection

class TestCrossingTrace(unittest.TestCase):
    def test_integer_bareiss(self):
        self.assertEqual(bareiss_det([[2,3],[1,4]]),5)
        self.assertEqual(bareiss_det([]),1)
    def test_f3_all_frozen_cases(self):
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').is_file():self.skipTest('full atlas not installed')
        for n in (1200,2400):
            pts=np.loadtxt(atlas/f'xyz/fibonacci_torus_F3_uniform_t_N{n}.xyz')
            for proj,expected_crossings in ((0,3),(1,4)):
                with self.subTest(n=n,proj=proj):
                    t=crossing_trace(pts@rotation_for_projection(proj).T)
                    self.assertEqual(t['crossing_count'],expected_crossings)
                    self.assertEqual(t['diagram_determinant']['value'],3)
                    self.assertEqual(t['nearly_degenerate_crossings'],0)
    def test_f4_cases(self):
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').is_file():self.skipTest('full atlas not installed')
        for n in (1200,2400):
            pts=np.loadtxt(atlas/f'xyz/fibonacci_torus_F4_uniform_t_N{n}.xyz')
            for proj in (0,1):
                with self.subTest(n=n,proj=proj):
                    self.assertEqual(crossing_trace(pts@rotation_for_projection(proj).T)['diagram_determinant']['value'],1)
    def test_no_ambiguous_crossing_false_evidence(self):
        c=[{'over':'ambiguous'}]
        from crossing_trace import wirtinger_determinant
        self.assertIsNone(wirtinger_determinant(c,[])['value'])
    def test_fail_to_pass_not_promoted(self):
        ext={'status':'FAIL_INVARIANT_SCREEN','subgates':{'G5a':'PARTIAL_UNRESOLVED'},
             'seed_results':[{'G5a_polynomial':'MISMATCH','G5d_projection_resolution':'FAIL'}]}
        self.assertEqual(status_extended('G5a',ext)[0],'FAIL')
        self.assertEqual(status_extended('G5d',ext)[0],'FAIL')

class TestFrameworkRealSource(unittest.TestCase):
    def test_authentic_framework_110_continues(self):
        # Users may supply actual frozen source during Windows integration test.
        root=pathlib.Path(__file__).resolve().parents[1]
        fw_env=__import__('os').environ.get('SST_FRAMEWORK_ROOT')
        if not fw_env:self.skipTest('SST_FRAMEWORK_ROOT not set; external integration test only')
        from a003_diagnostic_v027 import load_framework,gate_definitions
        fw,meta,mod,sha=load_framework(pathlib.Path(fw_env))
        ledger=mod.GateLedger(gate_definitions(mod),strict_dependencies=False)
        calls=[]
        e={'G0':lambda:{'status':'PASS'}, 'G5a':lambda:{'status':'FAIL'},
           'G5e':lambda:(calls.append('G5e') or {'status':'PASS'})}
        ledger.run_evaluators(e)
        rows={r['gate_id']:r for r in ledger.to_dict()['records']}
        self.assertEqual(rows['G5a']['status'],'FAIL')
        self.assertEqual(rows['G5e']['status'],'PASS')
        self.assertEqual(rows['G5e']['qualification'],'DIAGNOSTIC_ONLY')
        self.assertFalse(rows['G5e']['allows_dependent_claim'])
        self.assertIn('G5e',calls)

    def test_archived_f3_failure_continues_all_diagnostics(self):
        env=__import__('os').environ
        if not env.get('SST_FRAMEWORK_ROOT'):self.skipTest('framework source unavailable')
        atlas=ROOT.parent/'A003-v0.1.2'
        if not (atlas/'manifest.json').is_file():self.skipTest('full atlas unavailable')
        # v0.2.5 archived actual provider output: test reproduces A003 failure,
        # while crossing extraction runs independently under genuine GateLedger.
        historic=pathlib.Path('/mnt/data/a003_v025_results_inspection/outputs_g5_projection_robustness/validation_report.json')
        if not historic.is_file():self.skipTest('historical golden not locally mounted')
        ext=json.loads(historic.read_text())['extended_g5_screen']
        with tempfile.TemporaryDirectory() as td:
            rc,rundir,summary=run_diagnostic(atlas=atlas,root=pathlib.Path(env['SST_FRAMEWORK_ROOT']),
                                             out_root=pathlib.Path(td),run_provider=True,replay_extended=ext)
            ledger=json.loads((rundir/'GATE_LEDGER.json').read_text())
            d={r['gate_id']:r for r in ledger['records']}
            self.assertEqual(rc,2)
            self.assertEqual(d['G5a']['status'],'FAIL')
            self.assertEqual(d['G5e']['status'],'PASS')
            self.assertEqual(d['G5e']['qualification'],'DIAGNOSTIC_ONLY')
            self.assertEqual(d['G5f']['status'],'FAIL')
            self.assertTrue(summary['diagnostics_continued_after_fail'])
            diff=json.loads((rundir/'g5f_provider_diagram_comparison.json').read_text())
            p=[r for r in diff['comparisons'] if r['id']=='fibonacci_torus_F3' and r['N']==2400 and r['projection']==1][0]
            self.assertEqual(p['provider_determinant'],1)
            self.assertEqual(p['diagram_determinant'],3)
            self.assertEqual(p['status'],'MISMATCH')

if __name__=='__main__':unittest.main()

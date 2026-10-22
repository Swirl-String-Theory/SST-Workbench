from __future__ import annotations
import json, pathlib, sys, tempfile, unittest
from contextlib import nullcontext
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from a003_diagnostic_v027 import run_diagnostic

class TestPairedFailureContinuation(unittest.TestCase):
    def test_synthetic_stock_failure_and_corrected_success_not_certified(self):
        import os
        fw=os.environ.get('SST_FRAMEWORK_ROOT')
        atlas=ROOT.parent/'A003-v0.1.2'
        if not fw or not (atlas/'manifest.json').exists():
            self.skipTest('local test requires pinned v1.0.10 fixture and complete atlas')
        historic=json.loads((ROOT/'tests/fixtures/g5_v025_extended_replay.json').read_text())['extended_g5_screen']
        stock=json.loads(json.dumps(historic))
        corrected=json.loads(json.dumps(stock))
        for row in corrected['seed_results']:
            if row['id']=='fibonacci_torus_F3':
                for obs in row['observations']:
                    if obs['N']==2400 and obs['projection']==1:
                        obs['alexander_coefficients']=[1,-1,1]
                        obs['vassiliev_3'] = 1 if obs['mirror'] else -1
                row['status']='MULTI_INVARIANT_MATCH_NOT_CERTIFIED'
                row['G5a_polynomial']='MATCH'
                row['G5b_mirror_odd']='PASS_NONZERO_MIRROR_ODD_DIAGNOSTIC_ONLY'
                row['G5d_projection_resolution']='PASS'
        corrected['status']='PARTIAL_UNRESOLVED'
        corrected['subgates']['G5a']='PASS_SCREEN_NOT_CERTIFIED'
        corrected['subgates']['G5b']='PASS_MIRROR_DIAGNOSTIC_ONLY'
        corrected['subgates']['G5d']='PASS_TESTED_CASES_ONLY'
        calls=[]
        def fake_extended(*args,**kwargs):
            calls.append('stock_or_corrected')
            return stock if len(calls)==1 else corrected
        with tempfile.TemporaryDirectory() as tmp:
            with (patch('a003_diagnostic_v027.extended_g5_screen',side_effect=fake_extended),
                  patch('a003_diagnostic_v027.scoped_pyknotid_python_backend',return_value=nullcontext({'backend':'PYTHON_HELPERS_0.5.3_UNMODIFIED'})),
                  patch('a003_diagnostic_v027.scoped_pyknotid_crossing_fix',return_value=nullcontext({'patch':'SIMULATED_NO_REAL_PROVIDER'}))):
                rc,run_dir,summary=run_diagnostic(atlas=atlas,root=pathlib.Path(fw),out_root=pathlib.Path(tmp))
            rows={r['gate_id']:r for r in json.loads((run_dir/'GATE_LEDGER.json').read_text())['records']}
            self.assertEqual(rc,2)
            self.assertEqual(len(calls),2)
            self.assertEqual(rows['G5a']['status'],'FAIL')
            self.assertEqual(rows['G5g']['status'],'PASS')
            self.assertEqual(rows['G5h']['status'],'PASS')
            self.assertEqual(rows['G5g']['qualification'],'DIAGNOSTIC_ONLY')
            self.assertEqual(rows['G5h']['qualification'],'DIAGNOSTIC_ONLY')
            self.assertFalse(rows['G5h']['allows_dependent_claim'])
            self.assertTrue(summary['diagnostics_continued_after_fail'])
            self.assertEqual(json.loads((run_dir/'g5i_numeric_guard_evidence.json').read_text())['gate_pass'],True)

if __name__=='__main__':unittest.main()

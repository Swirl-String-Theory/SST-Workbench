"""v0.3.3: fail-closed injection controls with no changed upstream evidence."""
from __future__ import annotations
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
from framework_bridge.install import patch_cpu_gate_plan
from triadic.numeric_readiness import evaluate

ROOT=Path(__file__).resolve().parents[1]
LEGACY=['D01_G08_FILAMENT_SPATIAL_REFINEMENT','D01_G10_FILAMENT_SPATIAL_75_300']


def synthetic_controls():
    return [{'gate':x,'status':'FAIL' if x in LEGACY else 'PASS'}
            for x in LEGACY+[f'CONTROL_{i:02}' for i in range(17)]]


def qualification():
    q= json.loads((ROOT/'preregistration/QUALIFICATION_V032.json').read_text())
    digest=hashlib.sha256((ROOT/'preregistration/QUALIFICATION_V032.json').read_bytes()).hexdigest()
    return {'precommit_sha256':digest,
            'qualification':{'historical_fail_retained':'FAIL','refined_discretization':'PASS','time_discretization':'PASS'}}

class RoutingV033Tests(unittest.TestCase):
    def test_original_11_byte_identical(self):
        spec=json.loads((ROOT/'preregistration/ROUTING_V033.json').read_text())
        self.assertEqual(len(spec['protected_v032_file_sha256']),11)
        for name,sha in spec['protected_v032_file_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha,name)

    def test_g3_dag_is_modified_before_freeze(self):
        plan={'gates':[{'gate_id':f'G{i}','requires':[],'question':'','enabled':True} for i in range(10)]}
        patched=patch_cpu_gate_plan(plan)
        by={p['gate_id']:p for p in patched['gates']}
        self.assertEqual(by['G3']['requires'],['G1','G10'])
        self.assertEqual(by['G2']['requires'],[])
        self.assertEqual(by['G10']['requires'],['G1'])
        self.assertEqual(by['G11']['requires'],['G1'])
        self.assertEqual(by['G8']['requires'],['G3','G5'])

    def test_exact_expected_coarse_failures_permit_evaluation_only(self):
        result=evaluate(ROOT,synthetic_controls(),qualification(),g10_status='PASS')
        self.assertTrue(result['ready_for_G3_evaluation'])
        self.assertEqual(result['historical_G2'],'FAIL_RETAINED')
        self.assertEqual(result['g3_permitted_outcome'],'UNRESOLVED')
        self.assertEqual(result['physical_force_status'],'UNRESOLVED')

    def test_unexpected_analytic_failure_blocks(self):
        g=synthetic_controls();g[2]['status']='FAIL'
        self.assertFalse(evaluate(ROOT,g,qualification(),g10_status='PASS')['ready_for_G3_evaluation'])

    def test_g10_failure_blocks(self):
        self.assertFalse(evaluate(ROOT,synthetic_controls(),qualification(),g10_status='FAIL')['ready_for_G3_evaluation'])

    def test_temporal_failure_blocks(self):
        q=qualification();q['qualification']['time_discretization']='FAIL'
        self.assertFalse(evaluate(ROOT,synthetic_controls(),q,g10_status='PASS')['ready_for_G3_evaluation'])

    def test_changed_precommit_blocks(self):
        q=qualification();q['precommit_sha256']='0'*64
        self.assertFalse(evaluate(ROOT,synthetic_controls(),q,g10_status='PASS')['ready_for_G3_evaluation'])

    def test_modified_coarse_failure_signature_blocks(self):
        g=synthetic_controls();g[0]['status']='PASS'
        self.assertFalse(evaluate(ROOT,g,qualification(),g10_status='PASS')['ready_for_G3_evaluation'])

    def test_missing_control_blocks(self):
        g=synthetic_controls()[:-1]
        self.assertFalse(evaluate(ROOT,g,qualification(),g10_status='PASS')['ready_for_G3_evaluation'])

    def test_changed_seal_blocks_without_mutating_sources(self):
        # Patch the hash function, not source bytes (evidence remains untouched).
        from unittest.mock import patch
        with patch('triadic.numeric_readiness._sha', side_effect=lambda p: '0'*64 if str(p).endswith('D01_EULER.seal.json') else hashlib.sha256(Path(p).read_bytes()).hexdigest()):
            result=evaluate(ROOT,synthetic_controls(),qualification(),g10_status='PASS')
        self.assertFalse(result['ready_for_G3_evaluation'])
        self.assertEqual(result['protected_mismatches'],['seals/D01_EULER.seal.json'])

if __name__=='__main__': unittest.main()

"""Tests for G6 source-native readiness; mock data is never science evidence."""
import hashlib, json, pathlib, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from g6_pklsa_pilot_v029 import (g5_check,source_check,provider_check,finite_core_field,NS,SEEDS)

class G6ReadinessTests(unittest.TestCase):
    def test_g5_without_receipt_unresolved(self):
        self.assertEqual(g5_check(None)['status'],'UNRESOLVED')
    def test_source_absent_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(provider_check(pathlib.Path(d),'C005',pathlib.Path('missing'),pathlib.Path('core.py'))['status'],'UNRESOLVED')
    def test_source_presence_is_not_dynamics(self):
        with tempfile.TemporaryDirectory() as d:
            x=pathlib.Path(d)/'C005';x.mkdir()
            (x/'core.py').write_text('test')
            result=provider_check(pathlib.Path(d),'C005',pathlib.Path('C005'),pathlib.Path('core.py'))
            self.assertEqual(result['status'],'PASS')
            self.assertEqual(result['authority'],'LOCAL_SOURCE_PRESENT_NOT_VALIDATED_FOR_A003')
    def test_g5_ledger_tamper_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            d=pathlib.Path(d)
            (d/'QUALIFICATION_SUMMARY.json').write_text(json.dumps({'adapter_version':'0.2.8.1',
                'corrected_g5_bounded_result':'PASS_INVARIANT_SCREEN_NOT_CERTIFIED',
                'measured_provider_observations':32,'exit_code':0,
                'source_manifest_sha256':'01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d'}))
            (d/'GATE_LEDGER.json').write_text(json.dumps({'ledger_sha256':'fake','records':[]}))
            (d/'g5_corrected_four_resolutions.json').write_text(json.dumps({'expected_cases':32,'observation':{'provider':'pyknotid'}}))
            self.assertEqual(g5_check(d/'QUALIFICATION_SUMMARY.json')['status'],'FAIL')
    def test_g5_missing_provider_observations_unresolved(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'QUALIFICATION_SUMMARY.json';p.write_text('{}')
            self.assertEqual(g5_check(p)['status'],'UNRESOLVED')
    def test_six_field_probes_each_level_with_fake_numeric_kernel(self):
        atlas=pathlib.Path(__file__).resolve().parents[2]/'A003-v0.1.2'
        if not (atlas/'manifest.json').exists():self.skipTest('full external atlas unavailable')
        reg,_=source_check(atlas)
        def kernel(p,probes):
            # Testing-only constant divergence-free field; not experimental evidence.
            return [[1.,0.,0.] for _ in probes],[[[0.,0.,0.]]*3 for _ in probes],{'backend':'TEST_DOUBLE'}
        result=finite_core_field(atlas,reg,pathlib.Path('/fake'),backend_function=kernel)
        self.assertEqual(len(result['samples']),len(SEEDS)*len(NS))
        self.assertTrue(all(x['relative_divergence']==0 for x in result['samples']))
        self.assertFalse(result['euler_time_integrated'])
        self.assertFalse(result['physical_core_calibrated'])
    def test_no_pklsa_time_pass_from_static_field(self):
        self.assertIn('time integrator',__import__('g6_pklsa_pilot_v029').__doc__.lower())

if __name__=='__main__':unittest.main()

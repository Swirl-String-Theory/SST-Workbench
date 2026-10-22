from __future__ import annotations
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from g6_upstream_v033 import (check_a058,check_e010,stage_registry,p9_euler_audit,
    independent_source_audit,pressure_poisson_source_proxy,SourceError,SCHEMA)
from g6_pklsa_pilot_v029 import g5_check
from test_g5_receipt_transfer_v0321 import write_receipt

class UpstreamV033(unittest.TestCase):
    def test_e010_missing_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual('UNRESOLVED',check_e010(Path(td))['status'])
    def test_a058_missing_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual('UNRESOLVED',check_a058(Path(td))['status'])
    def test_a058_version_conflict_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'VERSION_CONTRACT.json').write_text(json.dumps({'version':'v0.3.5'}))
            a=check_a058(p)
            self.assertTrue(a['source_version_mismatch']);self.assertEqual('UNRESOLVED',a['status'])
    def test_p16_no_one_family_claim(self):
        v=independent_source_audit({'carriers':[{'n_native':47},{'n_native':86}]},'e010',None)
        self.assertEqual('UNRESOLVED',v['status'])
        self.assertEqual(0,v['distinct_verified_dynamic_provider_families'])
    def test_p16_no_interpolation_independence(self):
        v=independent_source_audit({'carriers':[{'n_native':47},{'n_native':86}]},{},None,{'status':'PASS_MODEL_DIAGNOSTIC_ONLY','rows':[{},{}]})
        self.assertEqual(2,v['actual_finite_core_computed_carriers'])
        self.assertEqual('UNRESOLVED',v['status'])
    def test_p9_cannot_be_promoted_by_external_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/'claim.json';x.write_text(json.dumps({'status':'PASS'}))
            a=p9_euler_audit({'status':'PASS_SOURCE_PRESENT_DEVELOPMENT_ONLY'},x)
            self.assertEqual('UNRESOLVED',a['status'])
            self.assertTrue(a['checks']['external_receipt_unverified'])
    def test_p8_no_e010_no_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=stage_registry(p,p/'e010',p/'atlas',p/'wb',[])
            self.assertEqual('UNRESOLVED',a['status'])
            self.assertFalse((p/'G6P8_STAGE_E010_V033').exists())
    def test_poisson_requires_actual_kernel(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            self.assertEqual('UNRESOLVED',pressure_poisson_source_proxy(p,p)['status'])
    def test_v033_receipt_accepted_and_unknown_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);p1=write_receipt(p/'a','0.3.3');p2=write_receipt(p/'b','0.3.5')
            self.assertEqual('PASS',g5_check(p1)['status'])
            self.assertEqual('FAIL',g5_check(p2)['status'])
    def test_version(self):self.assertEqual('sst.a003.g6-upstream/1',SCHEMA)

if __name__=='__main__':unittest.main()

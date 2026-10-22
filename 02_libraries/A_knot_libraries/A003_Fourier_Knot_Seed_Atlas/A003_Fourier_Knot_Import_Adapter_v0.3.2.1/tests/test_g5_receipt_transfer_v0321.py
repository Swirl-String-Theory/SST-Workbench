"""Synthetic software-regression controls for a v0.3.2 receipt transfer bug.

These synthetic receipts are intentionally NOT scientific evidence.  The actual
2026-10-21 Windows G5 receipt is verified separately during release preparation.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from g6_pklsa_pilot_v029 import g5_check, find_g5_summary, EXPECTED_MANIFEST


REQUIRED = ('G0','G1','G5Q0','G5Q1','G5Q2','G5Q3','G5Q4','G5Q5','G5Q6','G5Q7')


def write_receipt(directory, version='0.3.2'):
    p=Path(directory);p.mkdir(parents=True,exist_ok=True)
    s={'adapter_version':version,
       'corrected_g5_bounded_result':'PASS_INVARIANT_SCREEN_NOT_CERTIFIED',
       'measured_provider_observations':32,
       'source_manifest_sha256':EXPECTED_MANIFEST,
       'exit_code':0,'failed_gates':[],
       'run_id':'SYNTHETIC_UNIT_TEST_ONLY',
       'baseline_historical_stock_fail_preserved':True}
    ledger={'schema':'synthetic-test-ledger/1',
            'records':[{'gate_id':k,'status':'PASS'} for k in REQUIRED]}
    set_ledger_hash(ledger)
    (p/'QUALIFICATION_SUMMARY.json').write_text(json.dumps(s),encoding='utf8')
    (p/'GATE_LEDGER.json').write_text(json.dumps(ledger),encoding='utf8')
    (p/'g5_corrected_four_resolutions.json').write_text(json.dumps({
       'schema':'SYNTHETIC_UNIT_TEST_ONLY',
       'expected_cases':32,'observation':{'provider':'pyknotid'}}),encoding='utf8')
    return p/'QUALIFICATION_SUMMARY.json'


def set_ledger_hash(d):
    plain={k:v for k,v in d.items() if k!='ledger_sha256'}
    d['ledger_sha256']=hashlib.sha256((json.dumps(plain,sort_keys=True,
       separators=(',',':'),ensure_ascii=False)+'\n').encode('utf8')).hexdigest()


class TestReceiptVersionHandoff(unittest.TestCase):
    def test_v032_receipt_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual('PASS',g5_check(write_receipt(tmp, '0.3.2'))['status'])

    def test_v0321_receipt_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual('PASS',g5_check(write_receipt(tmp, '0.3.2.1'))['status'])

    def test_previous_v031_receipt_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual('PASS',g5_check(write_receipt(tmp, '0.3.1'))['status'])

    def test_unregistered_future_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual('FAIL',g5_check(write_receipt(tmp, '0.3.3'))['status'])

    def test_changed_ledger_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=write_receipt(tmp);q=p.parent/'GATE_LEDGER.json'
            d=json.loads(q.read_text());d['records'][0]['status']='FAIL';q.write_text(json.dumps(d))
            self.assertEqual('FAIL',g5_check(p)['status'])

    def test_rehashed_scientific_failure_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=write_receipt(tmp);q=p.parent/'GATE_LEDGER.json'
            d=json.loads(q.read_text());d['records'][4]['status']='FAIL';set_ledger_hash(d);q.write_text(json.dumps(d))
            self.assertEqual('FAIL',g5_check(p)['status'])

    def test_wrong_provider_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=write_receipt(tmp);q=p.parent/'g5_corrected_four_resolutions.json'
            d=json.loads(q.read_text());d['observation']['provider']='mock';q.write_text(json.dumps(d))
            self.assertEqual('FAIL',g5_check(p)['status'])

    def test_missing_raw_observations_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=write_receipt(tmp);(p.parent/'g5_corrected_four_resolutions.json').unlink()
            self.assertEqual('UNRESOLVED',g5_check(p)['status'])

    def test_bounded_failed_result_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=write_receipt(tmp);d=json.loads(p.read_text())
            d['corrected_g5_bounded_result']='FAIL_INVARIANT_SCREEN';p.write_text(json.dumps(d))
            self.assertEqual('FAIL',g5_check(p)['status'])

    def test_latest_new_directory_discovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp);atlas=parent/'A003-v0.1.2';atlas.mkdir()
            old=parent/'A003_Fourier_Knot_Import_Adapter_v0.3.1-outputs'/'old'
            new=parent/'A003_Fourier_Knot_Import_Adapter_v0.3.2.1-outputs'/'new'
            a=write_receipt(old,'0.3.1');b=write_receipt(new,'0.3.2.1')
            os.utime(a, (1000000000,1000000000))
            os.utime(b, (1100000000,1100000000))
            self.assertEqual(b,find_g5_summary(atlas,None,None))


if __name__=='__main__': unittest.main()

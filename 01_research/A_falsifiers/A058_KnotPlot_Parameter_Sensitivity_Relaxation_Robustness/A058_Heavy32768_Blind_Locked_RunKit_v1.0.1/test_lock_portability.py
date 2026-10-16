"""Standalone deterministic checks for detached A058 selection lock (stdlib only)."""
from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path

from locked_heavy import verify_native_selection, hash_file

HERE=Path(__file__).resolve().parent


class TestSelectionLockPortability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected=json.loads((HERE/'SELECTION_ENGINE_EXPECTED.json').read_text(encoding='utf-8'))
        cls.lock=json.loads((HERE/'HEAVY_SELECTION_LOCK.json').read_text(encoding='utf-8'))

    def test_original_commitment_unchanged(self):
        lock_sha=(HERE/'HEAVY_SELECTION_LOCK.sha256').read_text(encoding='ascii').split()[0]
        self.assertEqual(hash_file(HERE/'HEAVY_SELECTION_LOCK.json'), lock_sha)
        self.assertEqual(lock_sha, '11c0bb20703a8bcc7c0565620a485131a6feb36d649f21516c84f6b59be37137')
        self.assertEqual(hash_file(HERE/'SELECTION_ENGINE_EXPECTED.json'),self.lock['selection_detail_hash_sha256'])
        self.assertEqual(self.expected['selected_ids'], self.lock['selected_ids'])

    def test_exact_json(self):
        verify_native_selection(copy.deepcopy(self.expected), self.expected)

    def test_windows_path_separator(self):
        actual=copy.deepcopy(self.expected)
        actual['selection_from']=actual['selection_from'].replace('/','\\')
        verify_native_selection(actual,self.expected)

    def test_score_numeric_roundoff(self):
        actual=copy.deepcopy(self.expected)
        for row in actual['selection_details']:
            for key in ('source_score','source_shape_distance','source_scalar_rel'):
                if key in row:
                    row[key]+=2e-13
        verify_native_selection(actual,self.expected)

    def test_selection_id_mutation_rejected(self):
        actual=copy.deepcopy(self.expected)
        actual['selected_ids'][7]='C0999'
        with self.assertRaisesRegex(RuntimeError,'selected_ids'):
            verify_native_selection(actual,self.expected)

    def test_reason_mutation_rejected(self):
        actual=copy.deepcopy(self.expected)
        actual['selection_details'][8]['reason']='post hoc selection'
        with self.assertRaisesRegex(RuntimeError,'reason'):
            verify_native_selection(actual,self.expected)

    def test_large_numeric_drift_rejected(self):
        actual=copy.deepcopy(self.expected)
        target=next(row for row in actual['selection_details'] if 'source_score' in row)
        target['source_score']+=1e-5
        with self.assertRaisesRegex(RuntimeError,'score drift'):
            verify_native_selection(actual,self.expected)

    def test_source_hash_mutation_rejected(self):
        actual=copy.deepcopy(self.expected)
        actual['source_runlog_sha256']='0'*64
        with self.assertRaisesRegex(RuntimeError,'source_runlog_sha256'):
            verify_native_selection(actual,self.expected)

    def test_selected_detail_id_mutation_rejected(self):
        actual=copy.deepcopy(self.expected)
        actual['selection_details'][1]['condition_id']='C0999'
        with self.assertRaisesRegex(RuntimeError,'condition_id'):
            verify_native_selection(actual,self.expected)

    def test_invalid_source_path_rejected(self):
        actual=copy.deepcopy(self.expected)
        actual['selection_from']='campaign/runs/BASIC'
        with self.assertRaisesRegex(RuntimeError,'selection source mismatch'):
            verify_native_selection(actual,self.expected)


if __name__=='__main__':unittest.main(verbosity=2)

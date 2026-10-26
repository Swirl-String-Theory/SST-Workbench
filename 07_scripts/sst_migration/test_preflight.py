import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).with_name('preflight.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QueueTests(unittest.TestCase):
    def test_exclusive_lock_rejects_overlap(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            with module.locked(state):
                with self.assertRaises(FileExistsError):
                    with module.locked(state):
                        self.fail('overlapping lease')
            self.assertFalse((state / 'queue.lock').exists())

    def test_manifest_path_cannot_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                module.checked_child(Path(folder), '../outside')

    def test_one_item_no_scientific_promotion_or_source_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            family = root / 'family'
            family.mkdir()
            (family / 'A011-v0.3.1').mkdir()
            (family / 'A011-v0.3.1/raw.txt').write_text('immutable')
            state = root / 'state'
            state.mkdir()
            jobs = [{'id': id, 'family_path': 'family', 'pilot': True, 'status': 'PENDING_PREFLIGHT',
                     'source_version': 'A011-v0.3.1', 'proposed_version': id + '-v0.4.0'} for id in ['A011', 'A054', 'A065']]
            module.atomic(state / 'queue.json', {'jobs': jobs, 'pilot_validated': False, 'scheduling_enabled': False})
            module.atomic(state / 'inventory.json', {'registry_hashes': {'x': 'before'}})
            inv = {'registry_hashes': {'x': 'after'}, 'families': [{'path': 'family', 'issues': [], 'version_metadata': {}}]}
            audit = {'framework': {'status': 'BLOCKED_SOURCE_INTEGRITY'}, 'pklsa': {'source_hash_status': 'FAIL'}}
            with patch.object(module, 'inventory', return_value=inv), patch.object(module, 'audit', return_value=audit):
                result = module.next_item(root, state)
            queue = module.read(state / 'queue.json')
            self.assertEqual(result['id'], 'A011')
            self.assertEqual([j['status'] for j in queue['jobs']], ['BLOCKED_PREFLIGHT', 'PENDING_PREFLIGHT', 'PENDING_PREFLIGHT'])
            first = queue['jobs'][0]
            self.assertEqual(first['scientific_gate'], 'NOT_RUN')
            self.assertIn('REGISTRY_CHANGED_AFTER_INITIALIZATION', first['blockers'])
            self.assertIn('PKLSA_SOURCE_HASH_MISMATCH', first['blockers'])
            self.assertIn('FRAMEWORK_MANIFEST_MISMATCH', first['blockers'])
            self.assertFalse(queue['scheduling_enabled'])
            self.assertFalse((family / 'A011-v0.4.0').exists())
            self.assertEqual((family / 'A011-v0.3.1/raw.txt').read_text(), 'immutable')


if __name__ == '__main__':
    unittest.main()

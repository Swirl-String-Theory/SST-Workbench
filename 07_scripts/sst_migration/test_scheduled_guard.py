from pathlib import Path
import tempfile
import unittest

from scheduled_guard import acquire, release


class ScheduledGuardTests(unittest.TestCase):
    def test_second_run_cannot_claim_an_active_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            first = acquire(state)
            with self.assertRaises(FileExistsError):
                acquire(state)
            self.assertEqual(release(state, first['token'])['released'], True)
            self.assertFalse((state / 'run.lock').exists())

    def test_wrong_owner_cannot_remove_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            first = acquire(state)
            with self.assertRaises(PermissionError):
                release(state, 'wrong-token')
            self.assertTrue((state / 'run.lock').exists())
            release(state, first['token'])

    def test_unreadable_or_interrupted_lock_is_not_reclaimed(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            (state / 'run.lock').write_text('interrupted')
            with self.assertRaises(FileExistsError):
                acquire(state)
            self.assertEqual((state / 'run.lock').read_text(), 'interrupted')


if __name__ == '__main__':
    unittest.main()

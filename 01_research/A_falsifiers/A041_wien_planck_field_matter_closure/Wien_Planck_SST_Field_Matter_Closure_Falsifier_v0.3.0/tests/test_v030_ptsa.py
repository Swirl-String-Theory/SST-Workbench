from pathlib import Path
import json
import unittest
import numpy as np

from sst_wp.geometry import discover, load_geometry
from sst_wp.modal import dominant_frequency
from sst_wp.action_reveal import _ptsa_parameter_index


class TestV030PTSA(unittest.TestCase):
    def test_ptsa_48_self_contained(self):
        root = Path(__file__).resolve().parents[1] / 'datasets' / 'SST_Parametric_Trefoil_Seed_Atlas_v1.0.0'
        files = discover(root / 'candidates')
        self.assertEqual(len(files), 48)
        pub = json.loads((root / 'ATLAS_PUBLIC_MANIFEST.json').read_text())
        self.assertEqual(pub['candidate_count'], 48)
        self.assertEqual(len(pub['candidates']), 48)
        self.assertTrue(all(len(load_geometry(f)) == 1 for f in files[:3]))

    def test_reveal_parameter_index_has_48_candidates(self):
        idx = _ptsa_parameter_index()
        self.assertEqual(len(idx), 48)
        self.assertTrue(all(name.startswith("PTSA_") and name.endswith(".xyz") for name in idx))

    def test_first_fft_bin_is_window_limited(self):
        t = np.linspace(0, 1, 128)
        a = np.sin(2 * np.pi * 1.0 * t)
        q = dominant_frequency(t, a, 0)
        self.assertLessEqual(q['fft_bin_index'], 1)
        self.assertIs(q['frequency_window_limited'], True)


if __name__ == '__main__':
    unittest.main()

import unittest, math
import numpy as np
from pathlib import Path
from sst_wp.geometry import normalize_components, spacing_metrics
from sst_wp.kernels import velocity_python, energy_sum_python
from sst_wp.energy import dimensionless_line_energy
from sst_wp.reveal_normalization import dimensional_action_scale
from sst_wp.provenance import audit
from sst_wp.blind_guard import scan_blind_source, scan_blind_payload_leak

class TestCore(unittest.TestCase):
    def setUp(self):
        t = np.linspace(0, 2*np.pi, 40, endpoint=False)
        c = np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])
        self.p, self.o = normalize_components([c], 48)

    def test_geometry(self):
        self.assertLess(spacing_metrics(self.p, self.o)["ds_cv"], 0.002)

    def test_velocity_finite(self):
        self.assertTrue(np.isfinite(velocity_python(self.p, self.o, 1, .05)).all())

    def test_energy_finite(self):
        self.assertTrue(math.isfinite(energy_sum_python(self.p, self.o, .05)))
        ehat, _ = dimensionless_line_energy(self.p, self.o, .05)
        self.assertTrue(math.isfinite(ehat))

    def test_provenance_echo(self):
        self.assertLess(abs(audit()["numeric"]["ratio"] - 1), 2e-6)
        self.assertLess(abs(audit()["legacy_reveal_normalization"]["ratio_to_hbar"] - 1), 2e-6)

    def test_blind_source_has_no_canonical_constants(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(scan_blind_source(root), [])

    def test_payload_guard_rejects_SI_action_columns(self):
        bad = scan_blind_payload_leak({"columns":["delta_E_J","frequency_Hz"]})
        self.assertTrue(bad)

    def test_dimensionless_action_scale_formula(self):
        self.assertAlmostEqual(dimensional_action_scale(2,3,4), 384.0)

if __name__ == "__main__":
    unittest.main()

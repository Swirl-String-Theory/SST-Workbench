import unittest
from unittest.mock import patch
import numpy as np

from sst_wp.geometry import normalize_components
from sst_wp.perturb import tangent_field, project_mode_to_normal
from sst_wp.relative_equilibrium import fit_relative_equilibrium
from sst_wp.campaign import certify_frequency_horizon
from sst_wp.dynamics import evolve


class TestV031Certification(unittest.TestCase):
    def setUp(self):
        t = np.linspace(0, 2*np.pi, 48, endpoint=False)
        c = np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])
        self.X, self.offs = normalize_components([c], 48)

    def test_mode_projection_removes_tangential_gauge(self):
        t = tangent_field(self.X, self.offs)
        radial = self.X / np.maximum(np.linalg.norm(self.X, axis=1)[:, None], 1e-15)
        mixed = (3.0 * t + 0.5 * radial).reshape(-1)
        mode, diag = project_mode_to_normal(self.X, self.offs, mixed)
        M = mode.reshape(self.X.shape)
        self.assertLess(np.max(np.abs(np.sum(M * t, axis=1))), 1e-10)
        self.assertAlmostEqual(np.sqrt(np.mean(np.sum(M*M, axis=1))), 1.0, places=10)
        self.assertGreater(diag['mode_normal_fraction'], 0.0)
        self.assertLess(diag['mode_normal_fraction'], 1.0)

    def test_normal_relative_equilibrium_ignores_tangential_marker_speed(self):
        t = tangent_field(self.X, self.offs)
        U = np.array([0.1, -0.2, 0.3])
        Om = np.array([0.0, 0.0, 1.7])
        rigid = U[None, :] + np.cross(np.broadcast_to(Om, self.X.shape), self.X)
        phase = np.linspace(0, 2*np.pi, len(self.X), endpoint=False)
        synthetic_v = rigid + (4.0 + 2.0*np.sin(3*phase))[:, None] * t
        with patch('sst_wp.relative_equilibrium.velocity', return_value=synthetic_v):
            q = fit_relative_equilibrium(self.X, self.offs, 1.0, 0.05, False)
        self.assertLess(q['epsilon_RE_perp'], 1e-10)
        self.assertGreater(q['epsilon_RE_full'], 0.1)
        self.assertEqual(q['epsilon_RE'], q['epsilon_RE_perp'])

    def test_frequency_certification_is_iterative(self):
        calls = {'n': 0}
        def fake_pair(*args, **kwargs):
            calls['n'] += 1
            if calls['n'] < 3:
                fq = {
                    'frequency': 1.0,
                    'omega': 2*np.pi,
                    'spectral_power': 0.9,
                    'cycles': 1.0,
                    'period_cv': float('inf'),
                    'harmonic_r2': 0.9,
                    'fft_bin_index': 1,
                    'frequency_window_limited': True,
                    'fft_bin_width': 1.0,
                }
            else:
                fq = {
                    'frequency': 4.0,
                    'omega': 8*np.pi,
                    'spectral_power': 0.9,
                    'cycles': 7.0,
                    'period_cv': 0.02,
                    'harmonic_r2': 0.95,
                    'fft_bin_index': 4,
                    'frequency_window_limited': False,
                    'fft_bin_width': 0.5,
                }
            d = {'mesh_cv_max_observed': 0.02}
            return fq, d, d
        cfg = {
            't_final': 0.1,
            'samples': 64,
            'max_frequency_samples': 512,
            'max_frequency_horizon_factor': 16.0,
            'max_frequency_extension_rounds': 5,
            'frequency_horizon_growth': 2.0,
            'target_frequency_cycles': 6.0,
            'gates': {'min_cycles': 4.0},
        }
        with patch('sst_wp.campaign._run_matched_pair', side_effect=fake_pair):
            fq, _, _ = certify_frequency_horizon(
                self.X, self.offs, np.ones(self.X.size), 0.002, cfg, auto=True
            )
        self.assertEqual(calls['n'], 3)
        self.assertEqual(fq['frequency_certification_status'], 'RESOLVED')
        self.assertEqual(fq['frequency_extension_rounds'], 2)
        self.assertGreater(fq['effective_t_final'], cfg['t_final'])

    def test_adaptive_reparameterization_activates_on_bad_mesh(self):
        # Nonuniform parameter spacing on a circle, deliberately a marker-gauge defect.
        u = np.linspace(0, 1, 48, endpoint=False) ** 1.7
        a = 2*np.pi*u
        X = np.column_stack([np.cos(a), np.sin(a), np.zeros_like(a)])
        # Normalize only global length/centroid; preserve nonuniform marker spacing.
        X = X - X.mean(0)
        L = np.sum(np.linalg.norm(np.roll(X, -1, axis=0)-X, axis=1))
        X = X / L
        offs = np.array([0, len(X)], dtype=np.int64)
        cfg = {
            'gamma_dimensionless': 1.0,
            'core_fraction': 0.08,
            't_final': 0.002,
            'stability_cfl': 0.15,
            'require_native': False,
            'max_substeps': 5000,
            'dynamic_max_substeps': True,
            'max_substeps_safety_factor': 8.0,
            'max_substeps_absolute': 20000,
            'reparameterization_events': 0,
            'adaptive_reparameterization': True,
            'adaptive_reparam_cv_trigger': 0.03,
            'adaptive_reparam_edge_ratio_trigger': 1.5,
            'adaptive_reparam_check_every': 1,
        }
        _, _, d = evolve(X, offs, cfg, sample_count=20)
        self.assertGreater(d['adaptive_reparameterizations'], 0)
        self.assertLess(d['final_mesh']['ds_cv'], 0.03)


if __name__ == '__main__':
    unittest.main()

"""Separate control tests; physical clock claims are intentionally excluded."""
from __future__ import annotations
import math, tempfile, zipfile, json, hashlib, shutil,unittest
from pathlib import Path
from experiment.hill import hill_suite,hill_field,differential_metrics
from experiment.gp import gp_suite,solve_gp,profile_at
from experiment.ring import ring_suite,check_case
from experiment.pklsa import scan,PIN,ARCHIVE_NAME

ROOT=Path(__file__).resolve().parents[1]
class NewControls(unittest.TestCase):
    def test_hill_field(self):self.assertEqual(hill_suite()['status'],'PASS')
    def test_hill_gamma(self):
        r=hill_suite();self.assertAlmostEqual(r['Gamma_meridional']/(5*r['radius']),r['U'],places=11)
    def test_hill_interior(self):self.assertLess(differential_metrics((.3,.2,.1))['steady_euler_residual'],3e-8)
    def test_hill_exterior(self):self.assertLess(differential_metrics((2.,.2,.3))['curl_absolute_error'],3e-8)
    def test_hill_no_clock(self):self.assertFalse(hill_suite()['self_clock_predicted'])
    def test_gp(self):self.assertEqual(gp_suite()['status'],'PASS')
    def test_gp_no_clock(self):self.assertFalse(gp_suite()['global_phase_is_observable_clock'])
    def test_gp_core_to_bulk(self):
        s=solve_gp(105)
        self.assertGreater(float(profile_at(s,[4])[0]),.95)
        self.assertLess(float(profile_at(s,[.2])[0]),.2)
    def test_gp_winding(self):self.assertAlmostEqual(gp_suite()['circulation'],2*math.pi)
    def test_ring(self):self.assertEqual(ring_suite()['status'],'PASS')
    def test_ring_two_core_laws(self):
        for name in ('fixed_core','constant_core_volume'):
           self.assertLess(check_case(1.615,name)['relative_error'],3e-8)
    def test_ring_no_fat_core(self):self.assertTrue(ring_suite()['fat_core_R_over_a_0_898_is_excluded'])
    def test_pklsa_real_atlas(self):
        d=scan(ROOT/'sources'/ARCHIVE_NAME)
        self.assertEqual(d['status'],'PASS_STATIC_MANIFEST_ONLY')
        self.assertEqual(d['eligible_provider_groups'],['gilbert'])
        self.assertFalse(d['qualified_dynamics'])
        self.assertFalse(d['independent_physics_providers_met'])
    def test_pklsa_legacy_never_eligible(self):
        d=scan(ROOT/'sources'/ARCHIVE_NAME,allow_historical=True)
        self.assertEqual(d['eligible_provider_groups'],['gilbert'])
        self.assertTrue(any(x['provider_group']=='knotplot' for x in d['excluded_anchors']))
    def test_pklsa_bad_sha_fail_closed(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'atlas.zip';f.write_bytes(b'not a trustworthy static source')
            self.assertEqual(scan(f)['status'],'FAIL_INTEGRITY_SHA256')
    def test_pklsa_missing(self):
        self.assertEqual(scan(ROOT/'nonexistent.zip')['status'],'UNRESOLVED_MISSING_ATLAS')
    def test_pklsa_alternative_topology(self):
        x=scan(ROOT/'sources'/ARCHIVE_NAME,'5_1')
        self.assertEqual(x['eligible_provider_groups'],['gilbert'])
        self.assertFalse(x['qualified_dynamics'])
    def test_static_not_dynamic(self):
        x=scan(ROOT/'sources'/ARCHIVE_NAME)
        self.assertFalse(x['physical_clock_supported'])
        self.assertFalse(x['real_3d_trajectory_loaded'])
        self.assertFalse(x['upstream_source_bytes_verified'])
if __name__=='__main__':unittest.main()

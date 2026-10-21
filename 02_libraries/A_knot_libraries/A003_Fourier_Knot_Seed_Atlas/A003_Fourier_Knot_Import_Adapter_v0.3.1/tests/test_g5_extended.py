"""Deterministic extended G5 regressions; provider stand-ins are not science evidence."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import sympy as sp
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fourier_atlas_adapter as adapter
import g5_extended as g5

ATLAS=adapter.DEFAULT_ATLAS_ROOT


def seed_registry(seed):
    manifest,_=adapter.load_manifest(ATLAS)
    return {'records':[r.copy() for r in manifest['records'] if r['id']==seed and
             r['sampling']=='uniform_t' and r['points'] in (1200,2400)]}


def fake_provider(points):
    # Handedness fixture from three independent chords of parametrized trefoil.
    n=len(points)
    i,j,k=[int(f*n) for f in (.01,.03,.08)]
    triple=np.linalg.det(points[[i,j,k]]-points[0])
    if abs(triple)<1e-10:raise RuntimeError('degenerate fake diagnostic')
    return {'alexander_coefficients':[1,-1,1],
            'vassiliev_3':1 if triple>0 else -1}


class TestSymbolicReference(unittest.TestCase):
    def test_torus_polynomial_exact(self):
        self.assertEqual(g5.torus_polynomial_coefficients(2,3),[1,-1,1])
        self.assertEqual(g5.torus_polynomial_coefficients(3,4),[1,-1,0,1,0,-1,1])
        self.assertEqual(len(g5.torus_polynomial_coefficients(21,34)),661)
        self.assertEqual(g5.torus_polynomial_coefficients(13,21)[0],1)
    def test_twist_polynomial_ref(self):
        for m in range(1,10):
            poly=g5.known_polynomial_reference({'family':'twist','m':m})
            self.assertEqual(sum(poly),1)
            self.assertEqual(abs(sum(c*(-1)**i for i,c in enumerate(poly))),2*m+1)
    def test_unknown_fibonacci_not_classified(self):
        self.assertIsNone(g5.known_polynomial_reference({'family':'fibonacci_fourier','fibonacci_index':8}))
        self.assertIsNone(g5.expected_crossings({'family':'fibonacci_fourier','fibonacci_index':8}))
    def test_modular_burau_independent_algorithm(self):
        for p,q in ((2,3),(3,4),(3,5),(5,8),(8,13),(13,21),(21,34)):
            self.assertEqual(g5.analytic_braid_screen({'family':'torus','p':p,'q':q})['status'],
                             'PASS_BRAID_REFERENCE_ONLY')
    def test_laurent_normalization(self):
        t=sp.symbols('t')
        self.assertEqual(g5.normalized_alexander(2/t-3/t**2+2/t**3),[2,-3,2])
        self.assertEqual(g5.normalized_alexander(1-3*t+t**2),[-1,3,-1])
        self.assertEqual(g5.normalized_alexander(-t*(1-t+t*t)),[1,-1,1])
        with self.assertRaises(g5.QualificationError):
            g5.normalized_alexander(t*t+1)


@unittest.skipUnless(ATLAS.is_dir(),'Atlas unavailable')
class TestExtendedG5(unittest.TestCase):
    def test_bounded_multiresolution_mirror(self):
        registry=seed_registry('fibonacci_torus_F3')
        report={'gate_results':{'G5_INDEPENDENT_TOPOLOGY':'NOT_RUN'}}
        r=g5.extended_g5_screen(registry, report,ATLAS,enabled=True,
                                geometry_provider=fake_provider)
        self.assertEqual(r['status'],'MULTI_INVARIANT_SCREEN_ONLY_NOT_CERTIFIED')
        self.assertEqual(r['checked_polygon_projection_cases'],8)
        self.assertEqual(r['seed_results'][0]['G5d_projection_resolution'],'PASS')
        self.assertEqual(r['seed_results'][0]['G5a_polynomial'],'MATCH')
        self.assertEqual(r['seed_results'][0]['G5b_mirror_odd'],'PASS_NONZERO_MIRROR_ODD_DIAGNOSTIC_ONLY')
        self.assertEqual(r['subgates']['G5c'],'PASS_REFERENCE_ONLY')
        self.assertFalse(r['independent_topology_certified'])
        self.assertFalse(r['chirality_certified'])
    def test_wrong_polynomial_is_failure(self):
        registry=seed_registry('fibonacci_torus_F3')
        def wrong(pts):
            ret=fake_provider(pts)
            ret['alexander_coefficients']=[-1,3,-1]
            return ret
        report={'gate_results':{}}
        r=g5.extended_g5_screen(registry,report,ATLAS,enabled=True,geometry_provider=wrong)
        self.assertEqual(r['status'],'FAIL_INVARIANT_SCREEN')
    def test_v3_mirror_mismatch_is_failure(self):
        registry=seed_registry('fibonacci_torus_F3')
        def wrong(pts):return {'alexander_coefficients':[1,-1,1],'vassiliev_3':1}
        r=g5.extended_g5_screen(registry,{'gate_results':{}},ATLAS,enabled=True,geometry_provider=wrong)
        self.assertEqual(r['status'],'FAIL_INVARIANT_SCREEN')
    def test_high_crossing_skipped_not_falsified(self):
        registry=seed_registry('fibonacci_torus_F8')
        r=g5.extended_g5_screen(registry,{'gate_results':{}},ATLAS,enabled=True,geometry_provider=fake_provider)
        self.assertEqual(r['status'],'PARTIAL_UNRESOLVED')
        self.assertEqual(r['complexity_skipped_seeds'],1)
        self.assertEqual(r['checked_polygon_projection_cases'],0)
        self.assertEqual(r['subgates']['G5c'],'PASS_REFERENCE_ONLY')
    def test_missing_provider_is_not_certification(self):
        registry=seed_registry('fibonacci_torus_F3')
        with patch.dict(sys.modules,{'pyknotid':None,'pyknotid.spacecurves':None}):
            r=g5.extended_g5_screen(registry,{'gate_results':{}},ATLAS,enabled=True)
        self.assertEqual(r['status'],'PROVIDER_UNAVAILABLE')
    def test_integrity_error_blocks_before_provider(self):
        registry=seed_registry('fibonacci_torus_F3')
        registry['records'][0]['sha256']='0'*64
        with self.assertRaisesRegex(g5.QualificationError,'hash mismatch'):
            g5.extended_g5_screen(registry,{'gate_results':{}},ATLAS,enabled=True,
                                  geometry_provider=fake_provider)


class TestV024Packaging(unittest.TestCase):
    def test_cli_exposes_bounded_extended_gate(self):
        root=Path(__file__).resolve().parents[1]
        text=(root/'fourier_atlas_adapter.py').read_text(encoding='utf-8')
        for name in ('--g5-extended','--g5-extended-max-crossings','--require-g5-extended-complete'):
            self.assertIn(name,text)
        self.assertIn("ADAPTER_VERSION = '0.3.1'",text)
    def test_windows_cmd_targets_new_atlas_without_overwrite(self):
        root=Path(__file__).resolve().parents[1]
        for name in ('run_g5_extended_fibonacci_torus.cmd','run_g5_extended_twist.cmd',
                     'run_g5c_braid_reference.cmd'):
            cmd=(root/name).read_text(encoding='utf-8')
            self.assertIn('A003-v0.1.2',cmd)
            self.assertIn('exit /b %errorlevel%',cmd)
    def test_g5c_no_false_certification(self):
        # Packaging contract: outputs_g5c_braid_reference/ is a runtime output,
        # not an input fixture. Compute it afresh using the unmodified production
        # script and a temporary path; leave the source release untouched.
        import contextlib, io, json, tempfile
        from g5c_braid_reference import main as run_g5c_reference
        atlas = Path(__file__).resolve().parents[2]/'A003-v0.1.2'
        if not (atlas / 'manifest.json').is_file():
            self.skipTest('A003-v0.1.2 atlas unavailable')
        with tempfile.TemporaryDirectory(prefix='a003_g5c_regression_') as tmp:
            output = Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                rc = run_g5c_reference(['--atlas', str(atlas), '--out', str(output)])
            self.assertEqual(rc, 0)
            j=json.loads((output/'g5c_braid_reference.json').read_text(encoding='utf-8'))
        self.assertEqual(j['checked_analytic_torus_seeds'],30)
        self.assertEqual(j['validated_source_xyz_count'],384)
        self.assertFalse(j['knot_topology_certified'])
        self.assertFalse(j['chirality_certified'])
        self.assertFalse(j['pklsa_euler_run'])
        self.assertFalse(j['source_byte_changes'])
        self.assertEqual(j['status'],'PASS_BRAID_REFERENCE_ONLY')

if __name__=='__main__':unittest.main()

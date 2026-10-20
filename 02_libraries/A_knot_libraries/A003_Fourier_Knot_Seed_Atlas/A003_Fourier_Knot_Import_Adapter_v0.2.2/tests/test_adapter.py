import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fourier_atlas_adapter as a
import gates_g4_g5 as gates

ATLAS_ENV=os.environ.get('SST_ATLAS_ROOT')
PARENT=Path(__file__).resolve().parents[2]
ATLAS=Path(ATLAS_ENV) if ATLAS_ENV else a.DEFAULT_ATLAS_ROOT


class TestStandaloneSafety(unittest.TestCase):
    def test_a003_default_layout_and_override(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/'A003_Fourier_Knot_Seed_Atlas'
            adapter=folder/'A003_Fourier_Knot_Import_Adapter_v0.2.2'
            actual=folder/'A003-v0.1.2'
            actual.mkdir(parents=True)
            (actual/'manifest.json').write_text('{}',encoding='utf-8')
            self.assertEqual(a.resolve_atlas_root(environ={},adapter_root=adapter),actual.resolve())
            override=Path(td)/'other_atlas'
            override.mkdir()
            (override/'manifest.json').write_text('{}',encoding='utf-8')
            self.assertEqual(a.resolve_atlas_root(environ={'SST_ATLAS_ROOT':str(override)},
                      adapter_root=adapter),override.resolve())
            self.assertEqual(a.resolve_atlas_root(actual,environ={'SST_ATLAS_ROOT':str(override)},
                      adapter_root=adapter),actual.resolve())
            with self.assertRaisesRegex(a.GateFailure,'manifest.json'):
                a.resolve_atlas_root(Path(td)/'missing',environ={},adapter_root=adapter)
    def test_expected_catalog_48(self):
        self.assertEqual(len(a.expected_catalog()),48)
        self.assertEqual(a.expected_catalog()['torus_8_19_direct']['knot'],'8_19')

    def test_safe_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for p in ('../secrets.xyz','xyz/../../secrets.xyz','other/file.xyz','xyz/wrong.csv'):
                with self.assertRaises(a.GateFailure):a.safe_atlas_file(root,p)

    def test_projection_mirror(self):
        t=np.linspace(0,2*np.pi,300,endpoint=False)
        v=np.column_stack(((2+np.cos(4*t))*np.cos(3*t),
                           (2+np.cos(4*t))*np.sin(3*t),np.sin(4*t)))
        nv=np.array([.37,.61,.70]);nv/=np.linalg.norm(nv)
        q=a.projection_diagram(v);mr=a.projection_diagram(v-2*np.outer(v@nv,nv))
        self.assertEqual(q['projection_crossings'],mr['projection_crossings'])
        self.assertEqual(q['signed_crossing_sum'],-mr['signed_crossing_sum'])
        self.assertGreater(q['projection_crossings'],0)

    def test_reject_invalid_physical_scale(self):
        with self.assertRaises(a.GateFailure):
            a.prepared_asset(Path('.'),{'records':[]},seed='a',sampling='uniform_t',n=1200,
                target_N=512,core_radius=0.,unit_scale_m=None,expected_library_version='0.2.5',
                knotlib_home=None,topology_provider='auto',require_topology_certified=False,out=Path('x.npz'))


class TestG4G5Safety(unittest.TestCase):
    def test_determinant_references(self):
        cat=a.expected_catalog()
        self.assertEqual(gates.expected_determinant(cat['torus_8_19_direct']),3)
        self.assertEqual(gates.expected_determinant(cat['torus_10_124_hoste']),1)
        self.assertEqual(gates.expected_determinant(cat['kauffman_4_1']),5)
        self.assertEqual(gates.expected_determinant(cat['twist_9_2_m7_lissajous']),15)

    def test_g4_is_opt_in(self):
        reg={'records':[{'polyline_length_coordinate_units':31.5}]}
        report={'gate_results':{'G4_PHYSICAL_SCALE':'NOT_DEFINED'}}
        res=gates.bind_physical_scale(reg,report)
        self.assertEqual(res['status'],'NOT_DEFINED')
        self.assertEqual(report['gate_results']['G4_PHYSICAL_SCALE'],'NOT_DEFINED')
        self.assertNotIn('physical_length_m',reg['records'][0])

    def test_g4_mapping_and_dimensions(self):
        reg={'records':[{'polyline_length_coordinate_units':31.5}]}
        report={'gate_results':{'G4_PHYSICAL_SCALE':'NOT_DEFINED'}}
        g4=gates.bind_physical_scale(reg,report,assumed_core_radius_units=.05)
        self.assertAlmostEqual(g4['meters_per_atlas_unit'],gates.CANONICAL_RC_M/.05)
        self.assertAlmostEqual(reg['records'][0]['physical_length_m'],31.5*gates.CANONICAL_RC_M/.05)
        self.assertEqual(g4['status'],'PASS_DIMENSIONAL_HYPOTHESIS_ONLY')
        self.assertFalse(g4['geometry_thickness_certified'])
        self.assertFalse(g4['dynamical_self_confinement_certified'])

    def test_g4_rejects_invalid_reference_radius(self):
        for r in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(gates.QualificationError):
                gates.bind_physical_scale({'records':[]},{'gate_results':{}},
                                          assumed_core_radius_units=r)

    def test_g5_provider_unavailable(self):
        with patch.dict(sys.modules,{'pyknotid':None,'pyknotid.spacecurves':None}):
            report={'gate_results':{'G5_INDEPENDENT_TOPOLOGY':'NOT_RUN'}}
            out=gates.independent_topology_screen({'records':[]},report,
                                                  atlas_root=Path('.'),enabled=True)
            self.assertEqual(out['status'],'PROVIDER_UNAVAILABLE')
            self.assertFalse(out['independent_topology_certified'])

    def test_g5_mock_invariants_not_certification(self):
        if not ATLAS.is_dir():self.skipTest('Atlas unavailable')
        records=[r.copy() for r in a.load_manifest(ATLAS)[0]['records']
                 if r['id']=='torus_8_19_direct' and r['sampling']=='uniform_t' and r['points'] in (1200,2400)]
        registry={'records':records}
        report={'gate_results':{'G5_INDEPENDENT_TOPOLOGY':'NOT_RUN'}}
        out=gates.independent_topology_screen(registry,report,atlas_root=ATLAS,
                 enabled=True,determinant_fn=lambda pts:3)
        self.assertEqual(out['status'],'INVARIANT_SCREEN_ONLY_NOT_CERTIFIED')
        self.assertEqual(out['checked_embedded_curves'],2)
        self.assertFalse(out['independent_topology_certified'])
        self.assertFalse(out['chirality_certified'])
        self.assertEqual(records[0]['independent_topology_screen_status'],
                         'INVARIANT_MATCH_NOT_CERTIFIED')

    def test_g5_mock_mismatch_blocks(self):
        if not ATLAS.is_dir():self.skipTest('Atlas unavailable')
        records=[r.copy() for r in a.load_manifest(ATLAS)[0]['records']
                 if r['id']=='torus_8_19_direct' and r['sampling']=='uniform_t' and r['points'] in (1200,2400)]
        report={'gate_results':{'G5_INDEPENDENT_TOPOLOGY':'NOT_RUN'}}
        out=gates.independent_topology_screen({'records':records},report,atlas_root=ATLAS,
                 enabled=True,determinant_fn=lambda pts:5)
        self.assertEqual(out['status'],'FAIL_INVARIANT_SCREEN')
        self.assertEqual(out['seed_results'][0]['status'],'INVARIANT_MISMATCH')

    def test_g5_resolution_mismatch(self):
        if not ATLAS.is_dir():self.skipTest('Atlas unavailable')
        records=[r.copy() for r in a.load_manifest(ATLAS)[0]['records']
                 if r['id']=='torus_8_19_direct' and r['sampling']=='uniform_t' and r['points'] in (1200,2400)]
        out=gates.independent_topology_screen({'records':records},{'gate_results':{}},
                     atlas_root=ATLAS,enabled=True,determinant_fn=lambda pts:3 if len(pts)==1200 else 5)
        self.assertEqual(out['status'],'FAIL_INVARIANT_SCREEN')
        self.assertEqual(out['seed_results'][0]['status'],'RESOLUTION_MISMATCH')


@unittest.skipUnless(ATLAS.is_dir(),'Full atlas not present; pass SST_ATLAS_ROOT to run complete tests')
class TestRealAtlas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry,cls.report=a.validate_atlas(ATLAS)

    def test_all_384(self):
        self.assertEqual(len(self.registry['records']),384)
        self.assertEqual(self.report['unique_seeds'],48)
        self.assertEqual(self.report['gate_results']['G2_GEOMETRIC_MIRROR_DIAGNOSTIC'],'PASS')
        self.assertEqual(self.report['gate_results']['G5_INDEPENDENT_TOPOLOGY'],'NOT_RUN')

    def test_full_bridge(self):
        self.assertEqual(len(self.report['convergence']),288)
        self.assertTrue(any(x['high_N']==9600 for x in self.report['convergence']))
        self.assertGreater(self.report['arclength_chord_warning_count'],0)

    def test_hash_tamper_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);m,_=a.load_manifest(ATLAS)
            m=copy.deepcopy(m)
            one=m['records'][0]
            path=root/one['file'];path.parent.mkdir(parents=True)
            path.write_bytes((ATLAS/one['file']).read_bytes()+b'\n')
            (root/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(a.GateFailure,'SHA256 mismatch'):
                a.validate_atlas(root,diagram=False)

    def test_metadata_tamper_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);m,_=a.load_manifest(ATLAS)
            m=copy.deepcopy(m);m['records'][0]['knot']='4_1'
            (root/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(a.GateFailure,'conflicting declared knot'):
                a.validate_atlas(root,diagram=False)

    def test_v025_katlas_limit_preserved(self):
        rec=next(x for x in self.registry['records'] if x['knot']=='8_19')
        self.assertEqual(rec['topology_status'],'NOT_REGISTERED')
        self.assertEqual(rec['chirality_status'],'SOURCE_DECLARED_NOT_CERTIFIED')

    def test_prepare_mock_contract_only(self):
        # A stub exercises adapter handling, NOT the actual frozen library runtime.
        class DummyAsset:
            def __init__(self,pts):self.points=pts
        def load(path):return DummyAsset(np.loadtxt(path))
        calls=[]
        def prepare(pts,**kw):
            calls.append(kw)
            ids=np.linspace(0,len(pts)-1,kw['n']).astype(int)
            return pts[ids],{'topology_certification':{'status':'UNVERIFIED'},
                             'geometry_sha256':'dummy','knot_library':'sst-knot-library/0.2.5'}
        lib=types.SimpleNamespace(load_geometry=load,prepare_for_falsifier=prepare)
        with patch.object(a,'require_knot_library',return_value=lib),tempfile.TemporaryDirectory() as td:
            out=Path(td)/'prepared.npz'
            meta=a.prepared_asset(ATLAS,self.registry,seed='torus_8_19_direct',
                sampling='uniform_s_polyline',n=1200,target_N=256,core_radius=.05,
                unit_scale_m=None,expected_library_version='0.2.5',knotlib_home=None,
                topology_provider='auto',require_topology_certified=False,out=out)
            self.assertTrue(out.is_file());self.assertTrue(out.with_suffix('.json').is_file())
            self.assertEqual(np.load(out)['xyz'].shape,(256,3))
            self.assertIsNone(calls[0]['expected_topology'])  # outside frozen v0.2.5 KAtlas
            self.assertEqual(meta['source_expected_knot'],'8_19')
            self.assertEqual(meta['coordinates_units'],'dimensionless')
            self.assertEqual(meta['scientific_status'],'GEOMETRIC_ONLY')
            with self.assertRaisesRegex(a.GateFailure,'refusing to overwrite'):
                a.prepared_asset(ATLAS,self.registry,seed='torus_8_19_direct',
                sampling='uniform_s_polyline',n=1200,target_N=256,core_radius=.05,
                unit_scale_m=None,expected_library_version='0.2.5',knotlib_home=None,
                topology_provider='auto',require_topology_certified=False,out=out)




class TestWindowsEntrypoint(unittest.TestCase):
    def test_run_all_flag_matches_cli(self):
        root=Path(__file__).resolve().parents[1]
        cmd=(root/'run_all.cmd').read_text(encoding='utf-8')
        py=(root/'fourier_atlas_adapter.py').read_text(encoding='utf-8')
        self.assertIn('--reference-core-radius-units "%A_STAR%"',cmd)
        self.assertIn("p.add_argument('--reference-core-radius-units'",py)
        self.assertIn('"SST_ATLAS_ROOT=%ATLAS_ROOT%"',cmd)
        self.assertNotIn(' --a-star "%A_STAR%"',cmd)
        self.assertIn('python -m unittest discover',cmd)
    def test_g5_command_uses_supported_options(self):
        root=Path(__file__).resolve().parents[1]
        cmd=(root/'run_g5.cmd').read_text(encoding='utf-8')
        for option in ('--g5','--require-g5-evidence','--g5-resolutions BASIC',
                       '--reference-core-radius-units "%A_STAR%"'):
            self.assertIn(option,cmd)

if __name__=='__main__':unittest.main()

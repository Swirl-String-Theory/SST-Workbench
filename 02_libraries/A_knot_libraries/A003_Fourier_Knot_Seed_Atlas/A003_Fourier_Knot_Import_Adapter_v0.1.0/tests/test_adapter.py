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

ATLAS_ENV=os.environ.get('SST_ATLAS_ROOT')
PARENT=Path(__file__).resolve().parents[2]
ATLAS=Path(ATLAS_ENV) if ATLAS_ENV else PARENT/'SST_Fourier_Knot_Seed_Atlas_v0.1.1'


class TestStandaloneSafety(unittest.TestCase):
    def test_expected_catalog_30(self):
        self.assertEqual(len(a.expected_catalog()),30)
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


@unittest.skipUnless(ATLAS.is_dir(),'Full atlas not present; pass SST_ATLAS_ROOT to run complete tests')
class TestRealAtlas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry,cls.report=a.validate_atlas(ATLAS)

    def test_all_240(self):
        self.assertEqual(len(self.registry['records']),240)
        self.assertEqual(self.report['unique_seeds'],30)
        self.assertEqual(self.report['gate_results']['G2_GEOMETRIC_MIRROR_DIAGNOSTIC'],'PASS')
        self.assertEqual(self.report['gate_results']['G5_INDEPENDENT_TOPOLOGY'],'NOT_RUN')

    def test_full_bridge(self):
        self.assertEqual(len(self.report['convergence']),180)
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


if __name__=='__main__':unittest.main()

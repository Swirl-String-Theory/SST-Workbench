import math, unittest, tempfile, hashlib
import numpy as np
import sst_knotlib as sk

class KnotLibTests(unittest.TestCase):
    def test_resample_uniform(self):
        p=sk.classic_trefoil(200)
        q=sk.resample_closed(p,512)
        ds=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        self.assertLess(ds.std()/ds.mean(),0.01)

    def test_s3_roundtrip(self):
        p=sk.classic_trefoil(256,scale=0.2)
        q=sk.inverse_stereographic(p)
        r=sk.stereographic_project(q)
        self.assertLess(np.max(np.linalg.norm(p-r,axis=1)),1e-11)

    def test_track_is_closed_polyline(self):
        p=sk.shader_track_trefoil(512)
        ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
        self.assertTrue(np.isfinite(p).all())
        self.assertGreater(ds.min(),0.0)

    def test_bundle_shape(self):
        p=sk.classic_trefoil(256)
        b=sk.thread_bundle(p,6,3.0,0.05)
        self.assertEqual(b.shape,(6,256,3))

    def test_torus_trefoil_writhe_finite(self):
        p=sk.torus_knot(2,3,256,R=2.0,a=0.6)
        w=sk.writhe(p)
        self.assertTrue(math.isfinite(w))

    def test_self_linking_reference(self):
        p=sk.resample_closed(sk.classic_trefoil(512),512)
        edge,_=sk.ribbon_edges(p,0.05)
        r=sk.self_linking_report(p,edge)
        self.assertLess(r['linking_integer_residual'],0.01)
        self.assertAlmostEqual(r['linking'],-3.0,delta=0.01)

    def test_qualification(self):
        p=sk.classic_trefoil(512)
        q=sk.qualify_seed(p,core_radius=0.02,n=512)
        self.assertIn('metrics',q); self.assertIn('gates',q)

    def test_provenance_version_matches_package(self):
        p=sk.classic_trefoil(64)
        _, prov=sk.prepare_for_falsifier(p,core_radius=0.01,n=32,convergence_levels=(32,))
        self.assertEqual(prov['geometry_library'],f'sst-knot-geometry/{sk.__version__}')

    def test_blind_commitment_exact_bytes(self):
        p=sk.classic_trefoil(64)
        candidates=[('trefoil',p,{'family':'test'})]
        with tempfile.TemporaryDirectory() as td:
            commit=sk.make_blind_campaign(candidates,td,seed=12345)
            reveal=(__import__('pathlib').Path(td)/'private'/'reveal.json').read_bytes()
            self.assertEqual(hashlib.sha256(reveal).hexdigest(),commit)
            rep=sk.verify_blind_campaign(td,require_private=True)
            self.assertTrue(rep['pass'])
            self.assertTrue(rep['reveal_commitment_ok'])

if __name__=='__main__': unittest.main(verbosity=2)

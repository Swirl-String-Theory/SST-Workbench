import math, unittest, tempfile, hashlib, json, struct
from pathlib import Path
import numpy as np
import sst_knotlib as sk
from sst_knotlib.formats import load_geometry, save_vect_components
from sst_knotlib.topology import braid_reference_report

class KnotLibTests(unittest.TestCase):
    def test_resample_uniform(self):
        q=sk.resample_closed(sk.classic_trefoil(200),512); ds=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        self.assertLess(ds.std()/ds.mean(),0.01)

    def test_s3_roundtrip(self):
        p=sk.classic_trefoil(256,scale=0.2); r=sk.stereographic_project(sk.inverse_stereographic(p))
        self.assertLess(np.max(np.linalg.norm(p-r,axis=1)),1e-11)

    def test_bundle_and_self_linking(self):
        p=sk.resample_closed(sk.classic_trefoil(512),512); b=sk.thread_bundle(p,6,3.0,0.05)
        self.assertEqual(b.shape,(6,512,3)); edge,_=sk.ribbon_edges(p,0.05); r=sk.self_linking_report(p,edge)
        self.assertLess(r['linking_integer_residual'],0.01); self.assertAlmostEqual(r['linking'],-3.0,delta=0.01)

    def test_registry_integrity_and_core_ids(self):
        r=sk.KAtlasSnapshot(); self.assertEqual(set(r.ids()),{'3_1','4_1','6_2','7_4'})
        self.assertEqual(r.get('6.2').dt,(4,8,10,12,2,6)); self.assertEqual(r.get('7_4').determinant,15)

    def test_topology_inference_from_parent_folder(self):
        self.assertEqual(sk.infer_knot_id_from_name('root/6.2/ideal.txt'),'6_2')
        self.assertEqual(sk.infer_knot_id_from_name('root/7_4/fseries'),'7_4')
        self.assertIsNone(sk.infer_knot_id_from_name('SST_Knot_Library_v0.2.0/ideal.txt'))

    def test_braid_reference_component_counts(self):
        for kid in ('3_1','4_1','6_2','7_4'):
            rep=braid_reference_report(kid); self.assertTrue(rep['component_count_match'],kid); self.assertEqual(rep['component_count'],1)

    def test_braid_link_component_cycles(self):
        from sst_knotlib.braid import braid_closure_components
        comps=braid_closure_components(2,[1,1],resample_n=96)
        self.assertEqual(len(comps),2)
        self.assertTrue(all(c.shape==(96,3) for c in comps))
        lm=sk.linking_matrix(comps); self.assertAlmostEqual(abs(lm[0,1]),1.0,delta=0.03)

    def test_braid_seed_finite(self):
        for kid in ('3_1','4_1','6_2','7_4'):
            p=sk.generate_topology_seed(kid,method='braid',n=192); self.assertEqual(p.shape,(192,3)); self.assertTrue(np.isfinite(p).all())

    def test_7_4_lissajous(self):
        p=sk.lissajous_7_4(256); self.assertTrue(np.isfinite(p).all()); self.assertGreater(sk.curve_length(p),1.0)

    def test_extensionless_fseries_coordinate_loader(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'7.4'; d.mkdir(); path=d/'fseries'; np.savetxt(path,sk.lissajous_7_4(32))
            a=load_geometry(path); self.assertEqual(a.source_family,'knotplot_fseries'); self.assertEqual(a.points.shape,(32,3))

    def test_vect_multicomponent_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            a=sk.classic_trefoil(64); b=a+np.array([10.,0,0]); path=Path(td)/'link.vect'
            save_vect_components(path,[a,b]); asset=load_geometry(path); self.assertEqual(asset.n_components,2)
            self.assertEqual(asset.source_format,'vect'); self.assertEqual(asset.components[0].shape,(64,3))

    def test_knotplot_locd_reader(self):
        p=sk.classic_trefoil(16)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'3.1.knot'; data=p.astype('>f8').tobytes()
            raw=b'KnotPlot 1.0 test\n\x0c\n'+b'LOCD'+struct.pack('>I',len(data))+data+b'endf'
            path.write_bytes(raw); a=load_geometry(path); self.assertEqual(a.source_format,'knotplot_1.0')
            self.assertLess(np.max(np.abs(a.points-p)),1e-12)

    def test_prepare_provenance_and_no_false_certification(self):
        p=sk.classic_trefoil(64)
        _,prov=sk.prepare_for_falsifier(p,core_radius=0.01,n=32,convergence_levels=(32,),expected_topology='3_1',topology_provider='reference-only')
        self.assertEqual(prov['knot_library'],f'sst-knot-library/{sk.__version__}')
        self.assertEqual(prov['topology_certification']['status'],'UNVERIFIED')
        self.assertTrue(len(prov['katlas_snapshot_sha256'])==64)

    def test_entry_policy_semantics(self):
        base={'topology_certification':{'status':'UNVERIFIED'},'qualification':{'pass':True}}
        self.assertTrue(sk.evaluate_record(base,'audit')['pass'])
        self.assertFalse(sk.evaluate_record(base,'strict')['pass'])
        bad={'topology_certification':{'status':'MISMATCH'},'qualification':{'pass':True}}
        self.assertFalse(sk.evaluate_record(bad,'audit')['pass'])

    def test_blind_commitment_exact_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            commit=sk.make_blind_campaign([('trefoil',sk.classic_trefoil(64),{'family':'test'})],td,seed=12345)
            reveal=(Path(td)/'private'/'reveal.json').read_bytes(); self.assertEqual(hashlib.sha256(reveal).hexdigest(),commit)
            self.assertTrue(sk.verify_blind_campaign(td,require_private=True)['pass'])

if __name__=='__main__': unittest.main(verbosity=2)

import json, math, tempfile, unittest
from pathlib import Path
import numpy as np

from sst_wp.pklsa_adapter import atlas_rows, normalized_candidate, write_gpu_batch, read_gpu_batch
from sst_wp.gpu_funnel import pair_strain_rms, shape_signature_drift, cpu_screen_batch

class TestV040PKLSAGPU(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(__file__).resolve().parents[1]
        cls.atlas=cls.root/'datasets'/'SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1'
        cls.rows=atlas_rows(cls.atlas)

    def test_atlas_scope_2352_49(self):
        self.assertEqual(len(self.rows),2352)
        fams={r['family'] for r in self.rows}
        self.assertEqual(len(fams),49)
        self.assertEqual({sum(1 for r in self.rows if r['family']==f) for f in fams},{48})

    def test_multicomponent_candidate_preserved(self):
        r=next(r for r in self.rows if r['family']=='link_6.3.2')
        _,X,o=normalized_candidate(self.atlas,r,96)
        self.assertEqual(len(o)-1,3)
        self.assertEqual(len(X),96)

    def test_gpu_binary_roundtrip(self):
        r=self.rows[14*48+3];_,X,o=normalized_candidate(self.atlas,r,40)
        nxt=np.full(40,-1,dtype=np.int32)
        for ci in range(len(o)-1):
            a,b=int(o[ci]),int(o[ci+1]);nxt[a:b-1]=np.arange(a+1,b,dtype=np.int32);nxt[b-1]=a
        rec=[{'opaque_id':'GF_deadbeef','points':X,'offsets':o,'next':nxt}]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'b.bin';write_gpu_batch(p,rec,40,.055,.12);q=read_gpu_batch(p)
        self.assertEqual(q['K'],1);self.assertEqual(q['N'],40);self.assertTrue(np.allclose(q['records'][0]['points'],X))
        self.assertTrue(np.array_equal(q['records'][0]['next'],nxt))

    def test_pair_strain_zero_for_rigid_motion(self):
        r=self.rows[14*48];_,X,o=normalized_candidate(self.atlas,r,48)
        nxt=np.full(48,-1,dtype=np.int32)
        for ci in range(len(o)-1):
            a,b=int(o[ci]),int(o[ci+1]);nxt[a:b-1]=np.arange(a+1,b,dtype=np.int32);nxt[b-1]=a
        U=np.array([.2,-.1,.3]);Om=np.array([.4,.3,-.2]);V=U+np.cross(np.broadcast_to(Om,X.shape),X)
        self.assertLess(pair_strain_rms(X,V,nxt),1e-10)

    def test_shape_signature_is_rigid_invariant(self):
        r=self.rows[14*48];_,X,o=normalized_candidate(self.atlas,r,48)
        nxt=np.full(48,-1,dtype=np.int32)
        for ci in range(len(o)-1):
            a,b=int(o[ci]),int(o[ci+1]);nxt[a:b-1]=np.arange(a+1,b,dtype=np.int32);nxt[b-1]=a
        th=.7;R=np.array([[math.cos(th),-math.sin(th),0],[math.sin(th),math.cos(th),0],[0,0,1.]])
        Y=X@R.T+np.array([1.2,-.3,.4])
        self.assertLess(shape_signature_drift(X,Y,nxt),1e-12)

    def test_cpu_screen_is_finite(self):
        r=self.rows[0];_,X,o=normalized_candidate(self.atlas,r,24)
        nxt=np.full(24,-1,dtype=np.int32)
        for ci in range(len(o)-1):
            a,b=int(o[ci]),int(o[ci+1]);nxt[a:b-1]=np.arange(a+1,b,dtype=np.int32);nxt[b-1]=a
        out,meta=cpu_screen_batch([{'opaque_id':'GF_test','points':X,'offsets':o,'next':nxt}],.08,.12,1)
        self.assertEqual(len(out),1);self.assertTrue(np.isfinite(out[0]['pair_strain_rms']));self.assertEqual(meta['backend'],'cpu_reference_fallback')

if __name__=='__main__': unittest.main()

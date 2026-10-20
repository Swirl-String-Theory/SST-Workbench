"""Pure synthetic tests. No actual local Zenodo data or holdout responses are needed."""
import csv
import math
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'data'))
import importlib.util
p=Path(__file__).resolve().parents[1]/'data'/'f005_free_run_family_v0.4.0.py'
spec=importlib.util.spec_from_file_location('f005_v040',p)
f=importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class ProtectY:
    def __init__(self, real, permitted):
        self.real=real
        self.permitted=set(permitted)
        self.calls=[]
    def __getitem__(self, where):
        ids=where if isinstance(where,(list,tuple,np.ndarray)) else [where]
        self.calls.extend(ids)
        if not set(ids)<=self.permitted:
            raise AssertionError('Attempt to load forbidden TEST/OOD heights')
        return self.real[where]

class TestF005(unittest.TestCase):
    def test_split_complete(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'split.csv'
            p.write_text('row_id_zero_based,candidate_partition\n0,STANDARD_TRAIN\n1,STANDARD_VALIDATION\n',encoding='utf-8')
            labels,counts=f.read_split(p,2,expected=None)
            self.assertEqual(counts,{'STANDARD_TRAIN':1,'STANDARD_VALIDATION':1})
    def test_split_duplicate_block(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'split.csv'
            p.write_text('row_id_zero_based,candidate_partition\n0,STANDARD_TRAIN\n0,STANDARD_TEST\n',encoding='utf-8')
            with self.assertRaises(ValueError):f.read_split(p,1,expected=None)
    def test_split_invalid_index_block(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'split.csv'
            p.write_text('row_id_zero_based,candidate_partition\n5,STANDARD_TRAIN\n',encoding='utf-8')
            with self.assertRaises(ValueError):f.read_split(p,1,expected=None)
    def test_time_spacing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.csv'
            p.write_text('time_s\n0\n0.004\n0.008\n0.012\n',encoding='utf-8')
            self.assertAlmostEqual(f.load_time(p,4),.004)
    def test_time_nonuniform_block(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'t.csv'
            p.write_text('time_s\n0\n0.004\n0.007\n0.012\n',encoding='utf-8')
            with self.assertRaises(ValueError):f.load_time(p,4)
    def test_fingerprint_amplitude_invariance(self):
        x=np.sin(np.arange(240)*.04)
        self.assertEqual(f.fingerprint(x,64,.05),f.fingerprint(2*x,64,.05))
    def test_compare_preserve_sign(self):
        x=np.sin(np.arange(350)*.033)
        self.assertLess(f.compare_shapes(x,-x)['correlation'],-.9)
    def test_compare_scaling(self):
        x=np.sin(np.arange(350)*.033)
        s=f.compare_shapes(x,2*x)
        self.assertGreater(s['correlation'],.9999)
        self.assertAlmostEqual(s['norm_rmse'],0.,places=9)
    def test_family_identical_cross_partition(self):
        x=np.sin(np.arange(240)*.03)
        arr=np.vstack((x,2*x,x+0.3,np.cos(np.arange(240)*.03)))
        labels={0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION',2:'STANDARD_TEST',3:'OPTIMIZED_OOD'}
        stats,examples=f.family_audit(arr,labels,max_pairs=100,max_bucket=15)
        self.assertGreaterEqual(stats['near_shape_cross_partition_pairs'],1)
        self.assertGreaterEqual(stats['family_components_cross_partition'],1)
        self.assertEqual(examples[0]['row_a'],0)
        self.assertEqual(examples[0]['row_b'],1)
    def test_family_exact_duplicate(self):
        x=np.sin(np.arange(180)*.03)
        arr=np.vstack([x,x,2*x])
        labels={0:'STANDARD_TRAIN',1:'STANDARD_TEST',2:'STANDARD_VALIDATION'}
        stats,_=f.family_audit(arr,labels,max_pairs=25,max_bucket=10)
        self.assertEqual(stats['exact_duplicate_cross_partition_pairs'],1)
    def test_family_pair_budget_blocks(self):
        x=np.sin(np.arange(160)*.02)
        arr=np.tile(x,(12,1))
        labels={i:('STANDARD_TRAIN' if i%2==0 else 'STANDARD_VALIDATION') for i in range(12)}
        stats,_=f.family_audit(arr,labels,max_pairs=2,max_bucket=15)
        self.assertEqual(stats['status'],'REVIEW_INCOMPLETE_PAIR_BUDGET')
    def test_family_buckets_skipped_reported(self):
        x=np.sin(np.arange(160)*.02)
        arr=np.tile(x,(7,1))
        labels={i:('STANDARD_TRAIN' if i%2==0 else 'STANDARD_VALIDATION') for i in range(7)}
        stats,_=f.family_audit(arr,labels,max_pairs=400,max_bucket=3)
        self.assertGreater(stats['skipped_large_buckets'],0)
    def test_true_free_run_and_holdout_protection(self):
        N=6;T=1500;dt=.004
        beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        rng=np.random.default_rng(50)
        x=rng.normal(size=(N,T))*.1
        y=np.zeros((N,T));y[:,1]=1e-3
        for n in range(1,T-1):
            y[:,n+1]=beta[0]*y[:,n]+beta[1]*y[:,n-1]+beta[2]*dt*dt*x[:,n]
        guarded=ProtectY(y*1e3,{1,3})
        rows,tr=f.rollouts(x,guarded,dt,beta,[1,3])
        self.assertEqual(len(rows),15)
        self.assertLess(max(r['rmse_arx_m'] for r in rows),1e-13)
        self.assertTrue(set(guarded.calls)<= {1,3})
        self.assertGreater(len(tr),15)
    def test_incorrect_forcing_is_not_perfect(self):
        T=1500;dt=.004
        beta=(1.985,-.991,-1.12)
        x=np.zeros((3,T));x[1,:380]=3.0
        y=np.zeros((3,T));y[:,1]=.001
        for n in range(1,T-1):
            y[:,n+1]=beta[0]*y[:,n]+beta[1]*y[:,n-1]+beta[2]*dt*dt*x[:,n]
        rows,_=f.rollouts(x,y*1e3,dt,(1.95,-.95,0.0),[1],anchors_s=[.004],horizons_s=[.1,1.0])
        self.assertGreater(rows[-1]['rmse_arx_m'],1e-6)
    def test_no_teacher_forcing_after_seed(self):
        T=1500;dt=.004;beta=(1.985,-.99,0.)
        x=np.zeros((1,T));y=np.zeros((1,T));y[:,1]=.001
        for n in range(1,T-1):y[:,n+1]=beta[0]*y[:,n]+beta[1]*y[:,n-1]
        y2=y.copy();y2[:,200:]+=999 # modifies truth but NOT the forecast for anchor=.004
        s1,_=f.rollouts(x,y*1e3,dt,beta,[0],anchors_s=[.004],horizons_s=[1.0])
        s2,_=f.rollouts(x,y2*1e3,dt,beta,[0],anchors_s=[.004],horizons_s=[1.0])
        # first is near perfect, second will not be "corrected" to match corrupted truth
        self.assertLess(s1[0]['rmse_arx_m'],1e-13)
        self.assertGreater(s2[0]['rmse_arx_m'],10.)
    def test_anchor_window_bounds(self):
        with self.assertRaises(ValueError):
            f.rollouts(np.zeros((1,100)),np.zeros((1,100)),.004,(1.,0.,0.),[0],anchors_s=[.1],horizons_s=[1.0])

if __name__=='__main__':unittest.main(verbosity=2)

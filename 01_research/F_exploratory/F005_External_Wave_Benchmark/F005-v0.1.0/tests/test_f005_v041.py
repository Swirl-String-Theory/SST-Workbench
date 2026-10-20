"""SYNTHETIC ONLY: P5b incomplete-screen review, P6a independent validation, holdout guard."""
import csv, importlib.util, json, math, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
P=Path(__file__).resolve().parents[1]/'data'/'f005_free_run_family_v0.4.1.py'
spec=importlib.util.spec_from_file_location('f005_v041',P)
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
class GuardedOutputs:
    def __init__(self,y,allowed): self.y=y;self.allowed=set(allowed);self.requests=[]
    def __getitem__(self,key):
        ii=list(key) if isinstance(key,(list,tuple,np.ndarray)) else [key]
        self.requests+=ii
        if not set(ii).issubset(self.allowed):raise AssertionError('SEALED TEST/OOD HEIGHT ACCESS')
        return self.y[key]
class Tests(unittest.TestCase):
    def test_frozen_coefficients_are_stable(self):
        roots=np.roots([1,-1.9856661039519918,0.9908696423084401])
        self.assertLess(float(np.max(abs(roots))),1.)
    def test_exact_duplicate_even_when_budget_small(self):
        x=np.sin(np.arange(200)*.05)
        a=np.tile(x,(100,1))
        labs={i:['STANDARD_TRAIN','STANDARD_VALIDATION','STANDARD_TEST','OPTIMIZED_OOD'][i%4] for i in range(100)}
        out,ex=f.family_audit(a,labs,max_pairs=2,max_bucket=3)
        self.assertEqual(out['status'],'REVIEW_BOUNDED_SCREEN_NOT_FAMILY_CERTIFIED')
        self.assertGreater(out['exact_duplicate_cross_partition_pairs'],0)
        self.assertEqual(out['candidate_pairs_scored'],2)
        self.assertGreater(out['large_buckets_sampled'],0)
        self.assertGreater(out['candidate_pairs_not_scored_due_cap'],0)
    def test_amplitude_scaled_near_match_candidate(self):
        x=np.sin(np.arange(150)*.04)
        a=np.vstack([x,3*x,np.cos(np.arange(150)*.04)])
        labs={0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION',2:'STANDARD_TEST'}
        out,ex=f.family_audit(a,labs,max_pairs=100)
        self.assertGreater(out['near_shape_cross_partition_pairs'],0)
        self.assertEqual(out['exact_duplicate_cross_partition_pairs'],0)
    def test_negative_shape_not_matched(self):
        x=np.sin(np.arange(150)*.04)
        labs={0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION'}
        out,_=f.family_audit(np.vstack((x,-x)),labs,max_pairs=100)
        self.assertEqual(out['near_shape_cross_partition_pairs'],0)
    def test_nonfinite_input_blocks(self):
        x=np.sin(np.arange(150)*.03)
        a=np.vstack([x,x]);a[1,4]=np.nan
        out,_=f.family_audit(a,{0:'STANDARD_TRAIN',1:'STANDARD_TEST'},max_pairs=10)
        self.assertEqual(out['status'],'BLOCKED_NONFINITE_INPUT')
    def test_deterministic_candidate_selection(self):
        rng=np.random.default_rng(4)
        template=np.sin(np.arange(160)*.05)
        a=np.stack([(i%5+1)*template + rng.normal(0,0.002,160) for i in range(60)])
        labs={i:['STANDARD_TRAIN','STANDARD_VALIDATION','STANDARD_TEST'][i%3] for i in range(60)}
        r1,e1=f.family_audit(a,labs,max_pairs=23,max_bucket=6)
        r2,e2=f.family_audit(a,labs,max_pairs=23,max_bucket=6)
        self.assertEqual(r1,r2);self.assertEqual(e1,e2)
    def test_free_run_no_teacher_forcing(self):
        N,T=4,1500;dt=.004; beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        x=np.zeros((N,T)); y=np.zeros((N,T));y[:,1]=.001
        for n in range(1,T-1):y[:,n+1]=beta[0]*y[:,n]+beta[1]*y[:,n-1]
        protected=GuardedOutputs(y*1000,{0,2})
        rows,trace=f.rollouts(x,protected,dt,beta,[0,2])
        self.assertEqual(len(rows),15)
        self.assertLess(max(row['rmse_arx_m'] for row in rows),1e-12)
        self.assertTrue(set(protected.requests)<={0,2})
    def test_development_run_despite_low_pair_budget(self):
        N,T=12,1500;dt=.004;beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        s=np.sin(np.arange(T)*.08)
        a=np.tile(s,(N,1));y=np.zeros((N,T));y[:,1]=.001
        for n in range(1,T-1):y[:,n+1]=beta[0]*y[:,n]+beta[1]*y[:,n-1]+beta[2]*dt*dt*a[:,n]
        labels={i:('STANDARD_VALIDATION' if i in (2,5) else 'STANDARD_TEST' if i==3 else 'STANDARD_TRAIN') for i in range(N)}
        yy=GuardedOutputs(y*1e3,{2,5})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source.txt';source.write_text('test')
            cfg={'a':a,'y':yy,'dt':dt,'beta':beta,'labels':labels,
                 'counts':dict(__import__('collections').Counter(labels.values())),
                 'audit':{},'old_path':source,'source_hashes':{'test':'yes'},
                 'split_path':source,'input_path':source,'output_path':source}
            with patch.object(f,'source_lock',return_value=cfg):
                rep,out=f.run(root,max_pairs=2,max_bucket=3)
            self.assertEqual(rep['P6a']['status'],'DEVELOPMENT_CONDITIONAL_FREE_RUN_FAMILY_REVIEW_OPEN')
            self.assertEqual(rep['P5b']['status'],'REVIEW_BOUNDED_SCREEN_NOT_FAMILY_CERTIFIED')
            self.assertEqual(len(rep['P6a']['rows']),15)
            self.assertTrue(set(yy.requests)<={2,5})
            self.assertTrue((out/'v041_report.json').exists())
            self.assertTrue((out/'F005_FreeRun_Family_v0.4.1_DEVELOPMENT.pdf').exists())
            self.assertEqual(len((out/'validation_free_run_metrics.csv').read_text().splitlines()),16)
if __name__=='__main__':unittest.main(verbosity=2)

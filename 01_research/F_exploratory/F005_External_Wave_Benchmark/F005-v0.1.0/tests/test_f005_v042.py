"""SYNTHETIC ONLY. No real local user NPY files shipped with this patch."""
import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import numpy as np
ROOT=Path(__file__).resolve().parents[1]
FP=ROOT/'data'/'f005_qualification_v0.4.2.py'
SPEC=importlib.util.spec_from_file_location('f005_v042',FP)
f=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(f)
BASE=ROOT/'tests'/'fixtures'/'f005_free_run_family_v0.4.1.py'
SPEC2=importlib.util.spec_from_file_location('f005_v041_locked',BASE)
old=importlib.util.module_from_spec(SPEC2); SPEC2.loader.exec_module(old)

class GuardedResponses:
    def __init__(self,arr,valid):self.arr=arr;self.valid=set(valid);self.requested=[]
    def __getitem__(self,key):
        indices=list(key) if isinstance(key,(list,tuple,np.ndarray)) else [key]
        self.requested.extend(indices)
        if not set(indices).issubset(self.valid):
            raise AssertionError('SEALED TEST/OOD RESPONSES ACCESSED')
        return self.arr[key]

class TestF005(unittest.TestCase):
    def test_generated_candidates_no_pair_cap(self):
        x=np.sin(np.arange(120)*.08)
        a=np.stack([x*(1+i/10) for i in range(50)])
        labs={i:['STANDARD_TRAIN','STANDARD_VALIDATION','STANDARD_TEST','OPTIMIZED_OOD'][i%4] for i in range(50)}
        pool,st=f.generate_candidates(a,labs)
        old_stat,_=old.family_audit(a,labs,max_pairs=2,max_bucket=5)
        self.assertEqual(len(pool),old_stat['candidate_pairs_proposed'])
        self.assertGreater(len(pool),2)
        self.assertEqual(pool,sorted(set(pool)))
        match,edges,components,overlap=f.score_candidate_set(a,labs,pool,old)
        self.assertEqual(match['pairs_scored'],len(pool))
        self.assertEqual(match['near_shape_cross_partition_pairs'],sum(q['cross_partition'] for q in edges))
        self.assertGreater(match['approximate_components_cross_partition'],0)
        self.assertEqual(match['candidate_pairs_unscored'],0)
        self.assertEqual(st['exact_duplicate_cross_partition_pairs'],0)

    def test_exact_cross_partition_sha256_includes_unproposed(self):
        x=np.sin(np.arange(120)*.05)
        a=np.stack([x,x,x*1.05])
        labs={0:'STANDARD_TRAIN',1:'STANDARD_TEST',2:'STANDARD_VALIDATION'}
        _,result=f.generate_candidates(a,labs)
        self.assertGreaterEqual(result['exact_duplicate_cross_partition_pairs'],1)

    def test_same_v041_shape_compare(self):
        t=np.arange(100)*.04
        for i,j in [(np.sin(t),2.3*np.sin(t)),(np.sin(t),-np.sin(t)),(np.cos(t),np.sin(t))]:
            corr,rmse,shift=f.scored_shapes(i,j)
            ref=old.compare_shapes(i,j)
            self.assertAlmostEqual(corr,ref['correlation'],places=10)
            self.assertAlmostEqual(rmse,ref['norm_rmse'],places=10)
            self.assertEqual(shift,ref['shift'])

    def test_damped_oscillator_limit(self):
        dt=.004;beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        gamma,fd=f.oscillator_parameters(beta,dt)
        a=f.oscillator_unforced(np.array([.003]),np.array([.003]),dt,np.array([0,100,1000]),gamma,fd)
        self.assertAlmostEqual(a[0],.003)
        self.assertTrue(np.isfinite(a).all())
        self.assertLess(abs(a[-1]),abs(a[0]))

    def test_path_and_endpoint_are_different(self):
        n=3;T=1500;dt=.004
        x=np.zeros((n,T));y=np.zeros((n,T))
        beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        y[:,1]=np.array([.001,.002,.003])
        for t in range(1,T-1):y[:,t+1]=beta[0]*y[:,t]+beta[1]*y[:,t-1]
        r,d,tr,osc=f.qualified_rollouts(x,y*1000,[0,1,2],dt,beta)
        self.assertEqual(len(r),15)
        self.assertLess(max(k['path_rmse_arx_mm'] for k in r),1e-8)
        self.assertTrue(any(k['path_rmse_zero_response_mm']>0 for k in r))
        self.assertEqual(r[0]['time_points_in_path'],25)
        self.assertNotEqual(r[0]['path_rmse_zero_response_mm'],r[0]['endpoint_rmse_zero_response_mm'])
        self.assertAlmostEqual(osc['gamma_s_inv'],1.1465368587688405,places=6)

    def test_path_catches_errors_hidden_from_endpoint(self):
        N,T=2,1500;dt=.004
        x=np.zeros((N,T));y=np.zeros((N,T))
        # One transient error which has vanished by the end of a 1s horizon.
        y[:,75]=.003
        beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        scores,_,_,_=f.qualified_rollouts(x,y*1000,[0,1],dt,beta)
        row=next(z for z in scores if z['anchor_time_s']==.004 and z['horizon_s']==1.0)
        self.assertEqual(row['endpoint_rmse_arx_mm'],0.0)
        self.assertGreater(row['path_rmse_arx_mm'],0.1)

    def test_no_input_nonfinite_silent_skip(self):
        x=np.zeros((3,200));x[2,10]=np.nan
        labs={0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION',2:'STANDARD_TEST'}
        with self.assertRaisesRegex(ValueError,'Nonfinite'):
            f.generate_candidates(x,labs)

    def test_zero_baseline_and_bootstrap_ci(self):
        ci=f.bootstrap_delta(np.array([1.,1.,1.]),np.array([4.,4.,4.]),seed=2)
        self.assertAlmostEqual(ci[0],1.)
        self.assertAlmostEqual(ci[1],1.)

    def test_phase_skips_short_window(self):
        ref=np.ones((3,25)); pr=np.ones((3,25))
        self.assertEqual(f.segment_metrics(ref,pr,.004,2.87)['status'],'INSUFFICIENT_WINDOW')

    def test_source_lock_matches_v041(self):
        self.assertEqual(f.VERSION,'0.4.2')
        self.assertEqual(old.VERSION,'0.4.1')

    def test_end_to_end_guarded_no_sealed_lookups(self):
        N,T=14,1500;dt=.004
        rng=np.random.default_rng(14)
        a=rng.normal(0,.1,(N,T))
        a[4]=a[1]*2.5  # exact morphology, not exact bytes
        beta=(1.9856661039519918,-.9908696423084401,-1.118156917616826)
        y=np.zeros((N,T));y[:,1]=.001
        for k in range(1,T-1):y[:,k+1]=beta[0]*y[:,k]+beta[1]*y[:,k-1]+beta[2]*dt*dt*a[:,k]
        labs={i:('STANDARD_VALIDATION' if i in (2,7,12) else
                 'OPTIMIZED_OOD' if i==3 else 'STANDARD_TEST' if i==4 else 'STANDARD_TRAIN') for i in range(N)}
        sealed=GuardedResponses(y*1000,{2,7,12})
        with TemporaryDirectory() as td:
            root=Path(td);(root/'data').mkdir()
            (root/'data'/'f005_free_run_family_v0.4.1.py').write_bytes(BASE.read_bytes())
            source=root/'source.bin';source.write_bytes(b'synthetic input')
            cfg={'a':a,'y':sealed,'dt':dt,'beta':beta,'labels':labs,
                 'counts':dict(__import__('collections').Counter(labs.values())),
                 'old_path':source,'source_hashes':{'test':'synthetic'},
                 'input_path':source,'audit':{},'split_path':source,'output_path':source}
            with patch.object(f,'load_prior_module',return_value=old),patch.object(old,'source_lock',return_value=cfg):
                report,out=f.run(root,require_previous=False)
            self.assertTrue(set(sealed.requested)<={2,7,12})
            self.assertTrue(report['P6d']['test_ood_heights_accessed'] is False)
            self.assertEqual(report['P5c']['candidate_pairs_generated'],report['P5c']['pairs_scored'])
            self.assertEqual(len(report['P6d']['rows']),15)
            self.assertEqual(report['P6d']['scorecard']['total_predeclared_anchor_horizon_conditions'],15)
            self.assertEqual(report['P6g']['validation_input_screen_negative_count'] + report['P6g']['validation_input_candidate_connected_to_train_count'],3)
            for item in ('v042_report.json','V042_SUMMARY.md','validation_horizon_metrics.csv',
                         'family_candidate_matches_REVIEW.csv','input_shape_components_REVIEW.csv',
                         'input_screen_negative_validation_sensitivity.csv','phase_amplitude_diagnostic.csv',
                         'F005_v0.4.2_QUALIFICATION_DEVELOPMENT.pdf'):
                self.assertTrue((out/item).is_file(),item)
            self.assertGreater((out/'F005_v0.4.2_QUALIFICATION_DEVELOPMENT.pdf').stat().st_size,1000)

if __name__=='__main__':unittest.main(verbosity=2)

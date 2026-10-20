import csv, importlib.util, math, tempfile, unittest
from pathlib import Path
import numpy as np

SRC=Path(__file__).resolve().parents[1]/'data'/'f005_integrity_baseline_v0.3.0.py'
spec=importlib.util.spec_from_file_location('f005_v030',SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class TestGates(unittest.TestCase):
    def make_split(self,records):
        tmp=tempfile.TemporaryDirectory();p=Path(tmp.name)/'split.csv'
        with p.open('w',encoding='utf-8',newline='') as f:
            wr=csv.writer(f);wr.writerow(['row_id_zero_based','candidate_partition','note'])
            for i,x in records:wr.writerow([i,x,'candidate'])
        self.addCleanup(tmp.cleanup);return p

    def test_split_legal(self):
        p=self.make_split([(0,'STANDARD_TRAIN'),(1,'STANDARD_VALIDATION'),(2,'STANDARD_TEST')]);a=m.read_split(p,3,expected=None)
        self.assertEqual(a['status'],'PASS');self.assertEqual(a['count'],3)

    def test_split_missing(self):
        p=self.make_split([(0,'STANDARD_TRAIN'),(2,'STANDARD_TEST')]);self.assertEqual(m.read_split(p,3,expected=None)['status'],'FAIL')

    def test_split_duplicate(self):
        p=self.make_split([(0,'STANDARD_TRAIN'),(0,'STANDARD_VALIDATION')]);self.assertEqual(m.read_split(p,1,expected=None)['status'],'FAIL')

    def test_cohort_not_family(self):
        meta=[{'trajectory_id':'a','trajectory_label':'a','trajectory_subset':'Standard'},
              {'trajectory_id':'b','trajectory_label':'b','trajectory_subset':'Standard'}]
        v=m.check_metadata_groups(meta,{0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION'})
        self.assertEqual(v['blockers'],[])
        self.assertEqual(v['fields']['trajectory_subset']['cross_partition_labels'],1)

    def test_duplicate_metadata_label(self):
        meta=[{'trajectory_id':'1','trajectory_label':'repeated','trajectory_subset':'Standard'},
              {'trajectory_id':'2','trajectory_label':'repeated','trajectory_subset':'Standard'}]
        v=m.check_metadata_groups(meta,{0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION'})
        self.assertTrue(v['blockers'])

    def test_exact_input_duplicate(self):
        a=np.array([[1.,2.,3.,4.],[1.,2.,3.,4.],[3.,4.,5.,6.]])
        out=m.audit_input_content(a,{0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION',2:'STANDARD_TRAIN'})
        self.assertEqual(out['exact_duplicate_cross_partition_groups'],1)
        self.assertEqual(out['status'],'FAIL')

    def test_coarse_collision_unproven(self):
        row=np.linspace(0,1,512)
        x=m.normalized_input_fingerprint(row)
        self.assertEqual(x,m.normalized_input_fingerprint(2*row))

    def test_oscillator_complex_stable(self):
        dt=.004; gamma=0.7; f=3.0
        r=math.exp(-gamma*dt);w=2*math.pi*f*dt
        A=2*r*math.cos(w);B=-r*r;C=-0.5
        result=m.derive_oscillator_coefficients([A,B,C],dt)
        self.assertTrue(result['poles_stable'])
        self.assertAlmostEqual(result['ringdown_frequency_hz'],3.0,places=7)
        self.assertAlmostEqual(result['ringdown_gamma_per_s'],0.7,places=7)

    def test_fit_recovery(self):
        dt=.004; A=1.99;B=-0.993;C=-0.13
        rng=np.random.default_rng(42)
        a=rng.normal(0,2,(12,256))
        y=np.zeros_like(a)
        for n in range(1,255):y[:,n+1]=A*y[:,n]+B*y[:,n-1]+C*dt*dt*a[:,n]
        beta,detail=m.fit_arx_train(a,y*1000,list(range(9)),dt)
        self.assertTrue(np.allclose(beta,[A,B,C],rtol=3e-3,atol=0.003),str(beta))
        score=m.validate_one_step(a,y*1000,list(range(9,12)),dt,beta)
        self.assertLess(score['one_step_rmse_m'],1e-7)

    def test_metadata_count(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        p=Path(t.name)/'m.csv';p.write_text('trajectory_id,trajectory_label\na,x\nb,y\n')
        self.assertTrue(m.read_metadata(p,2)['count_matches'])

    def test_nonfinite_leakage(self):
        a=np.array([[1.,float('nan'),2.], [1.,2.,3.]])
        out=m.audit_input_content(a,{0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION'})
        self.assertEqual(out['nonfinite_row_count'],1)
        self.assertEqual(out['status'],'FAIL')

if __name__=='__main__':unittest.main(verbosity=2)

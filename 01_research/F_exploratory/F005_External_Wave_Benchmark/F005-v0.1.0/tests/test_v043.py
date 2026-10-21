import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import Counter
from unittest.mock import patch
import numpy as np

SOURCE=Path(__file__).resolve().parents[1]/'data'/'f005_family_disjoint_v0.4.3.py'
spec=importlib.util.spec_from_file_location('f005_v043',SOURCE)
f=importlib.util.module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)

class Guard:
    """Fail closed on attempts to index original TEST/OOD measured responses."""
    def __init__(self,data,allowed):self.data=data;self.allowed=set(allowed);self.accessed=[]
    def __getitem__(self,indices):
        ids=np.atleast_1d(indices).tolist()
        for i in ids:
            i=int(i)
            if i not in self.allowed:raise AssertionError(f'SEALED OUTPUT ACCESS {i}')
            self.accessed.append(i)
        return self.data[indices]

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng=np.random.default_rng(784)
        cls.dt=.004; cls.n=70;N=cls.n;T=1500
        tt=np.arange(T)*cls.dt
        a=np.zeros((N,T));y=np.zeros_like(a)
        cls.groups=[]
        for g in range(14):
            group=list(range(g*5,(g+1)*5));cls.groups.append(group)
            amp=float(rng.uniform(.7,2.4));fdrive=float(rng.uniform(.3,1.7))
            for i in group:
                # Identical SHAPE, distinct amplitude, reproducible proxy family
                a[i]=amp*(.7+.3*(i%5))*np.sin(2*np.pi*fdrive*tt) * (tt<1.6)*(tt>.04)
        gam=.9;w=2*np.pi*2.8;K=-1.05
        denom=1+gam*cls.dt
        coeff=((2-w*w*cls.dt**2)/denom,-(1-gam*cls.dt)/denom,K/denom)
        cls.true_coeff=coeff
        y[:,1]=rng.uniform(.001,.003,size=N)
        for t in range(1,T-1):
            y[:,t+1]=coeff[0]*y[:,t]+coeff[1]*y[:,t-1]+coeff[2]*cls.dt**2*a[:,t]
        cls.a=a;cls.y=y*1000
        cls.labels={i:'STANDARD_TRAIN' if i%5<3 else 'STANDARD_VALIDATION' for i in range(60)}
        cls.labels.update({i:'STANDARD_TEST' if i<65 else 'OPTIMIZED_OOD' for i in range(60,70)})
        cls.dev_groups=[g for g in cls.groups if g[0]<60]

    def test_deterministic_component_split(self):
        t1,v1,r1=f.split_proxy_groups(self.dev_groups)
        t2,v2,r2=f.split_proxy_groups(self.dev_groups)
        self.assertEqual((t1,v1,r1),(t2,v2,r2))
        self.assertFalse(set(t1)&set(v1))
        self.assertEqual(len(t1)+len(v1),60)
        for g in self.dev_groups:self.assertTrue(set(g)<=set(t1) or set(g)<=set(v1))

    def test_arx_training_converges_and_is_stable(self):
        ids=list(range(40))
        coeff,info=f.fit_arx_train(self.a,self.y,ids,self.dt)
        self.assertTrue(info['stable'])
        self.assertLess(np.max(abs(np.array(coeff)-self.true_coeff)),.25)

    def test_oscillator_independent_train_fit(self):
        coeff,info=f.fit_oscillator_train(self.a,self.y,list(range(40)),self.dt)
        self.assertEqual(info['status'],'FITTED_TRAIN_ONLY_REDUCED_ORDER')
        self.assertTrue(info['ringdown_samples']>1500)
        self.assertTrue(np.all(np.isfinite(coeff)))
        recurrence=f.oscillator_recurrence(coeff,self.dt)
        self.assertLess(abs(recurrence[2]-self.true_coeff[2]),.25)

    def test_no_teacher_forcing_in_recursion(self):
        ids=[5,10];coeff=self.true_coeff
        p=f.recursive_predictions(self.a,self.y,ids,self.dt,coeff)
        self.assertLess(np.max(abs(p[1][0]-p[1][1])),1e-8)

    def test_group_bootstrap_determinism(self):
        err1=np.array([2.,1.,1.,.5]);err2=err1+1
        groups=['a','a','b','c']
        lohi=f.group_bootstrap_difference(err1,err2,groups,nboot=30)
        self.assertGreater(lohi[0],0)
        self.assertEqual(lohi,f.group_bootstrap_difference(err1,err2,groups,nboot=30))

    def test_qualified_error_detects_midpath_mistake(self):
        x=np.zeros((3,1500));y=np.zeros_like(x);y[:,100]=3.
        m,t=f.evaluate(x,y,[0,1,2],[dict(row_id_zero_based=i,proxy_component_id=str(i)) for i in range(3)],.004,self.true_coeff,nboot=8)
        one=next(r for r in m if r['anchor_s']==.004 and r['horizon_s']==1.)
        self.assertEqual(one['ARX_RETRAINED_ENDPOINT_RMSE_MM'],0.)
        self.assertGreater(one['ARX_RETRAINED_PATH_RMSE_MM'],0.)

    def test_graph_import_and_locked_source_sha(self):
        import json,csv
        labels={0:'STANDARD_TRAIN',1:'STANDARD_VALIDATION',2:'STANDARD_TEST',3:'OPTIMIZED_OOD'}
        x=np.sin(np.arange(1500)*.015)
        a=np.stack([x,2*x,np.cos(np.arange(1500)*.015),3*x])
        with TemporaryDirectory() as td:
            root=Path(td);p=root/'outputs'/'f005_qualification_v0.4.2';p.mkdir(parents=True)
            source=root/'source.npy';np.save(source,a)
            accepted=p/'family_candidate_matches_REVIEW.csv'
            accepted.write_text('row_a,partition_a,row_b,partition_b,correlation,norm_rmse,shift,cross_partition\n'
                '0,STANDARD_TRAIN,1,STANDARD_VALIDATION,1.0,0.0,0,1\n',encoding='utf-8')
            r={'tool':'F005_Qualification_v0.4.2','P5c':{'candidate_pairs_unscored':0,
               'independence_certification':'BLOCKED_NO_SOURCE_FAMILY_IDENTIFIERS',
               'near_shape_total_pairs':1},'P6g':{'test_ood_response_sealed':True},
               'source_locks':{'input_npy_sha256':f.sha(source)}}
            (p/'v042_report.json').write_text(json.dumps(r))
            groups,meta=f.graph_from_v042(root,labels,a,input_path=source)
            self.assertEqual(meta['matched_edges'],1)
            self.assertEqual(meta['development_edges'],1)
            self.assertEqual([0,1],next(g for g in groups if 0 in g))
            r['source_locks']['input_npy_sha256']='BAD'
            (p/'v042_report.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'SHA256'):
                f.graph_from_v042(root,labels,a,input_path=source)

    def test_insufficient_ringdown_fails_closed(self):
        # No quiet intervals and no free-ringdown data.
        n,t=4,1500
        a=np.ones((n,t));y=np.ones((n,t))
        fit,info=f.fit_oscillator_train(a,y,list(range(n)),.004)
        self.assertIsNone(fit)
        self.assertEqual(info['status'],'BLOCKED_INSUFFICIENT_FREE_RINGDOWN')

    def test_sealed_outputs_end_to_end(self):
        dev={i for i,p in self.labels.items() if p in ('STANDARD_TRAIN','STANDARD_VALIDATION')}
        cfg=dict(a=self.a,y=Guard(self.y,dev),labels=self.labels,dt=self.dt,
                 source_hashes={'kind':'synthetic'},counts=dict(Counter(self.labels.values())))
        info=dict(matched_edges=0,development_edges=0,matched_cross_original_partitions=0,
                  edge_rechecks=0,components=len(self.dev_groups),largest_component=5,
                  source_family_identity='SYNTHETIC')
        with TemporaryDirectory() as td:
            with patch.object(f,'make_pdf') as pdf:
                report,out=f.run(td,cfg_override=cfg,graph_override=(self.dev_groups,info),nboot=12)
            self.assertTrue(report['provenance']['test_ood_response_access'] is False)
            self.assertEqual(report['P5d']['cross_split_near_edges'],0)
            self.assertEqual(len(report['P6h']['metrics']),15)
            self.assertEqual(report['P6i']['fit']['status'],'FITTED_TRAIN_ONLY_REDUCED_ORDER')
            self.assertTrue((out/'v043_report.json').exists())
            self.assertTrue((out/'proxy_family_development_split.csv').exists())
            self.assertTrue(pdf.called)

if __name__=='__main__':unittest.main(verbosity=2)

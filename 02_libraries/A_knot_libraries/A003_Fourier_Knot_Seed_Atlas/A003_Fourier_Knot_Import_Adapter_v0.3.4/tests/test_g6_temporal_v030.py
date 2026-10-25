"""Targeted v0.3.0 tests; numerical mocks never count as scientific validation."""
import json,math,os,sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from g6_pklsa_temporal_v030 import (rk4,carrier_rows,register_e010,temporal_run,curve_length,
   nonlocal_vertex_distance,c005_callable,SEEDS,SOURCE_ID)
from g6_pklsa_pilot_v029 import source_check

class TemporalMathTests(unittest.TestCase):
    def test_rk4_known_analytic_exp(self):
        x=np.array([[1.,2.,3.]],dtype=float)
        one,_=rk4(lambda q:q,x,1.,4)
        two,_=rk4(lambda q:q,x,1.,8)
        three,_=rk4(lambda q:q,x,1.,16)
        e1=np.linalg.norm(one-np.exp(1)*x)
        e2=np.linalg.norm(two-np.exp(1)*x)
        e3=np.linalg.norm(three-np.exp(1)*x)
        self.assertGreater(e1,e2*10)
        self.assertGreater(e2,e3*10)
        self.assertTrue(np.all(np.isfinite(three)))
    def test_nonlocal_vertex_gap(self):
        x=np.c_[np.cos(np.arange(30)*2*np.pi/30),np.sin(np.arange(30)*2*np.pi/30),np.zeros(30)]
        self.assertGreater(nonlocal_vertex_distance(x),0.8)
        self.assertGreater(curve_length(x),6)
    def test_invalid_halving_rejected(self):
        from g6_pklsa_temporal_v030 import temporal_run
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):temporal_run(Path(t),{},Path(t),Path(t),steps=(4,7,16))

class SourceContracts(unittest.TestCase):
    def test_analytic_carriers_are_correlated(self):
        reg={'records':[]}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'xyz').mkdir()
            for seed in SEEDS:
                for n in (1200,2400,4800,9600):
                    rel=f'xyz/{seed}_{n}.xyz'
                    d=root/rel;d.write_text('1 2 3\n')
                    import hashlib
                    reg['records'].append({'id':seed,'points':n,'sampling':'uniform_t','file':rel,'sha256':hashlib.sha256(d.read_bytes()).hexdigest()})
            rows=carrier_rows(root,reg)
            self.assertEqual(len(rows),8)
            self.assertEqual(len({r['independence_group'] for r in rows}),2)
            self.assertTrue(all(r['topology_not_certified'] for r in rows))
    def test_missing_e010_does_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            self.assertEqual(register_e010(t,{},t,t,t)['status'],'UNRESOLVED')
    def test_external_atlas_does_not_auto_register(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td);a=t/'data';wb=t/'workspace';a.mkdir();wb.mkdir()
            self.assertEqual(register_e010(a,{},wb,wb,t)['status'],'UNRESOLVED')
    def test_existing_source_id_collision_fails_closed(self):
        import shutil
        from g6_pklsa_temporal_v030 import SOURCE_ID
        # Contract collision must be checked before importing native E010.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a').mkdir();(root/'e/sst_pklsa').mkdir(parents=True);(root/'e/configs').mkdir()
            (root/'e/sst_pklsa/__init__.py').write_text('')
            (root/'e/sst_pklsa/core.py').write_text('')
            (root/'e/configs/source_contract_v1.json').write_text(json.dumps({'sources':[{'source_id':SOURCE_ID}]}))
            with self.assertRaises(RuntimeError):register_e010(root/'a',{},root,root/'e',root)

if __name__=='__main__':unittest.main()

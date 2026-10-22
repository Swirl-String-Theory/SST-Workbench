from __future__ import annotations
import importlib.util, pathlib, tempfile, unittest, json
import numpy as np

SRC=pathlib.Path(__file__).resolve().parents[1]/'data/f005_e0_provenance_audit.py'
spec=importlib.util.spec_from_file_location('e0',SRC)
e0=importlib.util.module_from_spec(spec);spec.loader.exec_module(e0)

class Protected:
    def __init__(self): self.calls=[]
    def __getitem__(self, key):
        ix=key[0]
        indices=np.asarray(ix)
        if np.any(indices>=5000): raise AssertionError('SEALED_READ')
        self.calls.append(indices.copy())
        return np.zeros((len(indices),4))

class Tests(unittest.TestCase):
    def test_geometry_lock(self):
        cmp,missing,flags=e0.geometry_documentation_check(dict(e0.GEOMETRY))
        self.assertTrue(all(v['match'] for v in cmp.values()))
        self.assertEqual(set(missing), {'acceleration_axis_sign','measurement_height_sign'})
        self.assertTrue(flags['initial_equilibrium_confirmed'])
    def test_geometry_mismatch(self):
        cfg=dict(e0.GEOMETRY,tank_length_internal_m=0.12)
        cmp,_,_=e0.geometry_documentation_check(cfg)
        self.assertFalse(cmp['tank_length_internal_m']['match'])
    def test_model_sign_is_odd(self):
        a=np.ones((2,100))
        r,f=e0.model_from_rest(a)
        self.assertEqual(r.shape,(2,100))
        self.assertTrue(np.allclose(e0.model_from_rest(-a)[0], -r))
        self.assertTrue(np.all(f>0))
        self.assertAlmostEqual(r[0,0],0)
    def test_initial_diagnostic_no_certification(self):
        a=np.zeros((3,201))
        y=np.zeros_like(a)
        ini,sign=e0.signs_and_initial_state(a,y,.004)
        self.assertEqual(ini['status'],'DESCRIPTIVE_NOT_PROOF_OF_REST')
        self.assertIn('0.5',sign)
        self.assertEqual(sign['0.5']['relative_polarity_hypotheses']['1']['from_rest_path_rmse_mm'],0)
    def test_bad_shape(self):
        with self.assertRaises(ValueError):e0.signs_and_initial_state(np.zeros((2,10)),np.zeros((2,10)),.004)
    def test_nonfinite(self):
        a=np.zeros((2,160));y=np.zeros_like(a);y[1,4]=float('nan')
        with self.assertRaises(ValueError):e0.signs_and_initial_state(a,y,.004)
    def test_locked_train_safeguard(self):
        a=Protected();y=Protected()
        xx,yy=e0.read_train_only(a,y,list(range(3400)))
        self.assertEqual(xx.shape,(3400,4))
        self.assertEqual(len(a.calls),1)
        self.assertEqual(len(y.calls),1)
    def test_locked_train_reject_sealed_index(self):
        a=Protected();y=Protected();r=list(range(3399))+[5000]
        with self.assertRaises(ValueError):e0.read_train_only(a,y,r)
        self.assertFalse(a.calls)
        self.assertFalse(y.calls)
    def test_locked_train_reject_nonunique(self):
        a=Protected();y=Protected();r=list(range(3399))+[0]
        with self.assertRaises(ValueError):e0.read_train_only(a,y,r)
    def test_no_geometry_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            cfg=root/'config.json';raw=json.dumps(e0.GEOMETRY)
            cfg.write_text(raw)
            st=e0.run(root,root/'out',cfg)
            self.assertEqual(st['status'],'E0_DIAGNOSTIC_BLOCKED')
            self.assertEqual(cfg.read_text(),raw)
            self.assertTrue((root/'out'/'e0_audit_report.json').exists())

if __name__=='__main__':unittest.main()

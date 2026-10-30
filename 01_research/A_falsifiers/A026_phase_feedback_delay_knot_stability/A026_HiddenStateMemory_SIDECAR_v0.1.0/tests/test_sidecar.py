import unittest
import numpy as np
from src.model import synthetic, energy
from src.analysis import compare

class TestConservativeMemory(unittest.TestCase):
    def test_energy_exact(self):
        d=synthetic(n=120)
        rel=np.max(np.abs(d['final_energy']-d['initial_energy'])/np.maximum(d['initial_energy'],1e-20))
        self.assertLess(rel, 1e-12)

    def test_coupled_history_improves(self):
        r=compare(synthetic(n=1200,coupling=2.0))
        self.assertGreater(r['ci95_gain'][0],0.20)

    def test_decoupled_null_no_false_memory(self):
        r=compare(synthetic(n=1200,coupling=0.0))
        self.assertLess(r['ci95_gain'][1],0.05)

    def test_shuffled_history_null(self):
        d=synthetic(n=1200,coupling=2.0)
        d['history']=d['history'][np.random.default_rng(123).permutation(1200)]
        r=compare(d)
        self.assertLess(r['ci95_gain'][1],0.05)

    def test_sample_gate(self):
        d=synthetic(n=90)
        for k in ('current','history','target'): d[k]=d[k][:20]
        with self.assertRaises(ValueError): compare(d)

    def test_si(self):
        self.assertEqual(synthetic(n=100)['units']['energy'],'J')
if __name__ == '__main__': unittest.main()

class TestExternalContract(unittest.TestCase):
    def test_external_intake_is_unverified(self):
        import tempfile, json
        from pathlib import Path
        from src.intake import read_external
        n=90; t=np.linspace(0,3,13)
        base=np.linspace(0.001,0.01,n)[:,None]
        q=base*np.cos(2*t)[None,:]
        qdot=-2*base*np.sin(2*t)[None,:]
        meta={k:'TEST_ONLY' for k in ['solver_name','solver_revision','source_manifest_sha256',
             'observable_definition','geometry_manifest_sha256','core_model','boundary_conditions']}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'test.npz'
            np.savez(p,times_s=t,q_m=q,qdot_m_s=qdot,
                     trial_ids=np.arange(n).astype('U8'),metadata_json=json.dumps(meta))
            data, provenance=read_external(p)
            self.assertEqual(len(data['target']),n)
            self.assertEqual(provenance['status'],'UNVERIFIED_EXTERNAL_PROVENANCE')
            self.assertIn('file_sha256',provenance)

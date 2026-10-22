"""Safety and provenance unit fixtures; never constitute scientific G6 observations."""
import sys, tempfile, unittest, hashlib, json, math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from g6_safety_independence_v032 import (polygon_interpolant_certificate,
   dop853_independent_integrator,e010_candidate_contract,persistent_registry_readback,euler_closure_audit)
from g6_external_carriers_v032 import audit_external_carriers,arclength_resample


def circle(n=80):
    t=2*np.pi*np.arange(n)/n
    return np.column_stack([np.cos(t),np.sin(t),.13*np.sin(2*t)])

class TestInterpolantCertificate(unittest.TestCase):
    def test_static_polygon_pass(self):
        x=circle();r=polygon_interpolant_certificate([x,x,x])
        self.assertEqual(r['status'],'PASS_INTERPOLANT_ONLY')
        self.assertFalse(r['certifies_true_ode_path'])
        self.assertFalse(r['certifies_continuum_euler'])
    def test_small_movement_is_certifiable(self):
        x=circle();y=x+np.array([1.e-5,2.e-5,0.])
        self.assertEqual(polygon_interpolant_certificate([x,y])['status'],'PASS_INTERPOLANT_ONLY')
    def test_big_motion_never_false_pass(self):
        x=circle();y=x+np.array([1.,0.,0.])
        self.assertNotEqual(polygon_interpolant_certificate([x,y])['status'],'PASS_INTERPOLANT_ONLY')
    def test_real_crossing_is_fail(self):
        x=np.array([[-1.,0,0],[1.,0,0],[3.,3,0],[0.,-1,0],[0.,1,0],[3.,-3,0]])
        self.assertEqual(polygon_interpolant_certificate([x,x])['status'],'FAIL_OBSERVED_SEGMENT_CONTACT')
    def test_invalid_state_and_wrong_n_rejected(self):
        with self.assertRaises(ValueError):polygon_interpolant_certificate([circle(80),circle(82)])
    def test_sampled_scope_cannot_claim_true_ode(self):
        x=circle();p=polygon_interpolant_certificate([x,x])
        self.assertTrue(p['all_intervals_certified_for_interpolant'])
        self.assertFalse(p['certifies_true_ode_path'])

class TestIndependentSolver(unittest.TestCase):
    def test_stable_dop853_vs_analytic(self):
        x=circle()
        def f(y):return .01*np.column_stack([-y[:,1],y[:,0],np.zeros(len(y))])
        a=.01*2.;mat=np.array([[math.cos(a),math.sin(a),0],[-math.sin(a),math.cos(a),0],[0,0,1]])
        ref=x@mat
        r=dop853_independent_integrator(f,x,2.,ref)
        self.assertEqual(r['status'],'PASS_DIAGNOSTIC_ONLY')
        self.assertFalse(r['independent_physical_provider'])
    def test_wrong_reference_fails(self):
        x=circle();r=dop853_independent_integrator(lambda x:np.zeros_like(x),x,2.,x+0.01)
        self.assertEqual(r['status'],'FAIL_SOLVER_DISAGREEMENT')

class TestSourceGuard(unittest.TestCase):
    def test_no_external_is_unresolved(self):
        r=audit_external_carriers(None,None,None,Path('.'),.05,2.)
        self.assertEqual(r['status'],'UNRESOLVED')
    def test_arclength_resampling_preserves_closed_curve(self):
        x=circle(400);y=arclength_resample(x,150)
        self.assertEqual(y.shape,(150,3))
        self.assertLess(np.linalg.norm(y[0]-x[0]),1e-10)
    def test_euler_audit_cannot_fake_closure(self):
        z=euler_closure_audit({'source':'fermat_ext.core.backend_biot_savart'},.05,'PASS')
        self.assertEqual(z['status'],'UNRESOLVED')
        self.assertEqual(z['checks']['pressure_poisson_source_and_boundary_conditions'],'NOT_IMPLEMENTED')
    def test_persistent_readback_without_files_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            z=persistent_registry_readback(root,root,root,{'records':[]})
            self.assertEqual(z['status'],'UNRESOLVED')
    def test_candidate_does_not_mutate_e010(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);atlas=r/'atlas';atlas.mkdir();(atlas/'xyz').mkdir();e010=r/'e010';(e010/'configs').mkdir(parents=True)
            c=e010/'configs'/'source_contract_production_v2.json';c.write_text(json.dumps({'sources':[]}),encoding='utf-8')
            x=circle(1200);records=[]
            for sid in ('fibonacci_torus_F3','fibonacci_torus_F4'):
                for n in (1200,2400,4800,9600):
                    f=atlas/'xyz'/f'{sid}_{n}.xyz';np.savetxt(f,np.tile(x,(math.ceil(n/1200),1))[:n],fmt='%.17g')
                    records.append({'id':sid,'points':n,'sampling':'uniform_t','file':'xyz/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
            old=c.read_bytes();result=e010_candidate_contract(atlas,{'records':records},r,e010,r)
            self.assertEqual(result['status'],'UNRESOLVED')
            self.assertEqual(c.read_bytes(),old)
            self.assertTrue((r/'G6P8_E010_CARRIER_INDEX_PROPOSAL.json').exists())

if __name__=='__main__':unittest.main()

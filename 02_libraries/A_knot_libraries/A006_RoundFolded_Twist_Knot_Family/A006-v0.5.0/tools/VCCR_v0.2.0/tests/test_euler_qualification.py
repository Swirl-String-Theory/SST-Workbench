"""Independent benchmark and broken-control regressions for VCCR v0.2.0."""
import copy,json,math,unittest
from pathlib import Path
from vccr.core import reference_trefoil
from vccr.euler_qualification import (euler_pde_residual,run_case,convergence,
                                     initial_markers,rk4,ring_measure,velocity)
from vccr.native_qualification import analyze

ROOT=Path(__file__).resolve().parents[1]
class EulerQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.circular=run_case(max_lambda=4.,steps_per_unit=200.,rings=4,markers=64)
        cls.elliptic=run_case(ellipse=1.6,max_lambda=2.,steps_per_unit=200.,rings=4,markers=64)

    def test_numerical_euler_momentum_divergence(self):
        for t in (0.,.5,1.73,3.46):
            d=euler_pde_residual(t)
            self.assertLess(d['momentum_linf'],1e-8)
            self.assertLess(d['divergence_linf'],1e-9)
            self.assertLess(d['pressure_poisson_linf'],1e-7)

    def test_independent_tracer_does_not_use_closure(self):
        import vccr.core as old
        old_function=old.state_from_length
        try:
            old.state_from_length=lambda *a,**k: (_ for _ in ()).throw(AssertionError('tracer illegally called closure'))
            actual=run_case(max_lambda=2.,steps_per_unit=200.,rings=3,markers=32)
            self.assertEqual(actual['gates']['independent_material_tracer'],'PASS')
        finally:old.state_from_length=old_function

    def test_length_radius_gamma_volume_analytic(self):
        rows={r['lambda_target']:r for r in self.circular['rows']}
        for lam in (1.,1.5,2.,4.):
            v=rows[lam]
            self.assertAlmostEqual(v['measured_radius_ratio'],lam**-.5,delta=5e-9)
            self.assertAlmostEqual(v['mean_vorticity_ratio'],lam,delta=1e-8)
            self.assertLess(v['volume_relative_error'],3e-9)
            self.assertLess(v['circulation_relative_error'],3e-9)
            self.assertLess(v['circulation_stokes_relative_error'],3e-10)

    def test_elliptic_area_equivalent_not_geom_core(self):
        self.assertEqual(self.elliptic['gates']['circular_core'],'NOT_APPLICABLE_ELLIPTIC')
        self.assertEqual(self.elliptic['gates']['independent_material_tracer'],'PASS')
        self.assertLess(self.elliptic['rows'][-1]['roundness'],.42)
        self.assertAlmostEqual(self.elliptic['rows'][-1]['measured_radius_ratio'],2**-.5,delta=1e-9)

    def test_broken_rotation_fails_euler_and_kelvin(self):
        broken=run_case(max_lambda=2.,steps_per_unit=200.,rings=3,markers=32,freeze_rotation=True)
        self.assertEqual(broken['gates']['euler_pde_residual'],'FAIL')
        self.assertEqual(broken['gates']['independent_material_tracer'],'FAIL')
        self.assertGreater(broken['rows'][-1]['circulation_relative_error'],.4)

    def test_temporal_order(self):
        c=convergence((25,50,100,200))
        err=[x['volume_relative_error'] for x in c]
        self.assertTrue(all(a>b for a,b in zip(err,err[1:])))
        for x,y in zip(err,err[1:]):self.assertGreater(x/y,12)

    def test_sst_calibration_only_not_benchmark_pressure(self):
        ref=reference_trefoil()
        self.assertAlmostEqual(ref.a_m,1.40897017e-15,delta=1e-27)
        self.assertAlmostEqual(ref.volume_m3,2.877218654223102e-43,delta=1e-55)
        self.assertAlmostEqual(ref.circulation_m2_s,9.683619203488876e-9,delta=1e-19)
        self.assertAlmostEqual(ref.mean_omega_s1,1.552689e21,delta=2e16)

    def test_native_synthetic_contract_measures_not_certifies(self):
        j=json.loads((ROOT/'examples'/'synthetic_native_contract_demo.json').read_text())
        r=analyze(j)
        self.assertEqual(r['gate_results']['GN2_radius_volume_circulation_measured'],'PASS')
        self.assertEqual(r['gate_results']['GN4_full_Euler_PDE_residual'],'NOT_RUN')
        self.assertEqual(r['note'],'SYNTHETIC_DEMO_NOT_NATIVE_SOLVER')

    def test_native_identity_corruption_detected(self):
        j=json.loads((ROOT/'examples'/'synthetic_native_contract_demo.json').read_text())
        j['frames'][1]['segments'][0]['material_marker_ids'][0]='nonmaterial-index'
        r=analyze(j)
        self.assertEqual(r['gate_results']['GN0_schema_and_material_ids'],'FAIL')
        self.assertEqual(r['gate_results']['GN2_radius_volume_circulation_measured'],'FAIL')

    def test_native_kelvin_corruption_detected(self):
        j=json.loads((ROOT/'examples'/'synthetic_native_contract_demo.json').read_text())
        v=j['frames'][1]['segments'][0]['ring_velocities_m_s']
        for x in v:x[0]*=1.25;x[1]*=1.25
        r=analyze(j)
        self.assertEqual(r['gate_results']['GN2_radius_volume_circulation_measured'],'FAIL')
        self.assertGreater(r['maxima']['circulation_relative'],.2)

    def test_native_reject_malformed(self):
        j=json.loads((ROOT/'examples'/'synthetic_native_contract_demo.json').read_text())
        j['frames'][1]['segments'][0]['ring_positions_m']=[]
        with self.assertRaises(ValueError):analyze(j)

if __name__=='__main__':unittest.main()

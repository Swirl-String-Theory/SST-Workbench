import pathlib,sys,unittest,math,tempfile,shutil
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from triadic import physics as p
from triadic import security as sec
from triadic.runner import run_d01,run_d02,run_d03,run_blind,reveal,verify_predictions_against_commit


def create_test_run(t):
    from unittest.mock import patch
    from triadic.provider_manifest import write_new
    for folder in ['data','seals','preregistration']:
        shutil.copytree(R/folder,t/folder)
    write_new(t)
    with patch.dict('os.environ',{'SST_A065_ISOLATED_RUN':'1'}):
        run_blind(t)

class AnalyticalTests(unittest.TestCase):
    def test_poisson_stagnation(self):
        z=p.euler_snapshot({'gradient':[[.4,0,0],[0,-.4,0],[0,0,0]],'rho':1,'c_star':3,'point':[.1,.2,0]})
        self.assertAlmostEqual(z['omega2'],0)
        self.assertAlmostEqual(z['strain2'],.32)
        self.assertAlmostEqual(z['pressure_laplacian'],-.32)
    def test_rotating_pressure(self):
        z=p.euler_snapshot({'gradient':[[0,-.3,0],[.3,0,0],[0,0,0]],'rho':1,'c_star':3,'point':[.1,.2,0]})
        self.assertAlmostEqual(z['pressure_laplacian'],.18)
        self.assertAlmostEqual(z['pressure_poisson_rhs'],.18)
    def test_analytic_force_gradient(self):
        ds=sec.readjson(R/'data'/'D02_CLOCK_LINK'/'single_surface.json')['surfaces']
        a=1.2;t=1.0
        x=p.pressure_traction(a,t,ds['A'],ds['B'],900)
        y=p.pressure_finite_diff(a,t,ds['A'],ds['B'],900)
        self.assertLess(abs(x-y)/abs(x),0.012)
    def test_swap_symmetry(self):
        ds=sec.readjson(R/'data'/'D02_CLOCK_LINK'/'single_surface.json')['surfaces']
        self.assertAlmostEqual(p.pressure_traction(1,1,ds['A'],ds['B'],900),p.pressure_traction(1,1,ds['B'],ds['A'],900),12)
    def test_temperature_scaling(self):
        ds=sec.readjson(R/'data'/'D02_CLOCK_LINK'/'single_surface.json')['surfaces']
        v=p.pressure_traction(1,.5,ds['A'],ds['B'],900)
        self.assertAlmostEqual(p.pressure_traction(1,1,ds['A'],ds['B'],900),2*v,12)
    def test_sheet_decouple(self):
        ds=sec.readjson(R/'data'/'D02_CLOCK_LINK'/'single_surface.json')['surfaces']
        self.assertEqual(p.free_energy_area(1,1,ds['A'],ds['C'],900),0.0)
    def test_gauge_and_holonomy(self):
        g=sec.readjson(R/'data'/'D02_CLOCK_LINK'/'single_surface.json')['graph']
        q=p.phase_path(g,[0,1,2]);self.assertAlmostEqual(q,p.phase_path(p.gauge_transform(g,[1,-1,.3]),[0,1,2]),12)
        self.assertAlmostEqual(p.phase_path_rate(g,[0,1,2]),p.direct_phase_rate(g,[0,1,2]),12)
    def test_dataset_seals(self):
        self.assertEqual(len(sec.verify_all(R)),3)
    def test_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp)
            shutil.copytree(R/'data',t/'data');shutil.copytree(R/'seals',t/'seals');
            sec.verify_all(t)
            (t/'data'/'D01_EULER'/'cases.json').write_text('{}')
            with self.assertRaises(RuntimeError):sec.verify_all(t)
    def test_blind_output_tampering_blocks_reveal(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp)
            create_test_run(t)
            verify_predictions_against_commit(t)
            p=t/'outputs'/'BLIND'/'D03_TWO_SURFACE.json'
            p.write_bytes(p.read_bytes()+b'\n')
            with self.assertRaises(RuntimeError):verify_predictions_against_commit(t)

    def test_absent_escrow_blocks_reveal(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp)
            create_test_run(t)
            with self.assertRaisesRegex(RuntimeError,'ESCROW'):
                reveal(t)

    def test_all_synthetic_gates(self):
        for f in (run_d01,run_d02,run_d03):
            d=f(R)
            fails=[g['gate'] for g in d['gates'] if g['status']=='FAIL']
            self.assertEqual(fails,['D01_G08_FILAMENT_SPATIAL_REFINEMENT','D01_G10_FILAMENT_SPATIAL_75_300'] if d['dataset_id']=='D01_EULER' else [],d['gates'])
            if d['dataset_id']=='D01_EULER':
                self.assertEqual(d['filament_dynamics']['spatial_pairs']['150_vs_300']['gate'],'PASS')

if __name__=='__main__': unittest.main()

class PKLSATests(unittest.TestCase):
    def test_real_source_300_points(self):
        from triadic.pklsa import bridge
        d=bridge(R)
        self.assertEqual(d['stats']['points'],300)
        self.assertEqual(d['source_provider_count'],1)
        self.assertLess(d['stats']['relative_segment_spread'],0.005)

    def test_real_source_geometry_convergence(self):
        from triadic.pklsa import bridge
        d=bridge(R)
        self.assertLess(d['max_refinement_error'],0.01)
        self.assertTrue(all(math.isfinite(x) for r in d['fields'] for x in r['velocity_300']))

    def test_no_external_latex_pdf_mandatory(self):
        from triadic.report_pdf import _pdf_text
        with tempfile.TemporaryDirectory() as t:
            z=pathlib.Path(t)/'r.pdf'
            n=_pdf_text(z,[('h1','PDF fallback works without optional tools')]+[('normal','test row %s with stable fallback bytes and no LaTeX dependency'%i) for i in range(25)])
            self.assertGreaterEqual(n,1)
            self.assertIn(b'%PDF-1.4',z.read_bytes()[:30])
            self.assertGreater(z.stat().st_size,1000)

    def test_one_geometry_provider_not_certified(self):
        d=run_d01(R)
        self.assertIn('SECOND_PROVIDER_DYNAMICS_REQUIRED',d['open_qualifications'])
        self.assertNotEqual(d['pklsa']['physics_status'],'PHYSICAL_CERTIFIED')

class PKLSATamperTest(unittest.TestCase):
    def test_pklsa_source_byte_tamper_blocks_all(self):
        with tempfile.TemporaryDirectory() as t:
            t=pathlib.Path(t)
            for name in ('data','seals'):
                shutil.copytree(R/name,t/name)
            sec.verify_all(t)
            raw=t/'data'/'D01_EULER'/'pklsa'/'trefoil_KnotPlot_relaxed_N300.txt'
            raw.write_bytes(raw.read_bytes()+b'\n')
            with self.assertRaises(RuntimeError):sec.verify_all(t)

class DynamicsAndProvenanceTests(unittest.TestCase):
    def test_filament_rk4_dt_halving(self):
        from triadic.dynamics import run
        d=run(R)
        self.assertEqual(d['numerical_gate'],'PASS',d)
        self.assertGreater(d['rms_displacement'],0)
        self.assertGreater(d['rms_coarse_fine_difference'],0)
    def test_provider_is_not_fake_replicate(self):
        from triadic.providers import check
        d=check(R,raw_override=R/'imports'/'not_supplied.short')
        self.assertEqual(d['status'],'UNRESOLVED_SOURCE_MISSING')
        self.assertEqual(d['independence_group'],'fremlin:3_1')
    def test_provider_wrong_hash_fail_closed(self):
        from triadic.providers import check
        with tempfile.TemporaryDirectory() as t:
            f=pathlib.Path(t)/'bad.short'; f.write_text('0 0 0\n1 0 0\n')
            self.assertEqual(check(R,raw_override=f)['status'],'FAIL_RAW_HASH_MISMATCH')

class StrictRevealTests(unittest.TestCase):
    def test_tampered_escrow_rejected_before_physical_reveal(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=pathlib.Path(td)
            create_test_run(tmp)
            (tmp/'private_reveal').mkdir()
            (tmp/'private_reveal'/'targets.json').write_text('{"forged":"target"}')
            with self.assertRaisesRegex(RuntimeError,'private target commitment mismatch'):
                reveal(tmp)

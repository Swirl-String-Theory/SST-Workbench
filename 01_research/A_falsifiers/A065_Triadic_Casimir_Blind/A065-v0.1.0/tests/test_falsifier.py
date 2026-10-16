import pathlib,sys,unittest,math,tempfile,shutil
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from triadic import physics as p
from triadic import security as sec
from triadic.runner import run_d01,run_d02,run_d03,run_blind,reveal,verify_predictions_against_commit

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
            shutil.copytree(R/'data',t/'data');shutil.copytree(R/'seals',t/'seals');shutil.copytree(R/'private_reveal',t/'private_reveal')
            sec.verify_all(t)
            (t/'data'/'D01_EULER'/'cases.json').write_text('{}')
            with self.assertRaises(RuntimeError):sec.verify_all(t)
    def test_blind_output_tampering_blocks_reveal(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp)
            for folder in ['data','seals','private_reveal','outputs']:
                shutil.copytree(R/folder,t/folder)
            verify_predictions_against_commit(t)
            p=t/'outputs'/'BLIND'/'D03_TWO_SURFACE.json'
            p.write_bytes(p.read_bytes()+b'\n')
            with self.assertRaises(RuntimeError):verify_predictions_against_commit(t)

    def test_target_tampering_blocks_reveal(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp)
            for folder in ['data','seals','private_reveal','outputs']:
                shutil.copytree(R/folder,t/folder)
            p=t/'private_reveal'/'targets.json'
            p.write_bytes(p.read_bytes()+b'\n')
            with self.assertRaises(RuntimeError):verify_predictions_against_commit(t)

    def test_all_synthetic_gates(self):
        for f in (run_d01,run_d02,run_d03):
            d=f(R)
            self.assertTrue(all(g['status']=='PASS' for g in d['gates']),d['gates'])

if __name__=='__main__': unittest.main()

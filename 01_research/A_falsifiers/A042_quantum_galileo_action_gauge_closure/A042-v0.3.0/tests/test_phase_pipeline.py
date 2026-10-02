import csv, math, tempfile, unittest
from pathlib import Path
import numpy as np
from sst_qgi.phase_data import reconstruct_phase_from_population, specific_action_from_cubic

class PhasePipelineTests(unittest.TestCase):
    def test_specific_action_formula(self):
        g=9.91
        c3=7.0e9
        r=specific_action_from_cubic(c3,g)
        self.assertAlmostEqual(r["hbar_over_m_m2_s"],g*g/(24*c3))
        self.assertAlmostEqual(r["h_over_m_m2_s"],math.pi*g*g/(12*c3))
        self.assertFalse(r["mass_used"])
        self.assertFalse(r["planck_target_used"])

    def test_raw_population_reconstruction(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            p=td/"raw.csv"
            t=np.linspace(0.00030,0.00240,633)
            c=np.array([0.3,2.0e3,-2.0e6,7.0e9])
            phi=sum(c[k]*t**k for k in range(4))
            mean=0.50+0.015*(t-t.mean())/np.ptp(t)
            vis=0.78-0.56*(t-t.min())/np.ptp(t)
            pop=mean+0.5*vis*np.cos(phi)
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.writer(f)
                w.writerow(["twoT_s","population_outport1","sem_population"])
                for ti,yi in zip(t,pop):
                    w.writerow([ti,yi,0.005])
            r=reconstruct_phase_from_population(p,td/"out")
            self.assertEqual(r["source_grade"],"RAW_POPULATION_CSV")
            self.assertLess(abs(r["cubic_coeff_rad_s3_inv"]/c[3]-1.0),0.06)

if __name__=="__main__":
    unittest.main()

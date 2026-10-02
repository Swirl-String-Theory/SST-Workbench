import csv, json, math, tempfile, unittest
from pathlib import Path
from sst_qgi.fluid_data import compute_circulation_from_loop, prepare_fluid_measurement

class FluidDataTests(unittest.TestCase):
    def test_circular_loop_integral(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"loop.csv"
            n=2048
            R=0.02
            Omega=3.0
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.writer(f)
                w.writerow(["x_m","y_m","z_m","vx_m_s","vy_m_s","vz_m_s"])
                for i in range(n):
                    th=2*math.pi*i/n
                    x=R*math.cos(th); y=R*math.sin(th)
                    vx=-Omega*y; vy=Omega*x
                    w.writerow([x,y,0.0,vx,vy,0.0])
            r=compute_circulation_from_loop(p)
            expected=2*math.pi*Omega*R*R
            self.assertLess(abs(r["Gamma_m2_s"]/expected-1.0),5e-6)

    def test_provenance_clean(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            loop=td/"loop.csv"
            with loop.open("w",newline="",encoding="utf-8") as f:
                w=csv.writer(f); w.writerow(["x_m","y_m","z_m","vx_m_s","vy_m_s","vz_m_s"])
                n=64; R=1.0; Omega=1.0
                for i in range(n):
                    th=2*math.pi*i/n
                    x=R*math.cos(th); y=R*math.sin(th)
                    w.writerow([x,y,0,-Omega*y,Omega*x,0])
            prov=td/"prov.json"
            prov.write_text(json.dumps({
                "measurement_id":"test","status":"INDEPENDENT_MEASURED",
                "method":"synthetic unit test","source":"unit test",
                "depends_on_h":False,"depends_on_hbar":False,
                "depends_on_compton_radius":False,
                "depends_on_electron_mass":False,"depends_on_alpha":False
            }),encoding="utf-8")
            out=td/"out.json"
            r=prepare_fluid_measurement(loop,prov,out)
            self.assertTrue(r["clean_for_specific_action"])

if __name__=="__main__":
    unittest.main()

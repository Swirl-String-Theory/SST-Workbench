
from __future__ import annotations
import csv, math, random, sys
from pathlib import Path

H=6.62607015e-34

def action(path, plancklike=True):
    rng=random.Random(42)
    rows=[]
    for i in range(24):
        f=1.0e20*(1+0.08*i)
        if plancklike:
            dE=H*f*(1+rng.gauss(0,0.008))
        else:
            amp=0.5+0.06*i
            dE=2.3e-14*amp*amp*(1+rng.gauss(0,0.01))
        rows.append({
            "carrier_id":f"C{i%4}",
            "family":["trefoil","figure8","torus","control"][i%4],
            "mode_label":f"m{i%6}",
            "condition":"synthetic_control",
            "profile":"demo",
            "seed_name":f"s{i}",
            "frequency_Hz":f,
            "omega_rad_s":2*math.pi*f,
            "delta_E_J":dE
        })
    write(path,rows)

def closure(path, good=True):
    rng=random.Random(7)
    rows=[]
    base_omega=2.0e6
    for i in range(20):
        a=0.8+0.04*i
        omega=base_omega/a**2*(1+rng.gauss(0,0.005 if good else 0.15))
        MI=9.1e-31*(1+0.02*(i%3))
        ME=MI*(1+rng.gauss(0,0.01 if good else 0.12))
        kappa=3.2e15
        Cp=kappa*MI*(1+rng.gauss(0,0.01 if good else 0.2))
        bk=1.0e33*(1+rng.gauss(0,0.01))
        bf=bk*(1+rng.gauss(0,0.01 if good else 0.2))
        drift=rng.gauss(0,2e-7 if good else 5e-5)
        rows.append({
            "scale_a":a,"omega_rad_s":omega,"M_E_kg":ME,"M_I_kg":MI,
            "C_p":Cp,"beta_knot":bk,"beta_fluid":bf,"energy_drift_rel":drift
        })
    write(path,rows)

def write(path,rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: python -m sst_wp.synthetic_controls action-positive|action-negative|closure-positive|closure-negative OUT.csv")
    mode,out=sys.argv[1:]
    if mode=="action-positive": action(out,True)
    elif mode=="action-negative": action(out,False)
    elif mode=="closure-positive": closure(out,True)
    elif mode=="closure-negative": closure(out,False)
    else: raise SystemExit("unknown mode")

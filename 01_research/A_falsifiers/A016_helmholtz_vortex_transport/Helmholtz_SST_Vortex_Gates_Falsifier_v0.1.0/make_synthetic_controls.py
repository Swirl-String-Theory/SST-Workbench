from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from helmholtz_sst.metrics import total_velocity,relative_equilibrium,holonomy_metrics

def circle(n=192,R=2.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[R*np.cos(t),R*np.sin(t),np.zeros(n)]
def perturbed(n=192,R=2.0,eps=.18):
    t=np.linspace(0,2*np.pi,n,endpoint=False);r=R*(1+eps*np.cos(3*t));return np.c_[r*np.cos(t),r*np.sin(t),.12*np.sin(2*t)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path('synthetic_controls'));a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);ring=circle();bad=perturbed();core=.15
    rr=relative_equilibrium([ring],total_velocity([ring],core,'softcore',0));rb=relative_equilibrium([bad],total_velocity([bad],core,'softcore',0));hol=holonomy_metrics([ring],.4,3,128,.25,0);obj={'ring_re':rr,'perturbed_re':rb,'holonomy':hol};(a.out/'controls.json').write_text(json.dumps(obj,indent=2)+'\n');print(json.dumps(obj,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

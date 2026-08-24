from pathlib import Path
import json,tempfile
import numpy as np
import generate_seeds as gs
from geometry_utils import resample_closed,min_nonlocal_clearance,hash_resampled,kabsch_rms

ROOT=Path(__file__).resolve().parents[1]

def synthetic_trefoil(n=300):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    R=3.0; r=1.0
    # Standard (2,3) torus trefoil.
    return np.c_[
        (R+r*np.cos(3*t))*np.cos(2*t),
        (R+r*np.cos(3*t))*np.sin(2*t),
        r*np.sin(3*t)
    ]

def main():
    man=json.loads((ROOT/"seed_manifest.json").read_text())
    assert man["n_seeds"]==38
    x=resample_closed(synthetic_trefoil(),300)
    d0=min_nonlocal_clearance(x,400,5)
    assert d0>0
    hashes=[]
    for spec in man["seeds"]:
        y=gs.build_seed(x,spec,d0)
        ok,d1,mh,u=gs.check_homotopy(x,y,d0)
        if not ok:
            raise AssertionError(f"synthetic safety failed for {spec['seed_id']}: d1={d1/d0}, mh={mh/d0}")
        hashes.append(hash_resampled(y,128))
    assert len(set(hashes))==38
    assert kabsch_rms(x,x)<1e-12
    print("SELFTEST PASS: 38 preregistered seeds safe+unique on synthetic trefoil")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

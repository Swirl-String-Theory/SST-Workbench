from pathlib import Path
import json
import numpy as np
from sst_vortex_shear import reference, backend
from sst_vortex_shear.sampling import paired_transverse_samples, shear_matrix
from sst_vortex_shear.filaments import hopf_cell, filament_energy_python

if backend.backend_name() != "native":
    raise SystemExit("SST_BACKEND=native is required for parity qualification")
ROOT = Path(__file__).resolve().parent
BLIND = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs" / "BLIND"
CFG = json.loads((ROOT/"configs"/"default.json").read_text(encoding="utf-8"))
tol = float(CFG["tolerances"]["backend_parity_max_abs"])

n,w,_,_,_ = paired_transverse_samples(1000)
errs=[]
for g in (0.007,0.031,0.071):
    f=shear_matrix(g,"xy")
    errs.append(abs(reference.energy_ratio_general(n,w,f)-backend.energy_ratio_general(n,w,f)))
rng=np.random.default_rng(77)
a=rng.normal(size=(2048,3)); b=rng.normal(size=(2048,3))
errs.append(float(np.max(np.abs(np.cross(a,b)-backend.cross_product(a,b)))))
h=hopf_cell(1.0,24,True)
errs.append(abs(filament_energy_python(h,[1.0,1.0],0.18)-backend.filament_energy(h,[1.0,1.0],0.18)))
maxerr=max(errs)
result={"status":"PASS" if maxerr<=tol else "FAIL","tolerance_max_abs":tol,"max_abs":maxerr,"cases":len(errs)}
(BLIND/"backend_parity_summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
if result["status"] != "PASS": raise SystemExit(1)

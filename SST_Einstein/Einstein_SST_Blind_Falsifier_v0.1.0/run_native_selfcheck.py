from __future__ import annotations
import json, numpy as np
from sst_einstein import native, reference
from sst_einstein.geometry import kelvin_ring

native.require_native(); native.set_threads(None)
p=kelvin_ring(28,1.0,0.03,2,0.2,True); core=0.08; u=np.array([0.07,-0.03,0.02])
checks={}
def rel(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float);return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
checks["velocity_rel"]=rel(native.biot_savart_velocity(p,core,1.0,u),reference.biot_savart_velocity(p,core,1.0,u))
checks["energy_rel"]=abs(native.filament_energy(p,core)-reference.filament_energy(p,core))/abs(reference.filament_energy(p,core))
checks["impulse_rel"]=rel(native.impulse(p),reference.impulse(p))
checks["curvature_rel"]=rel(native.curvature(p),reference.curvature(p))
checks["rk4_rel"]=rel(native.rk4_step(p,0.003,core,1.0,u),reference.rk4_step(p,0.003,core,1.0,u))
tol=2e-11
ok=all(v<=tol for v in checks.values())
print(json.dumps({"backend":native.backend_name(),"checks":checks,"tolerance":tol,"PASS":ok},indent=2))
raise SystemExit(0 if ok else 3)

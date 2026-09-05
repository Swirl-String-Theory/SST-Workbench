from pathlib import Path
import sys, numpy as np
sys.path.insert(0,str(Path(__file__).parent/'src'))
import sst_phase_delay_falsifier.backend as B
if B.BACKEND != "cpp":
    raise SystemExit("ERROR: native C++ backend is not loaded")
t=np.linspace(0,2*np.pi,32,endpoint=False)
x=np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]
core=.08
vcpp=B.biot_savart_velocity(x,1.0,core)
vpy=B._vel_py(x,1.0,core)
rel=np.linalg.norm(vcpp-vpy)/max(np.linalg.norm(vpy),1e-300)
print(f"native/python velocity relative error = {rel:.3e}")
if not np.isfinite(rel) or rel>1e-12:
    raise SystemExit(2)
print("NATIVE PARITY PASS")

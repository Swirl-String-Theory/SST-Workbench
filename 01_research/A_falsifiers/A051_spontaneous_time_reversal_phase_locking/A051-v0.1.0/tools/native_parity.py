import numpy as np
from sst_trpl.synthetic import integrate as py_integrate
try:
    import sst_trpl_native as native
except Exception as e:
    raise SystemExit(f"SKIP native backend unavailable: {e}")
for phi0,p0 in [(1.3,0.1),(-1.4,-0.05),(0.8,0.2)]:
    t,ph,p=py_integrate(phi0,p0,1.0,0.005,2000)
    nph,np_=native.integrate(phi0,p0,1.0,0.005,2000)
    err=max(float(np.max(np.abs(ph-nph))),float(np.max(np.abs(p-np_))))
    print(phi0,p0,err)
    if err>5e-12: raise SystemExit(2)
print('NATIVE_PARITY PASS')

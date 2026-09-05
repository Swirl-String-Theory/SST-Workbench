from __future__ import annotations
import json, os
import numpy as np
from native_ext.sycl_worker import worker_info, biot_savart, shutdown_worker
from native_ext.fallback import biot_savart as host_biot

def main():
    os.environ['SST_SYCL_ALLOW_FP32']='1'
    t=np.linspace(0,2*np.pi,96,endpoint=False);p=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    info=worker_info(start=True);print(json.dumps(info,indent=2))
    vg,label=biot_savart(p,p,gamma=1.0,core=0.05)
    vh=host_biot(p,p,1.0,0.05)
    denom=max(float(np.linalg.norm(vh)),1e-30)
    rel=float(np.linalg.norm(vg-vh)/denom);mx=float(np.max(np.abs(vg-vh)))
    finite=bool(np.all(np.isfinite(vg)))
    out={'backend':label,'finite':finite,'relative_l2_vs_python_fp64':rel,'max_abs_vs_python_fp64':mx,'shape':list(vg.shape)}
    print(json.dumps(out,indent=2));shutdown_worker()
    return 0 if finite and rel<5e-4 else 2
if __name__=='__main__': raise SystemExit(main())

from __future__ import annotations
import argparse, json, numpy as np
from sst_thread_falsifier.native_ext import fallback
from sst_thread_falsifier.native_ext.core import biot_savart, backend_name
from sst_thread_falsifier.geometry import kabsch_rms, radius_gyration


def trefoil(n=160):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    p=np.c_[np.sin(t)+2*np.sin(2*t), np.cos(t)-2*np.cos(2*t), -np.sin(3*t)]
    return p.astype(float)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--require-native",action="store_true"); ap.add_argument("--tol",type=float,default=5e-10)
    a=ap.parse_args(); P=trefoil(); O=np.array([0,len(P)],dtype=np.int64); rg=radius_gyration(P); core=0.06
    py=fallback.biot_savart(P,O,1.0,core)
    cpp=biot_savart(P,O,1.0,core,skip_build=True)
    be=backend_name(); denom=max(float(np.linalg.norm(py)),1e-15); rel=float(np.linalg.norm(cpp-py)/denom)
    U=np.array([0.31,-0.27,0.19]); dt=0.01
    x0=P+dt*cpp; xb=P+dt*(cpp+U)
    boost_rms=kabsch_rms(x0,xb)/rg
    ok=(rel<=a.tol and boost_rms<=a.tol and (be=="cpp" or not a.require_native))
    print(json.dumps({"backend":be,"native_vs_python_relative_l2":rel,"uniform_boost_shape_rms_over_rg":boost_rms,"tol":a.tol,"status":"PASS" if ok else "FAIL"},indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=="__main__": main()

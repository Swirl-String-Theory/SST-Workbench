#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
from native_ext import load_backend
from native_ext import fallback
from sst6.geometry import pack_components
from sst6.io import write_json

ROOT=Path(__file__).resolve().parent

def rel(a,b): return float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(np.linalg.norm(np.asarray(b)),1e-15))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="outputs/native_audit.json"); ap.add_argument("--strict",action="store_true"); args=ap.parse_args()
    native,name=load_backend(force_python=False,force_build=False,build_verbose=True)
    th=np.linspace(0,2*math.pi,96,endpoint=False); c=np.column_stack([3*np.cos(th),3*np.sin(th),np.zeros_like(th)]); v,o=pack_components([c]); q=np.array([[0,0,0],[4,0,0],[0,0,2]],float)
    checks={}
    if name=="cpp":
        checks["velocity_rel"]=rel(native.biot_savart_velocity(q,v,o,2*math.pi,1),fallback.biot_savart_velocity(q,v,o,2*math.pi,1))
        checks["energy_rel"]=abs(native.regularized_energy(v,o,1,2*math.pi,1)-fallback.regularized_energy(v,o,1,2*math.pi,1))/max(abs(fallback.regularized_energy(v,o,1,2*math.pi,1)),1e-15)
        checks["writhe_abs"]=abs(native.gauss_writhe_component(v,o,0))
        checks["contacts_count"]=len(native.nearest_segment_contacts(v,o,3,8))
    ok=(name=="cpp" and checks.get("velocity_rel",1)<1e-11 and checks.get("energy_rel",1)<1e-11 and checks.get("writhe_abs",1)<2e-3)
    data={"backend":name,"checks":checks,"ok":ok}
    out=Path(args.out); out=out if out.is_absolute() else ROOT/out; write_json(out,data); print(json.dumps(data,indent=2))
    if args.strict and not ok: return 2
    return 0
if __name__=="__main__": raise SystemExit(main())

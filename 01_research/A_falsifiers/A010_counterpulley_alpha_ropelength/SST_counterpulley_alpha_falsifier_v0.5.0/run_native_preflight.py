#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, platform, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
from sst_counterpulley import fallback
from sst_counterpulley.backend import load_backend
from sst_counterpulley._config import CPP_REL

def main()->int:
    ap=argparse.ArgumentParser(description="Build/import native kernel and parity-check pair dynamics.")
    ap.add_argument("--force-build",action="store_true"); ap.add_argument("--allow-python",action="store_true"); ap.add_argument("--verbose",action="store_true")
    a=ap.parse_args(); backend,name=load_backend(force_build=a.force_build,build_verbose=a.verbose)
    t=np.linspace(0,2*np.pi,24,endpoint=False); p=np.column_stack((np.cos(t),np.sin(t),.15*np.sin(2*t))); m=p+np.array([.17,-.09,.11]); eps=.07
    py=fallback.pair_rhs(p,m,1.0,-1.0,eps); got=np.asarray(backend.pair_rhs(p,m,1.0,-1.0,eps) if hasattr(backend,'pair_rhs') else py)
    rel=float(np.linalg.norm(got-py)/max(np.linalg.norm(py),1e-30)); src=(ROOT/CPP_REL).read_bytes()
    result={"ok":bool(rel<1e-11 and (name=="cpp" or a.allow_python)),"backend":name,"interpreter":sys.executable,"python":sys.version,"platform":platform.platform(),"source_hash":hashlib.sha256(src).hexdigest(),"pair_rhs_relative_error":rel,"native_required":not a.allow_python}
    print(json.dumps(result,indent=2)); return 0 if result["ok"] else 1
if __name__=="__main__": raise SystemExit(main())

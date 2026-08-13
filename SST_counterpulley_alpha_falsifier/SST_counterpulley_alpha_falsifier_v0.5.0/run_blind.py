#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from sst_counterpulley.core import DEFAULT_DATA
from sst_counterpulley.blind_gates import run_blind_gates

def main()->int:
    ap=argparse.ArgumentParser(description="Run v0.5 H0-H18: Newton-Krylov RPO first, true Floquet second, alpha closed.")
    ap.add_argument("--data",default=str(DEFAULT_DATA)); ap.add_argument("--out-dir",default="audit_out_blind")
    ap.add_argument("--force-python",action="store_true"); ap.add_argument("--force-build",action="store_true")
    ap.add_argument("--build-verbose",action="store_true"); ap.add_argument("--quick",action="store_true")
    a=ap.parse_args(); s=run_blind_gates(out_dir=a.out_dir,data_path=a.data,force_python=a.force_python,
        force_build=a.force_build,build_verbose=a.build_verbose,quick=a.quick)
    print(json.dumps(s,indent=2)); return 2 if s["verdict"].startswith("INCONCLUSIVE") else 0
if __name__=="__main__": raise SystemExit(main())

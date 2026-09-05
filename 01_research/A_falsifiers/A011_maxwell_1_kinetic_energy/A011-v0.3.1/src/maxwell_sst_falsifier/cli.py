from __future__ import annotations
import argparse, json
from pathlib import Path
from .campaign import run_campaign, save_campaign
from .native_ext import backend_info, require_native
from .workflow import run_workflow


def main()->int:
    p=argparse.ArgumentParser(prog="sst-maxwell-falsify",description="Maxwell-SST Kinetic Falsifier v0.3.1")
    sub=p.add_subparsers(dest="cmd",required=True)

    b=sub.add_parser("backend",help="Report native C++ / Python backend")
    b.add_argument("--force-build",action="store_true")
    b.add_argument("--require-native",action="store_true",help="Exit nonzero unless the C++ backend is active")

    w=sub.add_parser("workflow",help="Run solver-facing geometry/mode/coupling-proxy workflow")
    w.add_argument("--knots-dir",required=True,type=Path)
    w.add_argument("--out",required=True,type=Path)
    w.add_argument("--preset",choices=["basic","extended"],default="basic")
    w.add_argument("--threads",type=int,default=1)
    w.add_argument("--pairing",choices=["self","unique","all"],default=None)
    w.add_argument("--require-native",action="store_true")
    w.add_argument("--max-files",type=int,default=None)

    r=sub.add_parser("run",help="Run strict v0.1-compatible physical falsifier campaign")
    r.add_argument("--config",required=True,type=Path); r.add_argument("--out",required=True,type=Path)

    a=p.parse_args()
    try:
        if a.cmd=="backend":
            info = require_native(force_build=a.force_build, verbose=True) if a.require_native else backend_info(force_build=a.force_build,verbose=True)
            print(json.dumps(info,indent=2)); return 0
        if a.cmd=="workflow":
            result=run_workflow(a.knots_dir,a.out,a.preset,max(1,a.threads),a.pairing,a.require_native,a.max_files)
            print(json.dumps(result,indent=2)); return 0
        if a.cmd=="run":
            result=run_campaign(a.config); save_campaign(result,a.out); print(result["overall_verdict"]); print(a.out/"report.md"); return 0
        return 2
    except Exception as exc:
        print(f"[1_MaxwellSST ERROR] {exc}")
        return 1
if __name__=="__main__": raise SystemExit(main())

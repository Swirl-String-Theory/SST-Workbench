from __future__ import annotations
import argparse
from pathlib import Path
from sst_kelvin_workbench.phases import run_all


def main() -> int:
    ap=argparse.ArgumentParser(description="Run all four SST Kelvin/Floquet workbench phases.")
    ap.add_argument("--preset",choices=["quick","full"],default="quick")
    ap.add_argument("--out-dir",default="audit_out")
    ap.add_argument("--force-python",action="store_true")
    ap.add_argument("--force-build",action="store_true")
    args=ap.parse_args()
    s=run_all(Path(args.out_dir),preset=args.preset,force_python=args.force_python,force_build=args.force_build)
    print("SST Kelvin/Floquet Workbench",s["version"],args.preset)
    for k,v in sorted(s["gate_statuses"].items()): print(f"{k}: {v}")
    print(Path(args.out_dir).resolve())
    return 2 if s["hard_failures"] else 0

if __name__=="__main__": raise SystemExit(main())

from __future__ import annotations
import argparse
import json
from pathlib import Path
from sst_kelvin_workbench.phases import run_phase5


def main() -> int:
    ap=argparse.ArgumentParser(description="Run C006 Phase V spectral/Darboux certification.")
    ap.add_argument("--preset",choices=["quick","full"],default="quick")
    ap.add_argument("--out-dir",default="audit_out/phase5")
    ap.add_argument("--phase2-summary",default="audit_out/phase2/phase2_summary.json")
    ap.add_argument("--force-python",action="store_true")
    args=ap.parse_args()
    p2p=Path(args.phase2_summary)
    p2=json.loads(p2p.read_text(encoding="utf-8")) if p2p.is_file() else {"gates":{"K6":{"status":"SKIP"}}}
    result=run_phase5(Path(args.out_dir),p2,preset=args.preset,force_python=args.force_python)
    print(json.dumps(result["gates"],indent=2))
    return 2 if any(v.get("status")=="FAIL" for v in result["gates"].values()) else 0

if __name__=="__main__": raise SystemExit(main())

from __future__ import annotations
import argparse,json,shutil,time
from pathlib import Path
from sst_thread_falsifier.campaign import run_full


def main():
    ap=argparse.ArgumentParser(description="SST v0.3.0 explicit closed vortex-thread blind falsifier (exact segment + RK4)")
    ap.add_argument("--config",default="config/basic.json")
    ap.add_argument("--dataset",default=r"..\..\KnotPlot\knots\final")
    ap.add_argument("--out",default=None)
    ap.add_argument("--force-python",action="store_true")
    ap.add_argument("--skip-build",action="store_true")
    ap.add_argument("--overwrite",action="store_true")
    a=ap.parse_args()
    out=Path(a.out or f"outputs_{Path(a.config).stem}_{time.strftime('%Y%m%d_%H%M%S')}")
    if out.exists() and a.overwrite: shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)
    report=run_full(a.config,a.dataset,out,a.force_python,a.skip_build)
    print(json.dumps({"out":str(out),"overall_structural_status":report["overall_structural_status"],
                      "overall_conditional_bridge_status":report["overall_conditional_bridge_status"],
                      "scientific_classification":report["scientific_classification"],"datasets":len(report["datasets"])},indent=2))
    raise SystemExit(0 if report["overall_structural_status"]=="PASS" else 2)
if __name__=="__main__": main()

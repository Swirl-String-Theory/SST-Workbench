#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from sst_counterpulley.core import DEFAULT_DATA,write_json
from sst_counterpulley.blind_gates import run_blind_gates

def main()->int:
    ap=argparse.ArgumentParser(description="Run v0.5 blind Newton-Krylov RPO/Floquet gates; unblind only when H18 passes.")
    ap.add_argument("--data",default=str(DEFAULT_DATA)); ap.add_argument("--out-dir",default="audit_out")
    ap.add_argument("--force-python",action="store_true"); ap.add_argument("--force-build",action="store_true")
    ap.add_argument("--build-verbose",action="store_true"); ap.add_argument("--quick",action="store_true")
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    blind=run_blind_gates(out_dir=out,data_path=a.data,force_python=a.force_python,force_build=a.force_build,
                          build_verbose=a.build_verbose,quick=a.quick)
    if blind.get("ready_for_alpha_unblinding"):
        from sst_counterpulley.benchmark import benchmark_blind_summary
        post=benchmark_blind_summary(blind); write_json(out/"posthoc_alpha_benchmark.json",post)
    else:
        post={"benchmark_phase":"NOT_IMPORTED_OR_OPENED","alpha_value_opened":False,"reason":"H18 is closed."}
        write_json(out/"posthoc_alpha_benchmark.json",post)
    combined={"audit_name":"SST counter-pulley Newton-Krylov RPO + true Floquet falsifier v0.5.0","blind_verdict":blind["verdict"],
              "posthoc_verdict":post.get("verdict",post["benchmark_phase"]),"blind":blind,"posthoc":post}
    write_json(out/"audit_summary.json",combined); print(json.dumps(combined,indent=2)); return 2 if blind["verdict"].startswith("INCONCLUSIVE") else 0
if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from sst_counterpulley.core import write_json


def main()->int:
    ap=argparse.ArgumentParser(description="Open alpha only if archived v0.5 H18 permits it.")
    ap.add_argument("blind_summary"); ap.add_argument("--out",default="audit_out_blind/posthoc_alpha_benchmark.json")
    ap.add_argument("--diagnostic-override",action="store_true",help="Explicitly violate the scientific gate for diagnostics only.")
    a=ap.parse_args(); src=json.loads(Path(a.blind_summary).read_text(encoding="utf-8"))
    ready=bool(src.get("ready_for_alpha_unblinding",False))
    if not ready and not a.diagnostic_override:
        # Deliberately do NOT import sst_counterpulley.benchmark here: the alpha
        # numerical target therefore never enters this process when H18 is closed.
        r={"benchmark_phase":"BLOCKED_BY_BLIND_RPO_FLOQUET_GATES","alpha_value_opened":False,
           "blind_verdict":src.get("verdict"),"reason":"H18 is closed; benchmark module not imported."}
    else:
        from sst_counterpulley.benchmark import benchmark_blind_summary
        r=benchmark_blind_summary(src,diagnostic_override=a.diagnostic_override)
    write_json(a.out,r); print(json.dumps(r,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())

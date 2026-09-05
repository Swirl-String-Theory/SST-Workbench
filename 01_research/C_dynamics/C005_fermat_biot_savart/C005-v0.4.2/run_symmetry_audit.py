#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.certification import symmetry_audit


def main()->int:
    p=argparse.ArgumentParser(description="Audit rigid-motion, reindexing, orientation and mirror covariance.")
    p.add_argument("--knots",nargs="+",default=list(DEFAULT_KNOT_IDS)); p.add_argument("--epsilon",type=float,default=0.0019)
    p.add_argument("--centerline-points",type=int,default=4096); p.add_argument("--scale-over-rc",type=float,default=1.0)
    p.add_argument("--force-python",action="store_true"); p.add_argument("--no-auto-build",action="store_true")
    p.add_argument("--require-native",action="store_true"); p.add_argument("--out-dir",default="symmetry_audit")
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    results={}; rows=[]
    for i,k in enumerate(a.knots):
        r=symmetry_audit(k,epsilon=a.epsilon,centerline_points=a.centerline_points,scale_over_rc=a.scale_over_rc,
                         force_python=a.force_python,auto_build=(not a.no_auto_build) if i==0 else False)
        results[k]=r; write_json(out/f"{k}.json",r)
        rows.append({"knot_id":k,"backend":r["backend"]["backend"],"passed":r["passed"],
                     "max_beta_covariance_linf_error":r["max_beta_covariance_linf_error"],
                     "max_jacobian_covariance_linf_error":r["max_jacobian_covariance_linf_error"]})
    matrix={"schema":"sst.fermat.symmetry-matrix.v0.4.2","rows":rows,"results":results,
            "global_closed_orbit_certified":False,"qsm_certified":False}
    write_json(out/"symmetry_audit.json",matrix)
    native_all=all(r["backend"]=="cpp" for r in rows); passed=all(r["passed"] for r in rows)
    ok=passed and (native_all if a.require_native else True)
    print(json.dumps({"ok":ok,"native_all":native_all,"rows":rows},indent=2)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())

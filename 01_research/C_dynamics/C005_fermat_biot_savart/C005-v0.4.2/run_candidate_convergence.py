#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.certification import build_convergence_matrix


def main()->int:
    p=argparse.ArgumentParser(description="Certify radial minimum branches across three or more centerline resolutions.")
    p.add_argument("--knots",nargs="+",default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon",type=float,default=0.0019)
    p.add_argument("--point-counts",nargs="+",type=int,default=[4096,8192,16384])
    p.add_argument("--scale-over-rc",type=float,default=1.0)
    p.add_argument("--stations",type=int,default=8); p.add_argument("--angles",type=int,default=16)
    p.add_argument("--rho-min",type=float,default=0.0005); p.add_argument("--rho-max",type=float,default=0.03)
    p.add_argument("--bracket-samples",type=int,default=96)
    p.add_argument("--relative-tolerance",type=float,default=1e-3)
    p.add_argument("--strong-relative-tolerance",type=float,default=1e-4)
    p.add_argument("--reach-pair-points",type=int,default=1024)
    p.add_argument("--force-python",action="store_true"); p.add_argument("--no-auto-build",action="store_true")
    p.add_argument("--require-native",action="store_true"); p.add_argument("--out-dir",default="convergence_report")
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    matrix=build_convergence_matrix(
        a.knots,epsilon=a.epsilon,point_counts=a.point_counts,
        relative_tolerance=a.relative_tolerance,strong_relative_tolerance=a.strong_relative_tolerance,
        scale_over_rc=a.scale_over_rc,stations=a.stations,angles=a.angles,rho_min=a.rho_min,rho_max=a.rho_max,
        bracket_samples=a.bracket_samples,reach_pair_points=a.reach_pair_points,
        force_python=a.force_python,auto_build=not a.no_auto_build,
    )
    matrix["settings"]={
        "knots":a.knots,"epsilon":a.epsilon,"point_counts":a.point_counts,"scale_over_rc":a.scale_over_rc,
        "stations":a.stations,"angles":a.angles,"rho_min":a.rho_min,"rho_max":a.rho_max,
        "bracket_samples":a.bracket_samples,"relative_tolerance":a.relative_tolerance,
        "strong_relative_tolerance":a.strong_relative_tolerance,"reach_pair_points":a.reach_pair_points,
        "force_python":a.force_python,"no_auto_build":a.no_auto_build,"require_native":a.require_native,"out_dir":str(out),
    }
    for k,v in matrix["results"].items(): write_json(out/f"{k}.json",v)
    write_json(out/"convergence_report.json",matrix); write_csv(out/"convergence_report.csv",matrix["rows"])
    native_all=all(r["highest_backend"]=="cpp" for r in matrix["rows"])
    print(json.dumps({"ok":native_all if a.require_native else True,"native_all":native_all,"rows":matrix["rows"]},indent=2))
    return 0 if (native_all or not a.require_native) else 1
if __name__=="__main__": raise SystemExit(main())

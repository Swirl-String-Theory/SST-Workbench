#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.certification import build_scale_sweep


def main()->int:
    p=argparse.ArgumentParser(description="Separate ideal-knot scale from Rosenhead softening.")
    p.add_argument("--knots",nargs="+",default=list(DEFAULT_KNOT_IDS)); p.add_argument("--scales",nargs="+",type=float,required=True)
    p.add_argument("--epsilon",type=float,default=0.0019); p.add_argument("--resolution-mode",choices=("adaptive","fixed"),default="adaptive")
    p.add_argument("--centerline-points",type=int,default=8192); p.add_argument("--target-ds-over-epsilon",type=float,default=1.0)
    p.add_argument("--min-centerline-points",type=int,default=4096); p.add_argument("--max-centerline-points",type=int,default=65536)
    p.add_argument("--round-centerline-points-to",type=int,default=1024)
    p.add_argument("--stations",type=int,default=8); p.add_argument("--angles",type=int,default=16)
    p.add_argument("--rho-min",type=float,default=0.0005); p.add_argument("--rho-max",type=float,default=0.03)
    p.add_argument("--bracket-samples",type=int,default=96); p.add_argument("--reach-pair-points",type=int,default=1024)
    p.add_argument("--force-python",action="store_true"); p.add_argument("--no-auto-build",action="store_true")
    p.add_argument("--require-native",action="store_true"); p.add_argument("--out-dir",default="scale_sweep")
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    result=build_scale_sweep(
        a.knots,scales=a.scales,epsilon=a.epsilon,resolution_mode=a.resolution_mode,
        centerline_points=a.centerline_points,target_ds_over_epsilon=a.target_ds_over_epsilon,
        min_centerline_points=a.min_centerline_points,max_centerline_points=a.max_centerline_points,
        round_centerline_points_to=a.round_centerline_points_to,stations=a.stations,angles=a.angles,
        rho_min=a.rho_min,rho_max=a.rho_max,bracket_samples=a.bracket_samples,reach_pair_points=a.reach_pair_points,
        force_python=a.force_python,auto_build=not a.no_auto_build,
    )
    write_json(out/"scale_sweep.json",result); write_csv(out/"scale_sweep.csv",result["rows"])
    native_all=all(r["backend"]=="cpp" for r in result["rows"])
    print(json.dumps({"ok":native_all if a.require_native else True,"native_all":native_all,"rows":result["rows"]},indent=2))
    return 0 if (native_all or not a.require_native) else 1
if __name__=="__main__": raise SystemExit(main())

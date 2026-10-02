#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.certification import build_candidate_atlas


def main() -> int:
    p=argparse.ArgumentParser(description="Resolve radial Fermat stationary roots for the four-knot atlas.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-points", type=int, default=8192)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--stations", type=int, default=8)
    p.add_argument("--angles", type=int, default=16)
    p.add_argument("--rho-min", type=float, default=0.0005)
    p.add_argument("--rho-max", type=float, default=0.03)
    p.add_argument("--bracket-samples", type=int, default=96)
    p.add_argument("--reach-pair-points", type=int, default=1024)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="candidate_atlas")
    a=p.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    matrix=build_candidate_atlas(
        a.knots, epsilon=a.epsilon, centerline_points=a.centerline_points,
        scale_over_rc=a.scale_over_rc, stations=a.stations, angles=a.angles,
        rho_min=a.rho_min, rho_max=a.rho_max, bracket_samples=a.bracket_samples,
        reach_pair_points=a.reach_pair_points, force_python=a.force_python,
        auto_build=not a.no_auto_build,
    )
    matrix["settings"]={
        "knots":a.knots,"epsilon":a.epsilon,"centerline_points":a.centerline_points,
        "scale_over_rc":a.scale_over_rc,"stations":a.stations,"angles":a.angles,
        "rho_min":a.rho_min,"rho_max":a.rho_max,"bracket_samples":a.bracket_samples,
        "reach_pair_points":a.reach_pair_points,"force_python":a.force_python,
        "no_auto_build":a.no_auto_build,"require_native":a.require_native,"out_dir":str(out),
    }
    for knot_id,result in matrix["results"].items(): write_json(out/f"{knot_id}.json",result)
    write_json(out/"candidate_atlas.json",matrix); write_csv(out/"candidate_atlas.csv",matrix["rows"])
    native_all=all(r["backend"]=="cpp" for r in matrix["rows"])
    print(json.dumps({"ok": (native_all if a.require_native else True), "native_all":native_all,
                      "rows":matrix["rows"],"out_dir":str(out)},indent=2))
    return 0 if (native_all or not a.require_native) else 1
if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Single-run entry point for SST dark-knot Rayleigh / rocking diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_dark_knot_harness.core import run_audit, write_json


def main() -> int:
    p = argparse.ArgumentParser(description="Run one SST dark-knot Rayleigh/rocking audit.")
    p.add_argument("--knot", default="4_1", choices=["3_1", "4_1", "trefoil", "figure8", "figure-eight"], help="Knot identifier.")
    p.add_argument("--n", type=int, default=256, help="Number of polygon vertices.")
    p.add_argument("--omega", type=float, default=1.0, help="Background rotation rate Ω in audit units.")
    p.add_argument("--epsilon-bs", type=float, default=1.0, help="Biot-Savart regularization ε_BS in tau units.")
    p.add_argument("--shell-dr", type=float, default=0.25, help="Radial shell spacing Δr in tau units.")
    p.add_argument("--shell-h", type=float, default=0.5, help="Gaussian shell bandwidth h in tau units.")
    p.add_argument("--gamma", type=float, default=1.0, help="Circulation Γ used in the geometric kernel.")
    p.add_argument("--input-csv", default="", help="Optional base centerline CSV with x,y,z columns.")
    p.add_argument("--vertices-plus", default="", help="Optional relaxed V(+Ω) CSV for rocking/breathing.")
    p.add_argument("--vertices-minus", default="", help="Optional relaxed V(-Ω) CSV for rocking/breathing.")
    p.add_argument("--proxy-response-gain", type=float, default=0.0, help="Smoke-test only: synthesize small paired deformation when no response vertices are supplied.")
    p.add_argument("--response-source", default="auto", choices=["auto", "proxy", "ridgerunner", "projected_ridgerunner", "solver", "manual", "unknown"], help="Declare the provenance of --vertices-plus/--vertices-minus. Use ridgerunner/projected_ridgerunner/solver only for physically relaxed response CSVs.")
    p.add_argument("--mirror-axis", default="x", choices=["x", "y", "z"], help="Mirror axis for P closure test.")
    p.add_argument("--omega-axis", default="z", choices=["x", "y", "z"], help="Rotation axis used for Q_perp projection.")
    p.add_argument("--force-python", action="store_true", help="Skip C++ backend; use Python path only.")
    p.add_argument("--skip-build", action="store_true", help="Do not attempt C++ auto-build.")
    p.add_argument("--force-build", action="store_true", help="Force C++ rebuild before run.")
    p.add_argument("--build-verbose", action="store_true", help="Print compiler/build logs.")
    p.add_argument("--out", default="", help="Optional JSON output path.")
    p.add_argument("--summary-only", action="store_true", help="Print one-line summary instead of full JSON.")
    args = p.parse_args()

    result = run_audit(
        knot_id=args.knot,
        n=args.n,
        omega=args.omega,
        epsilon_bs=args.epsilon_bs,
        shell_dr=args.shell_dr,
        shell_h=args.shell_h,
        gamma=args.gamma,
        input_csv=args.input_csv or None,
        vertices_plus=args.vertices_plus or None,
        vertices_minus=args.vertices_minus or None,
        proxy_response_gain=args.proxy_response_gain,
        response_source=args.response_source,
        mirror_axis=args.mirror_axis,
        omega_axis=args.omega_axis,
        force_python=args.force_python,
        skip_build=args.skip_build,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
    )
    if args.out:
        write_json(args.out, result)
    if args.summary_only:
        rd = result["rayleigh"]
        rb = result["rocking_breathing"]
        print(
            f"[{'PASS' if result['ok'] else 'FAIL'}] knot={result['knot_id']} backend={result['backend']} "
            f"Delta={rd['Delta_Omega']:.6g} SigmaHat={rd['Sigma_hat_Omega']:.6g} "
            f"Rrock={rb.get('R_rock', float('nan')):.6g} epsP={rb.get('epsilon_P_rock', float('nan')):.6g}"
        )
    else:
        print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

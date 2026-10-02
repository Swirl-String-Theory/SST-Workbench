#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from fermat_ext import constants
from fermat_ext.core import analyze_profile, sweep_profiles, write_csv, write_json
from fermat_ext.knot_scan import scan_torus_knot


def main() -> int:
    p = argparse.ArgumentParser(description="Run the SST Fermat standalone audit battery.")
    p.add_argument("--out-dir", default="audit_out")
    p.add_argument("--force-build", action="store_true")
    args = p.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    ext_py = analyze_profile("external", 0.0045, 1e-5, 0.1, 6000, force_python=True, auto_build=False)
    ext_primary = analyze_profile("external", 0.0045, 1e-5, 0.1, 6000, force_build=args.force_build)
    write_json(out/"external_python.json", ext_py)
    write_json(out/"external_primary.json", ext_primary)

    x_py = ext_py["critical_roots"][0]["x"] if ext_py["critical_roots"] else math.nan
    x_primary = ext_primary["critical_roots"][0]["x"] if ext_primary["critical_roots"] else math.nan
    analytic_error = abs(x_py-constants.FORMAL_X_STAR)
    parity_error = abs(x_primary-x_py)

    sweep = sweep_profiles("rankine", [0.0038,0.0042,0.0048,0.0052,0.0060], force_python=True, auto_build=False)
    write_json(out/"rankine_sweep.json", sweep)
    write_csv(out/"rankine_sweep.csv", sweep)

    # Small fallback-only knot smoke test; intentionally not a global orbit certification.
    knot = scan_torus_knot(
        p=2, q=3, centerline_points=80, stations=3, angles=4,
        radial_samples=35, rho_min=0.002, rho_max=0.03,
        epsilon=0.0045, force_python=True, auto_build=False,
    )
    write_json(out/"trefoil_smoke_python.json", knot)

    checks = {
        "external_root_found": math.isfinite(x_py),
        "external_analytic_error_lt_1e-10": analytic_error < 1e-10,
        "primary_python_parity_lt_1e-10": parity_error < 1e-10,
        "rankine_sweep_has_rows": len(sweep) == 5,
        "knot_guard_preserved": knot["global_closed_orbit_certified"] is False and knot["qsm_certified"] is False,
    }
    summary = {
        "schema": "sst.fermat.audit.v0.1",
        "audit_name": "SST Fermat standalone Python+C++ audit battery",
        "primary_backend": ext_primary["backend"],
        "analytic_external_x_star": constants.FORMAL_X_STAR,
        "computed_external_x_star_python": x_py,
        "computed_external_x_star_primary": x_primary,
        "analytic_error": analytic_error,
        "parity_error": parity_error,
        "checks": checks,
        "ok": all(checks.values()),
        "note": "When pybind11/compiler is unavailable, primary uses the audited Python fallback; native parity must then be rerun on the target machine.",
    }
    write_json(out/"audit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

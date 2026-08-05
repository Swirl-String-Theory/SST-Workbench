#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fermat_ext.certification import symmetry_field_audit
from fermat_ext.core import write_csv, write_json
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS


def main() -> int:
    p = argparse.ArgumentParser(description="Audit rigid-motion, orientation, reindexing, and mirror covariance.")
    p.add_argument("--knots", nargs="+", default=list(DEFAULT_KNOT_IDS))
    p.add_argument("--epsilon", type=float, default=0.0019)
    p.add_argument("--centerline-points", type=int, default=2048)
    p.add_argument("--scale-over-rc", type=float, default=1.0)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--no-auto-build", action="store_true")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--out-dir", default="symmetry_audit")
    args = p.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    rows = []; results = {}
    for i, knot_id in enumerate(args.knots):
        result = symmetry_field_audit(
            knot_id,
            epsilon=args.epsilon,
            centerline_points=args.centerline_points,
            scale_over_rc=args.scale_over_rc,
            force_python=args.force_python,
            auto_build=(not args.no_auto_build) if i == 0 else False,
        )
        if args.require_native and result["backend"]["backend"] != "cpp":
            raise SystemExit("native backend required")
        results[knot_id] = result
        write_json(out / f"{knot_id}.json", result)
        rows.append({
            "knot_id": knot_id,
            "backend": result["backend"]["backend"],
            "max_beta_vector_linf_error": result["max_beta_vector_linf_error"],
            "max_jacobian_linf_error": result["max_jacobian_linf_error"],
            "max_scalar_G_linf_error": result["max_scalar_G_linf_error"],
        })
    combined = {"schema": "sst.fermat.symmetry-matrix.v0.5.1", "rows": rows, "results": results}
    write_json(out / "symmetry_audit.json", combined)
    write_csv(out / "symmetry_audit.csv", rows)
    print(json.dumps({"out_dir": str(out), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compare paired zero/background solid-body-vorticity campaign results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="campaign_summary.csv")
    ap.add_argument("--output", help="optional JSON report")
    ap.add_argument("--tolerance", type=float, default=1e-10)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    required = {
        "resolution", "epsilon", "kernel", "label", "background_vorticity",
        "relative_equilibrium_residual", "total_normalized_residual",
        "rigid_rate",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"missing columns: {missing}")

    strengths = sorted(float(x) for x in df["background_vorticity"].unique())
    if 0.0 not in strengths or len(strengths) < 2:
        raise SystemExit("campaign must contain zeta*=0 and at least one nonzero strength")

    index = ["resolution", "epsilon", "kernel", "label"]
    metrics = [
        "relative_equilibrium_residual",
        "total_normalized_residual",
        "rigid_rate",
        "deformation_rate",
        "energy_proxy",
        "impulse_norm",
    ]
    report: dict[str, object] = {
        "input": str(Path(args.csv).resolve()),
        "background_vorticities": strengths,
        "tolerance": args.tolerance,
        "comparisons": {},
    }
    worst_intrinsic = 0.0
    for strength in strengths:
        if strength == 0.0:
            continue
        comp: dict[str, float | int | bool] = {}
        for metric in metrics:
            if metric not in df.columns:
                continue
            pivot = df.pivot_table(index=index, columns="background_vorticity", values=metric, aggfunc="first")
            if 0.0 not in pivot.columns or strength not in pivot.columns:
                continue
            delta = (pivot[strength] - pivot[0.0]).dropna()
            comp[f"{metric}_max_abs_delta"] = float(np.max(np.abs(delta))) if len(delta) else float("nan")
            comp[f"{metric}_mean_delta"] = float(np.mean(delta)) if len(delta) else float("nan")
        intrinsic = float(comp.get("relative_equilibrium_residual_max_abs_delta", float("inf")))
        worst_intrinsic = max(worst_intrinsic, intrinsic)
        comp["intrinsic_invariance_pass"] = bool(intrinsic <= args.tolerance)
        report["comparisons"][str(strength)] = comp

    report["worst_intrinsic_residual_delta"] = worst_intrinsic
    report["overall_pass"] = bool(worst_intrinsic <= args.tolerance)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

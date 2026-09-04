#!/usr/bin/env python3
"""Analyze physical-tube and numerical-discretization bundle campaigns."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


def read_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("campaign_summary.csv")):
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["_source"] = str(path)
                for key, value in list(row.items()):
                    if key == "_source" or value in (None, "", "None"):
                        continue
                    if value in ("True", "False"):
                        row[key] = value == "True"
                        continue
                    try:
                        row[key] = float(value)
                    except ValueError:
                        pass
                rows.append(row)
    return rows


def relerr(a: float, b: float) -> float | None:
    if not math.isfinite(a) or not math.isfinite(b) or abs(b) < 1e-15:
        return None
    return abs(a-b)/abs(b)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Root containing campaign_summary.csv files")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    root = Path(args.input).resolve()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = read_rows(root)

    physical = [r for r in rows if r.get("bundle_mode") == "physical_tubes"]
    numerical = [r for r in rows if r.get("bundle_mode") == "numerical_discretization"]
    continuum = [r for r in rows if r.get("bundle_mode") == "continuum"]

    physical_checks = []
    for r in physical:
        expected = r["tube_count"] * r["circulation_per_tube"]
        physical_checks.append(abs(r["total_circulation"] - expected) < 1e-10)

    numerical_checks = []
    for r in numerical:
        expected = r["total_circulation"] / r["tube_count"]
        numerical_checks.append(abs(r["circulation_per_tube"] - expected) < 1e-10)

    # Match numerical rows to continuum rows with same protocol and physical total flux.
    convergence: list[dict[str, Any]] = []
    match_keys = ["label", "resolution", "epsilon", "kernel", "radius_ratio_to_hole", "total_circulation"]
    for r in numerical:
        candidates = [c for c in continuum if all(c.get(k) == r.get(k) for k in match_keys)]
        if not candidates:
            continue
        c = candidates[0]
        convergence.append({
            "label": r["label"],
            "resolution": r["resolution"],
            "epsilon": r["epsilon"],
            "kernel": r["kernel"],
            "radius_ratio_to_hole": r["radius_ratio_to_hole"],
            "total_circulation": r["total_circulation"],
            "tube_count": r["tube_count"],
            "background_velocity_rms_relerr": relerr(r["background_velocity_rms"], c["background_velocity_rms"]),
            "intrinsic_residual_relerr": relerr(r["intrinsic_residual"], c["intrinsic_residual"]),
            "clock_omega_relerr": relerr(r["clock_omega"], c["clock_omega"]),
        })

    # Summaries by tube count.
    count_summary: dict[str, dict[str, float | int | None]] = {}
    for n in sorted({int(r["tube_count"]) for r in numerical}):
        rr = [x for x in convergence if int(x["tube_count"]) == n]
        def avg(key: str) -> float | None:
            vals = [x[key] for x in rr if x[key] is not None]
            return sum(vals)/len(vals) if vals else None
        count_summary[str(n)] = {
            "matched_rows": len(rr),
            "mean_background_velocity_rms_relerr": avg("background_velocity_rms_relerr"),
            "mean_intrinsic_residual_relerr": avg("intrinsic_residual_relerr"),
            "mean_clock_omega_relerr": avg("clock_omega_relerr"),
        }

    gate_rows = []
    for gate in sorted({str(r.get("ladder_gate")) for r in rows}):
        gr = [r for r in rows if str(r.get("ladder_gate")) == gate]
        gate_rows.append({
            "gate": gate,
            "runs": len(gr),
            "valid_geometry_fraction": sum(bool(r.get("valid_geometry")) for r in gr)/len(gr) if gr else None,
            "relative_equilibrium_pass_fraction": sum(float(r.get("intrinsic_residual", 1)) <= 0.05 for r in gr)/len(gr) if gr else None,
            "minimum_intrinsic_residual": min((float(r["intrinsic_residual"]) for r in gr), default=None),
            "maximum_residual_reduction_fraction": max((float(r["residual_reduction_fraction"]) for r in gr if isinstance(r.get("residual_reduction_fraction"), (int,float))), default=None),
        })

    payload = {
        "status": "COMPLETE",
        "input_root": str(root),
        "total_rows": len(rows),
        "physical_rows": len(physical),
        "numerical_discretization_rows": len(numerical),
        "continuum_rows": len(continuum),
        "checks": {
            "physical_total_flux_equals_N_times_tube_flux": bool(physical_checks) and all(physical_checks),
            "numerical_tube_flux_equals_total_over_N": bool(numerical_checks) and all(numerical_checks),
            "full_3d_tube_backreaction_certified": False,
        },
        "numerical_convergence_by_count": count_summary,
        "gate_ledger": gate_rows,
        "epistemic_guard": (
            "Convergence concerns frozen straight tubes only. Physical-tube N-ladders change total flux; "
            "numerical-discretization N-ladders hold total flux fixed. These must not be merged."
        ),
    }
    (out / "bundle_mode_analysis.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if convergence:
        fields = list(convergence[0])
        with (out / "numerical_discretization_convergence.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(convergence)
    if gate_rows:
        fields = list(gate_rows[0])
        with (out / "B0_B8_gate_ledger.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(gate_rows)

    md = [
        "# Axial vortex-bundle mode analysis",
        "",
        f"Rows analyzed: **{len(rows)}**.",
        "",
        "## Mode separation",
        "",
        f"- Physical-tube rows: {len(physical)}",
        f"- Numerical-discretization rows: {len(numerical)}",
        f"- Continuum-reference rows: {len(continuum)}",
        "",
        "Physical tubes hold circulation per tube fixed, so total circulation grows as `N * Gamma_tube`.",
        "Numerical discretization holds total bundle circulation fixed, so each tube carries `Gamma_total / N`.",
        "",
        "## Backreaction gate",
        "",
        "Full three-dimensional bending and mutual evolution of the axial tubes is **not certified in v0.3.0**. "
        "All bundle results use frozen infinite straight tubes.",
        "",
        "## Numerical convergence by tube count",
        "",
        "| N | matched | mean velocity-field error | mean intrinsic-residual error | clock-rate error |",
        "|---:|---:|---:|---:|---:|",
    ]
    for n, s in count_summary.items():
        def fmt(v: Any) -> str:
            return "—" if v is None else f"{v:.6g}"
        md.append(f"| {n} | {s['matched_rows']} | {fmt(s['mean_background_velocity_rms_relerr'])} | {fmt(s['mean_intrinsic_residual_relerr'])} | {fmt(s['mean_clock_omega_relerr'])} |")
    (out / "BUNDLE_MODE_ANALYSIS.md").write_text("\n".join(md)+"\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
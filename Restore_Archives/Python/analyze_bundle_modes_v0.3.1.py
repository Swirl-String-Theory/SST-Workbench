#!/usr/bin/env python3
"""Analyze physical-tube and numerical-discretization bundle campaigns.

v0.3.1 hotfix:
- accepts explicit --physical-input and --numerical-input directories;
- keeps legacy --input (repeatable) for broad recursive discovery;
- skips non-bundle campaign_summary.csv files instead of assuming one schema;
- reports which summary files were used or skipped.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable

BUNDLE_MODES = {"physical_tubes", "numerical_discretization", "continuum"}
REQUIRED_COLUMNS = {
    "ladder_gate",
    "label",
    "resolution",
    "epsilon",
    "kernel",
    "bundle_mode",
    "radius_ratio_to_hole",
    "tube_count",
    "circulation_per_tube",
    "total_circulation",
    "clock_omega",
    "valid_geometry",
    "intrinsic_residual",
    "residual_reduction_fraction",
    "background_velocity_rms",
}


def _summary_path(path: Path) -> Path:
    """Resolve a direct campaign directory or an explicit CSV file."""
    return path if path.is_file() else path / "campaign_summary.csv"


def _discover_recursive(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.rglob("campaign_summary.csv"))


def _convert(value: str | None) -> Any:
    if value in (None, "", "None", "null"):
        return None
    if value == "True":
        return True
    if value == "False":
        return False
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def read_rows(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    used: list[str] = []
    skipped: list[dict[str, Any]] = []

    seen: set[Path] = set()
    for raw_path in paths:
        path = raw_path.resolve()
        if path in seen:
            continue
        seen.add(path)

        if not path.exists():
            skipped.append({"path": str(path), "reason": "not_found"})
            continue
        if path.name != "campaign_summary.csv":
            skipped.append({"path": str(path), "reason": "not_a_campaign_summary_csv"})
            continue

        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            missing = sorted(REQUIRED_COLUMNS - headers)
            if missing:
                skipped.append({
                    "path": str(path),
                    "reason": "non_bundle_or_older_schema",
                    "missing_columns": missing,
                })
                continue

            file_rows = 0
            for raw in reader:
                row = {key: _convert(value) for key, value in raw.items()}
                if row.get("bundle_mode") not in BUNDLE_MODES:
                    continue
                row["_source"] = str(path)
                rows.append(row)
                file_rows += 1

            if file_rows:
                used.append(str(path))
            else:
                skipped.append({"path": str(path), "reason": "no_supported_bundle_rows"})

    return rows, used, skipped


def relerr(a: Any, b: Any) -> float | None:
    try:
        aa, bb = float(a), float(b)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(aa) or not math.isfinite(bb) or abs(bb) < 1e-15:
        return None
    return abs(aa - bb) / abs(bb)


def _finite_values(rows: Iterable[dict[str, Any]], key: str) -> list[float]:
    out: list[float] = []
    for row in rows:
        try:
            value = float(row[key])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(value):
            out.append(value)
    return out


def _same_value(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-11, abs_tol=1e-12)
    return a == b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        action="append",
        default=[],
        help="Broad root containing campaign_summary.csv files; may be repeated. Non-bundle schemas are skipped.",
    )
    ap.add_argument(
        "--physical-input",
        help="Physical-tube campaign directory or its campaign_summary.csv file.",
    )
    ap.add_argument(
        "--numerical-input",
        help="Numerical-discretization campaign directory or its campaign_summary.csv file.",
    )
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    explicit_paths: list[Path] = []
    if args.physical_input:
        explicit_paths.append(_summary_path(Path(args.physical_input)))
    if args.numerical_input:
        explicit_paths.append(_summary_path(Path(args.numerical_input)))

    recursive_paths: list[Path] = []
    for item in args.input:
        recursive_paths.extend(_discover_recursive(Path(item)))

    input_paths = explicit_paths + recursive_paths
    if not input_paths:
        ap.error("Provide --input or explicit --physical-input and/or --numerical-input.")

    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows, used_files, skipped_files = read_rows(input_paths)
    if not rows:
        raise SystemExit(
            "No v0.3 axial-bundle rows found. Use the two explicit campaign directories or inspect skipped_summary_files.json."
        )

    physical = [r for r in rows if r.get("bundle_mode") == "physical_tubes"]
    numerical = [r for r in rows if r.get("bundle_mode") == "numerical_discretization"]
    continuum = [r for r in rows if r.get("bundle_mode") == "continuum"]

    physical_checks = []
    for r in physical:
        expected = float(r["tube_count"]) * float(r["circulation_per_tube"])
        physical_checks.append(math.isclose(float(r["total_circulation"]), expected, rel_tol=1e-11, abs_tol=1e-10))

    numerical_checks = []
    for r in numerical:
        n = float(r["tube_count"])
        if n <= 0:
            numerical_checks.append(False)
            continue
        expected = float(r["total_circulation"]) / n
        numerical_checks.append(math.isclose(float(r["circulation_per_tube"]), expected, rel_tol=1e-11, abs_tol=1e-10))

    convergence: list[dict[str, Any]] = []
    match_keys = ["label", "resolution", "epsilon", "kernel", "radius_ratio_to_hole", "total_circulation"]
    for r in numerical:
        candidates = [c for c in continuum if all(_same_value(c.get(k), r.get(k)) for k in match_keys)]
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

    count_summary: dict[str, dict[str, float | int | None]] = {}
    for n in sorted({int(float(r["tube_count"])) for r in numerical}):
        rr = [x for x in convergence if int(float(x["tube_count"])) == n]

        def avg(key: str) -> float | None:
            vals = [float(x[key]) for x in rr if x[key] is not None and math.isfinite(float(x[key]))]
            return sum(vals) / len(vals) if vals else None

        count_summary[str(n)] = {
            "matched_rows": len(rr),
            "mean_background_velocity_rms_relerr": avg("background_velocity_rms_relerr"),
            "mean_intrinsic_residual_relerr": avg("intrinsic_residual_relerr"),
            "mean_clock_omega_relerr": avg("clock_omega_relerr"),
        }

    gate_rows: list[dict[str, Any]] = []
    gates = sorted({str(r.get("ladder_gate")) for r in rows if r.get("ladder_gate") not in (None, "", "None")})
    for gate in gates:
        gr = [r for r in rows if str(r.get("ladder_gate")) == gate]
        residuals = _finite_values(gr, "intrinsic_residual")
        reductions = _finite_values(gr, "residual_reduction_fraction")
        gate_rows.append({
            "gate": gate,
            "runs": len(gr),
            "valid_geometry_fraction": sum(bool(r.get("valid_geometry")) for r in gr) / len(gr) if gr else None,
            "relative_equilibrium_pass_fraction": sum(v <= 0.05 for v in residuals) / len(residuals) if residuals else None,
            "minimum_intrinsic_residual": min(residuals) if residuals else None,
            "maximum_residual_reduction_fraction": max(reductions) if reductions else None,
        })

    payload = {
        "status": "COMPLETE",
        "input_mode": "explicit" if explicit_paths else "recursive",
        "used_summary_files": used_files,
        "skipped_summary_file_count": len(skipped_files),
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
    (out / "skipped_summary_files.json").write_text(json.dumps(skipped_files, indent=2), encoding="utf-8")

    if convergence:
        fields = list(convergence[0])
        with (out / "numerical_discretization_convergence.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(convergence)
    if gate_rows:
        fields = list(gate_rows[0])
        with (out / "B0_B8_gate_ledger.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(gate_rows)

    md = [
        "# Axial vortex-bundle mode analysis",
        "",
        f"Rows analyzed: **{len(rows)}**.",
        f"Summary files used: **{len(used_files)}**; skipped as incompatible: **{len(skipped_files)}**.",
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
        "Full three-dimensional bending and mutual evolution of the axial tubes is **not certified in v0.3.1**. "
        "All bundle results use frozen infinite straight tubes.",
        "",
        "## Numerical convergence by tube count",
        "",
        "| N | matched | mean velocity-field error | mean intrinsic-residual error | clock-rate error |",
        "|---:|---:|---:|---:|---:|",
    ]

    def fmt(v: Any) -> str:
        return "—" if v is None else f"{float(v):.6g}"

    for n, summary in count_summary.items():
        md.append(
            f"| {n} | {summary['matched_rows']} | {fmt(summary['mean_background_velocity_rms_relerr'])} | "
            f"{fmt(summary['mean_intrinsic_residual_relerr'])} | {fmt(summary['mean_clock_omega_relerr'])} |"
        )
    (out / "BUNDLE_MODE_ANALYSIS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

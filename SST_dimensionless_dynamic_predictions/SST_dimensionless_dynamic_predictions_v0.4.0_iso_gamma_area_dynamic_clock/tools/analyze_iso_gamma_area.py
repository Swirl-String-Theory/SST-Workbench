#!/usr/bin/env python3
"""Analyze iso-Gamma/A dynamic-clock campaigns.

The analyzer never derives T_dyn from Gamma/A. It consumes the independently
measured multipole-phase rates written by sst_iso_gamma_area_clock.py and tests
Q_Gamma = 1 with preregistered per-run and family-spread gates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any) -> float:
    if value in (None, "", "None", "nan", "NaN"):
        return math.nan
    return float(value)


def _read_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["_source_file"] = str(path)
                rows.append(row)
    return rows


def _find_summaries(inputs: list[str]) -> list[Path]:
    found: list[Path] = []
    for text in inputs:
        p = Path(text)
        if p.is_file():
            found.append(p)
        elif p.is_dir():
            direct = p / "campaign_summary.csv"
            if direct.exists():
                found.append(direct)
            else:
                found.extend(sorted(p.rglob("campaign_summary.csv")))
        else:
            raise FileNotFoundError(text)
    unique: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(rp)
    return unique


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def analyze(rows: list[dict[str, Any]], q_tolerance: float, spread_tolerance: float) -> dict[str, Any]:
    compatible = [r for r in rows if "q_gamma_signed" in r and "t_dyn_certified" in r]
    skipped = [r for r in rows if r not in compatible]
    certified = [r for r in compatible if _bool(r.get("t_dyn_certified"))]

    ledger: list[dict[str, Any]] = []
    for r in compatible:
        q = _float(r.get("q_gamma_signed"))
        cert = _bool(r.get("t_dyn_certified"))
        deviation = abs(q - 1.0) if math.isfinite(q) else math.inf
        if not cert:
            verdict = "INCONCLUSIVE_UNCERTIFIED_T_DYN"
        elif deviation <= q_tolerance:
            verdict = "PASS_RUN_GATE"
        else:
            verdict = "FALSIFY_RUN_GATE"
        ledger.append({
            "run_id": r.get("run_id"),
            "family_id": r.get("family_id"),
            "representation": r.get("representation"),
            "radius_ratio_to_hole": r.get("radius_ratio_to_hole"),
            "gamma_over_area": r.get("gamma_over_area"),
            "predicted_period": r.get("predicted_period"),
            "t_dyn": r.get("t_dyn"),
            "q_gamma_signed": r.get("q_gamma_signed"),
            "q_gamma_stderr": r.get("q_gamma_stderr"),
            "certified": cert,
            "absolute_q_deviation": deviation,
            "verdict": verdict,
            "reason": r.get("t_dyn_certification_reason"),
        })

    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in compatible:
        families[str(r.get("family_id"))].append(r)

    family_rows: list[dict[str, Any]] = []
    family_falsifications = 0
    family_passes = 0
    for family_id, group in sorted(families.items()):
        cert = [r for r in group if _bool(r.get("t_dyn_certified")) and math.isfinite(_float(r.get("q_gamma_signed")))]
        q_values = [_float(r["q_gamma_signed"]) for r in cert]
        continuum = [r for r in cert if str(r.get("representation")) == "continuum"]
        q_cont = [_float(r["q_gamma_signed"]) for r in continuum]
        if not cert:
            verdict = "INCONCLUSIVE_NO_CERTIFIED_RUNS"
            spread = math.nan
            max_dev = math.nan
        else:
            spread = (max(q_cont) - min(q_cont)) if len(q_cont) >= 2 else 0.0
            max_dev = max(abs(q - 1.0) for q in q_values)
            if max_dev > q_tolerance or spread > spread_tolerance:
                verdict = "FALSIFIED_WITHIN_MODEL"
                family_falsifications += 1
            else:
                verdict = "PASS_WITHIN_MODEL"
                family_passes += 1
        zeta_values = [_float(r.get("gamma_over_area")) for r in group]
        finite_zeta = [z for z in zeta_values if math.isfinite(z)]
        zeta_spread = max(finite_zeta) - min(finite_zeta) if finite_zeta else math.nan
        family_rows.append({
            "family_id": family_id,
            "runs": len(group),
            "certified_runs": len(cert),
            "continuum_certified_runs": len(continuum),
            "mean_q_gamma_signed": sum(q_values)/len(q_values) if q_values else math.nan,
            "minimum_q_gamma_signed": min(q_values) if q_values else math.nan,
            "maximum_q_gamma_signed": max(q_values) if q_values else math.nan,
            "maximum_absolute_q_deviation": max_dev,
            "continuum_iso_family_q_spread": spread,
            "gamma_over_area_absolute_spread": zeta_spread,
            "q_tolerance": q_tolerance,
            "spread_tolerance": spread_tolerance,
            "verdict": verdict,
        })

    if any(row["verdict"] == "FALSIFY_RUN_GATE" for row in ledger) or family_falsifications:
        overall = "FALSIFIED_WITHIN_FROZEN_BUNDLE_MODEL"
    elif certified and family_passes:
        overall = "PASS_WITHIN_FROZEN_BUNDLE_MODEL"
    else:
        overall = "INCONCLUSIVE_NO_CERTIFIED_DYNAMIC_PERIOD"

    return {
        "overall_verdict": overall,
        "input_rows": len(rows),
        "compatible_rows": len(compatible),
        "skipped_rows": len(skipped),
        "certified_rows": len(certified),
        "run_falsifications": sum(1 for row in ledger if row["verdict"] == "FALSIFY_RUN_GATE"),
        "run_passes": sum(1 for row in ledger if row["verdict"] == "PASS_RUN_GATE"),
        "family_falsifications": family_falsifications,
        "family_passes": family_passes,
        "q_tolerance": q_tolerance,
        "spread_tolerance": spread_tolerance,
        "ledger": ledger,
        "families": family_rows,
        "sources": sorted({str(r.get("_source_file")) for r in rows}),
    }


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Iso-Γ/A dynamic-clock falsification analysis",
        "",
        "## Verdict",
        "",
        f"`{result['overall_verdict']}`",
        "",
        "The measured dynamic period is extracted from the evolving trefoil multipole phase. "
        "The prescribed value Γ/A is used only afterward to form the falsifier",
        "",
        r"\[",
        r"\mathcal Q_\Gamma=\frac{2(\Omega_{\rm bundle}^{\rm obs}-\Omega_{0}^{\rm obs})}{\Gamma/A}.",
        r"\]",
        "",
        r"The hypothesis predicts \(\mathcal Q_\Gamma=1\).",
        "",
        "## Counts",
        "",
        f"- Input rows: {result['input_rows']}",
        f"- Compatible rows: {result['compatible_rows']}",
        f"- Certified T_dyn rows: {result['certified_rows']}",
        f"- Run-level falsifications: {result['run_falsifications']}",
        f"- Run-level passes: {result['run_passes']}",
        f"- Family-level falsifications: {result['family_falsifications']}",
        f"- Family-level passes: {result['family_passes']}",
        "",
        "## Family ledger",
        "",
        "| Family | Certified | mean Q | max |Q-1| | iso-family spread | Verdict |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in result["families"]:
        def fmt(x: Any) -> str:
            try:
                v = float(x)
                return f"{v:.6g}" if math.isfinite(v) else "—"
            except (TypeError, ValueError):
                return "—"
        lines.append(
            f"| {row['family_id']} | {row['certified_runs']} | "
            f"{fmt(row['mean_q_gamma_signed'])} | {fmt(row['maximum_absolute_q_deviation'])} | "
            f"{fmt(row['continuum_iso_family_q_spread'])} | {row['verdict']} |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "A failure falsifies the claim only for the implemented frozen straight Rankine/discrete "
        "bundle model and the selected trefoil observable. Full 3-D mutual backreaction, tube "
        "bending and a proper-time identification remain separate open gates.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze SST iso-Gamma/A dynamic-clock campaigns")
    p.add_argument("--input", action="append", required=True, help="Campaign directory or campaign_summary.csv; repeatable")
    p.add_argument("--output", required=True)
    p.add_argument("--q-tolerance", type=float, default=0.02)
    p.add_argument("--spread-tolerance", type=float, default=0.02)
    args = p.parse_args()

    summaries = _find_summaries(args.input)
    if not summaries:
        raise SystemExit("No campaign_summary.csv files found")
    rows = _read_rows(summaries)
    result = analyze(rows, args.q_tolerance, args.spread_tolerance)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "iso_gamma_area_analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_csv(out / "falsification_ledger.csv", result["ledger"])
    _write_csv(out / "iso_family_summary.csv", result["families"])
    (out / "ISO_GAMMA_AREA_ANALYSIS.md").write_text(_markdown(result), encoding="utf-8")
    print(json.dumps({
        "status": "complete",
        "verdict": result["overall_verdict"],
        "certified_rows": result["certified_rows"],
        "output": str(out.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

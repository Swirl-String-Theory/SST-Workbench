#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finite_core_spectral.core import write_json
from finite_core_spectral.fourier import FourierSettings, _detect_fourier_candidates_with_diagnostics
from finite_core_spectral.fourier_convergence import evaluate_fourier_convergence


def settings_from_result(result: dict, args) -> FourierSettings:
    old = result.get("fourier_settings", {})
    return FourierSettings(
        max_m=int(old.get("max_m", 12)),
        symmetry_order=int(old.get("symmetry_order", 4)),
        low_mode_leakage_max=float(old.get("low_mode_leakage_max", 0.10)),
        sector_leakage_max=float(old.get("sector_leakage_max", 1e-8)),
        dominant_mode_weight_min=float(old.get("dominant_mode_weight_min", 0.50)),
        branch_overlap_min=float(old.get("branch_overlap_min", 0.80)),
        candidate_abs_m_min=int(old.get("candidate_abs_m_min", 2)),
        growth_rate_floor=float(args.growth_rate_floor),
        eigenpair_abs_tol=float(args.eigenpair_abs_tol),
        eigenpair_rel_tol=float(args.eigenpair_rel_tol),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-run only the v0.1.2.4 detector/canonicalization on completed Fourier case JSON files.")
    ap.add_argument("source_dir", help="Existing audit directory containing case_*.json files.")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--growth-rate-floor", type=float, default=1e-8)
    ap.add_argument("--eigenpair-abs-tol", type=float, default=1e-10)
    ap.add_argument("--eigenpair-rel-tol", type=float, default=1e-6)
    ap.add_argument("--q-cluster-tol", type=float, default=0.025)
    ap.add_argument("--q-gate-tol", type=float, default=0.020)
    args = ap.parse_args()

    src = Path(args.source_dir)
    if not src.is_dir():
        raise SystemExit(f"source directory not found: {src}")
    out = Path(args.out_dir) if args.out_dir else src.with_name(src.name + "_detector_v0.1.2.4")
    out.mkdir(parents=True, exist_ok=True)

    case_results = []
    totals = {
        "raw_real_sign_flip_count": 0,
        "rejected_subfloor_sign_flip_count": 0,
        "resolved_growth_transition_branch_count": 0,
        "rejected_dominant_abs_m_change_count": 0,
        "raw_candidate_count": 0,
        "canonical_candidate_count": 0,
        "eigenpair_duplicates_removed": 0,
    }

    case_files = sorted(src.glob("case_*.json"))
    if not case_files:
        raise SystemExit(f"no case_*.json files found in {src}")

    for path in case_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        result = data.get("result", {})
        if "sector_rows" not in result or "rows" not in result:
            raise SystemExit(f"case lacks stored Fourier rows required for detector-only reprocessing: {path.name}")
        fs = settings_from_result(result, args)
        candidates, diag = _detect_fourier_candidates_with_diagnostics(result["sector_rows"], result["rows"], fs)
        for k in totals:
            totals[k] += int(diag.get(k, 0))
        light = {
            "axis": data["axis"], "case": data["case"], "value": data["value"],
            "result": {
                "config": result.get("config"),
                "fourier_settings": fs.__dict__,
                "candidate_diagnostics": diag,
                "candidates": candidates,
            },
        }
        case_results.append(light)
        write_json(out / f"case_{data['axis']}_{data['case']}_detector.json", light)

    clusters = evaluate_fourier_convergence(case_results, q_cluster_tol=args.q_cluster_tol, q_gate_tol=args.q_gate_tol)
    promoted = [c for c in clusters if c.get("promote_converged_candidate") is True]
    summary = {
        "ok": True,
        "protocol": "detector-reprocess-v0.1.2.4",
        "source_dir": str(src),
        "source_case_count": len(case_results),
        "operator_recomputed": False,
        "growth_rate_floor": args.growth_rate_floor,
        "candidate_diagnostics": totals,
        "n_candidate_clusters": len(clusters),
        "n_promoted_converged_candidates": len(promoted),
        "n_clusters_with_full_promotion_gates_evaluated": sum(1 for c in clusters if c.get("full_promotion_gates_evaluated") is True),
        "n_clusters_with_full_promotion_gates_not_evaluated": sum(1 for c in clusters if c.get("full_promotion_gates_evaluated") is False),
        "note": "Detector-only reprocessing uses stored Fourier rows; it does not recompute the numerical operator.",
    }
    write_json(out / "candidate_clusters.json", clusters)
    write_json(out / "audit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

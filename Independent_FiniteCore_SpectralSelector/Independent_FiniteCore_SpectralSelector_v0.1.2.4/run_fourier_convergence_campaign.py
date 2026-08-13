#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from finite_core_spectral.core import independence_manifest, write_csv, write_json
from finite_core_spectral.fourier import FourierSettings, fourier_scan
from finite_core_spectral.fourier_convergence import evaluate_fourier_convergence

BASE = {
    "n_nodes": 96,
    "ring_radius_over_core": 4.0,
    "q_min": 2.31,
    "q_max": 3.10,
    "q_step": 0.01,
    "image_shell": 2,
    "fd_eps_over_core": 1e-4,
    "core_model": 0,
    "threads": 16,
    "neutral_modes": 6,
    "eig_zero_tol": 1e-8,
    "residual_max": 5e-2,
}

QUICK_BASE = {**BASE, "n_nodes": 48}


def cases(quick: bool = False):
    if quick:
        return [
            ("resolution", "N32", 32),
            ("resolution", "N48", 48),
            ("image_shell", "S1", 1),
            ("image_shell", "S2", 2),
            ("fd_eps", "H3e-4", 3e-4),
            ("fd_eps", "H1e-4", 1e-4),
        ]
    return [
        ("resolution", "N48", 48),
        ("resolution", "N64", 64),
        ("resolution", "N96", 96),
        ("resolution", "N128", 128),
        ("image_shell", "S1", 1),
        ("image_shell", "S2", 2),
        ("image_shell", "S3", 3),
        ("fd_eps", "H3e-4", 3e-4),
        ("fd_eps", "H1e-4", 1e-4),
        ("fd_eps", "H3e-5", 3e-5),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Blind v0.1.2 Fourier/C4 mode-resolved convergence campaign. No external physical target is accepted."
    )
    ap.add_argument("--out-dir", default="audit_fourier_convergence")
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--q-min", type=float, default=2.31)
    ap.add_argument("--q-max", type=float, default=3.10)
    ap.add_argument("--q-step", type=float, default=0.01)
    ap.add_argument("--max-m", type=int, default=12)
    ap.add_argument("--symmetry-order", type=int, default=4)
    ap.add_argument("--low-mode-leakage-max", type=float, default=0.10)
    ap.add_argument("--sector-leakage-max", type=float, default=1e-8)
    ap.add_argument("--dominant-mode-weight-min", type=float, default=0.50)
    ap.add_argument("--branch-overlap-min", type=float, default=0.80)
    ap.add_argument("--growth-rate-floor", type=float, default=1e-8,
                    help="Resolved |Re(lambda)| floor; sub-floor sign flips are rejected as numerical noise.")
    ap.add_argument("--eigenpair-abs-tol", type=float, default=1e-10,
                    help="Absolute tolerance for conjugate/+/- eigenpair event canonicalization.")
    ap.add_argument("--eigenpair-rel-tol", type=float, default=1e-6,
                    help="Relative tolerance for conjugate/+/- eigenpair event canonicalization.")
    ap.add_argument("--q-cluster-tol", type=float, default=0.015)
    ap.add_argument("--q-gate-tol", type=float, default=0.010)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--force-python", action="store_true")
    ap.add_argument("--no-c4-accel", action="store_true", help="Disable exact C4 Jacobian column reconstruction acceleration.")
    ap.add_argument("--no-c4-audit", action="store_true", help="Disable independent rotated-column audit (not recommended for research runs).")
    ap.add_argument("--force-build", action="store_true")
    ap.add_argument("--build-verbose", action="store_true")
    ap.add_argument("--no-resume", action="store_true", help="Ignore compatible completed case JSON files in out-dir and recompute them.")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    selected_base = QUICK_BASE if args.quick else BASE
    base = {**selected_base, "threads": args.threads, "q_min": args.q_min, "q_max": args.q_max, "q_step": args.q_step}
    fs = FourierSettings(
        max_m=args.max_m,
        symmetry_order=args.symmetry_order,
        low_mode_leakage_max=args.low_mode_leakage_max,
        sector_leakage_max=args.sector_leakage_max,
        dominant_mode_weight_min=args.dominant_mode_weight_min,
        branch_overlap_min=args.branch_overlap_min,
        candidate_abs_m_min=2,
        growth_rate_floor=args.growth_rate_floor,
        eigenpair_abs_tol=args.eigenpair_abs_tol,
        eigenpair_rel_tol=args.eigenpair_rel_tol,
    )

    c4_accel_enabled = bool(args.quick and not args.no_c4_accel)
    manifest = independence_manifest(base)
    manifest["protocol"] = "dimensionless-blind-v1.2.4"
    manifest["fourier_analysis"] = {
        **fs.__dict__,
        "q_cluster_tolerance": args.q_cluster_tol,
        "q_gate_tolerance": args.q_gate_tol,
        "global_spectrum_promotion_allowed": False,
        "external_target_matching": False,
        "transition_detector": "resolved-growth-floor-v1",
        "eigenpair_canonicalization": "conjugate-plus-minus-v1",
        "quick_missing_full_gates": "not_evaluated",
        "range_provenance": "restricted only from prior internal blind numerical support; no external physical target used",
        "c4_acceleration_enabled": c4_accel_enabled,
        "c4_acceleration_scope": "quick-only by default; full research campaign retains brute-force Jacobian",
        "c4_independent_audit_enabled": bool(c4_accel_enabled and not args.no_c4_audit),
        "quick_base_n_nodes": QUICK_BASE["n_nodes"] if args.quick else None,
    }
    write_json(out / "independence_manifest.json", manifest)

    case_results = []
    flat_fourier = []
    flat_global = []
    cache: dict[str, dict] = {}
    resumed_count = 0
    todo = cases(args.quick)
    for idx, (axis, tag, value) in enumerate(todo, 1):
        cfg = dict(base)
        if axis == "resolution":
            cfg["n_nodes"] = int(value)
        elif axis == "image_shell":
            cfg["image_shell"] = int(value)
        elif axis == "fd_eps":
            cfg["fd_eps_over_core"] = float(value)
        print(f"\n=== [{idx}/{len(todo)}] {axis}:{tag} ===")
        key = json.dumps(cfg, sort_keys=True, separators=(",", ":")) + json.dumps(fs.__dict__, sort_keys=True) + f"|c4={int(c4_accel_enabled)}"
        case_path = out / f"case_{axis}_{tag}.json"
        result = None
        if not args.no_resume and case_path.exists():
            try:
                saved = json.loads(case_path.read_text(encoding="utf-8"))
                sr = saved.get("result", {})
                perf = sr.get("performance", {})
                if (
                    sr.get("config") == cfg
                    and sr.get("fourier_settings") == fs.__dict__
                    and bool(perf.get("c4_acceleration_used", False)) == c4_accel_enabled
                ):
                    result = sr
                    resumed_count += 1
                    print("resuming compatible completed case from disk")
            except Exception:
                result = None
        if result is None and key in cache:
            print("reusing identical baseline configuration")
            result = cache[key]
        if result is None:
            result = fourier_scan(
                cfg,
                fs,
                force_python=args.force_python,
                force_build=(args.force_build and not cache),
                build_verbose=args.build_verbose,
                progress=True,
                use_c4_accel=c4_accel_enabled,
                audit_c4_accel=not args.no_c4_audit,
            )
        cache[key] = result
        case = {"axis": axis, "case": tag, "value": value, "result": result}
        case_results.append(case)
        write_json(case_path, case)
        for r in result["rows"]:
            flat_global.append({"axis": axis, "case": tag, "value": value, **r})
        for r in result["sector_rows"]:
            flat_fourier.append({"axis": axis, "case": tag, "value": value, **r})

    clusters = evaluate_fourier_convergence(
        case_results, q_cluster_tol=args.q_cluster_tol, q_gate_tol=args.q_gate_tol
    )
    candidate_diag_totals = {
        "raw_real_sign_flip_count": sum(int(c["result"].get("candidate_diagnostics", {}).get("raw_real_sign_flip_count", 0)) for c in case_results),
        "rejected_subfloor_sign_flip_count": sum(int(c["result"].get("candidate_diagnostics", {}).get("rejected_subfloor_sign_flip_count", 0)) for c in case_results),
        "resolved_growth_transition_branch_count": sum(int(c["result"].get("candidate_diagnostics", {}).get("resolved_growth_transition_branch_count", 0)) for c in case_results),
        "raw_candidate_count": sum(int(c["result"].get("candidate_diagnostics", {}).get("raw_candidate_count", len(c["result"].get("candidates", [])))) for c in case_results),
        "canonical_candidate_count": sum(int(c["result"].get("candidate_diagnostics", {}).get("canonical_candidate_count", len(c["result"].get("candidates", [])))) for c in case_results),
        "eigenpair_duplicates_removed": sum(int(c["result"].get("candidate_diagnostics", {}).get("eigenpair_duplicates_removed", 0)) for c in case_results),
    }
    write_csv(out / "fourier_sector_rows.csv", flat_fourier)
    write_csv(out / "global_reference_rows.csv", flat_global)
    write_json(out / "candidate_clusters.json", clusters)
    promoted = [c for c in clusters if c["promote_converged_candidate"]]
    summary = {
        "ok": True,
        "dimensionless_only": True,
        "n_cases": len(case_results),
        "max_m": args.max_m,
        "symmetry_order": args.symmetry_order,
        "n_fourier_candidate_clusters": len(clusters),
        "n_promoted_converged_candidates": len(promoted),
        "candidate_diagnostics": candidate_diag_totals,
        "n_clusters_with_full_promotion_gates_evaluated": sum(1 for c in clusters if c.get("full_promotion_gates_evaluated") is True),
        "n_clusters_with_full_promotion_gates_not_evaluated": sum(1 for c in clusters if c.get("full_promotion_gates_evaluated") is False),
        "promoted_candidates": promoted,
        "global_spectrum_promotion_allowed": False,
        "performance": {
            "c4_acceleration_enabled": c4_accel_enabled,
        "c4_acceleration_scope": "quick-only by default; full research campaign retains brute-force Jacobian",
            "c4_independent_audit_enabled": bool(c4_accel_enabled and not args.no_c4_audit),
            "quick_base_n_nodes": QUICK_BASE["n_nodes"] if args.quick else None,
            "unique_case_count_after_cache": len(cache),
            "resumed_case_count": resumed_count,
        },
        "note": "Promotion is numerical Fourier/C4 convergence only; it is not an external physical interpretation.",
    }
    write_json(out / "audit_summary.json", summary)
    print("\n" + json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

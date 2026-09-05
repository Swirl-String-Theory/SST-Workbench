#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from finite_core_spectral.core import independence_manifest, spectrum_at_q, write_json
from finite_core_spectral.convergence import evaluate_gap_convergence
from finite_core_spectral.fourier import FourierSettings, fourier_scan, project_low_fourier
from finite_core_spectral.fourier_convergence import evaluate_fourier_convergence
from finite_core_spectral import fallback


def _synthetic_old_gate_regression():
    base = {"kind": "full_spectrum_isolated_gap_minimum", "q": 2.75, "cell_over_core": 15.6, "gap": 1e-3}
    cases = []
    for axis, vals in [
        ("resolution", [(64, 2.750), (96, 2.755)]),
        ("image_shell", [(2, 2.751), (3, 2.754)]),
        ("fd_eps", [(3e-4, 2.749), (1e-4, 2.752), (3e-5, 2.756)]),
    ]:
        for v, q in vals:
            cases.append({"axis": axis, "case": str(v), "value": v, "result": {"refined_primary_candidates": [{**base, "q": q}]}})
    clusters = evaluate_gap_convergence(cases, 0.02)
    return {"n_clusters": len(clusters), "promoted": bool(clusters and clusters[0]["promote_converged_candidate"])}


def _block_circulant(n: int) -> np.ndarray:
    J = np.zeros((2 * n, 2 * n), dtype=float)
    A0 = np.array([[0.15, -0.40], [0.35, -0.05]])
    Ap = np.array([[0.04, 0.02], [-0.01, 0.03]])
    Am = np.array([[-0.02, 0.01], [0.03, -0.01]])
    for j in range(n):
        sl = slice(2 * j, 2 * j + 2)
        J[sl, sl] += A0
        kp = (j + 1) % n
        km = (j - 1) % n
        J[sl, slice(2 * kp, 2 * kp + 2)] += Ap
        J[sl, slice(2 * km, 2 * km + 2)] += Am
    return J


def _fourier_projection_regression():
    n = 16
    fs = FourierSettings(max_m=5, low_mode_leakage_max=1e-10, sector_leakage_max=1e-10)
    base = _block_circulant(n)
    p0 = project_low_fourier(base, n, fs)

    # Add a C4-symmetric local modulation. This intentionally mixes m with m+-4
    # while preserving the C4 residue sectors.
    J = base.copy()
    theta = 2.0 * np.pi * np.arange(n) / n
    B = np.array([[0.10, 0.0], [0.0, -0.06]])
    for j, th in enumerate(theta):
        sl = slice(2 * j, 2 * j + 2)
        J[sl, sl] += math.cos(4.0 * th) * B
    p4 = project_low_fourier(J, n, fs)
    diag_min = min(float(x["diagonal_fraction"]) for x in p4["mode_blocks"])
    return {
        "circulant_low_mode_leakage": p0["low_mode_projection_leakage"],
        "circulant_c4_leakage": p0["c4_symmetry_leakage"],
        "c4_modulated_c4_leakage": p4["c4_symmetry_leakage"],
        "c4_modulated_min_diagonal_fraction": diag_min,
        "ok": bool(
            p0["low_mode_projection_leakage"] < 1e-10
            and p0["c4_symmetry_leakage"] < 1e-10
            and p4["c4_symmetry_leakage"] < 1e-10
            and diag_min < 0.999
        ),
    }


def _fourier_convergence_regression():
    def cand(q):
        return {
            "kind": "fourier_sector_isolated_abs_minimum",
            "sector": 2,
            "branch": 0,
            "dominant_abs_m": 2,
            "q": q,
            "cell_over_core": math.exp(q),
            "quality_gate": True,
        }

    cases = []
    for axis, vals in [
        ("resolution", [(64, 2.500), (96, 2.503), (128, 2.506)]),
        ("image_shell", [(2, 2.502), (3, 2.507)]),
        ("fd_eps", [(3e-4, 2.501), (1e-4, 2.504), (3e-5, 2.506)]),
    ]:
        for v, q in vals:
            cases.append({"axis": axis, "case": str(v), "value": v, "result": {"candidates": [cand(q)]}})
    clusters = evaluate_fourier_convergence(cases, q_cluster_tol=0.015, q_gate_tol=0.010)
    return {
        "n_clusters": len(clusters),
        "promoted": bool(clusters and clusters[0]["promote_converged_candidate"]),
        "ok": bool(len(clusters) == 1 and clusters[0]["promote_converged_candidate"]),
    }



def _c4_acceleration_regression():
    n=8; R=2.0; cell=math.exp(2.5); shell=1; h=1e-3
    full=np.asarray(fallback.ring_normal_jacobian(n,R,cell,shell,h,0,1,True),dtype=float)
    fast=np.asarray(fallback.ring_normal_jacobian_c4(n,R,cell,shell,h,0,1,True),dtype=float)
    rel=float(np.linalg.norm(full-fast)/max(np.linalg.norm(full),1e-300))
    audit=fallback.ring_c4_symmetry_audit(n,R,cell,shell,h,0,True)
    return {
        "relative_matrix_error": rel,
        "independent_rotated_column_audit": audit,
        "expected_column_reduction": 4,
        "ok": bool(rel < 1e-8 and audit["relative_error"] < 1e-8),
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="v0.1.2.3 dimensionless smoke, native/Python parity, Fourier/C4 and performance regressions.")
    ap.add_argument("--out-dir", default="audit_checks")
    ap.add_argument("--force-build", action="store_true")
    ap.add_argument("--threads", type=int, default=1)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cfg = {
        "n_nodes": 8,
        "ring_radius_over_core": 2.0,
        "q_min": 2.0,
        "q_max": 3.0,
        "q_step": 0.5,
        "image_shell": 1,
        "fd_eps_over_core": 1e-3,
        "core_model": 0,
        "threads": args.threads,
        "neutral_modes": 6,
        "eig_zero_tol": 1e-8,
        "residual_max": 0.2,
    }
    manifest = independence_manifest(cfg)
    manifest["protocol"] = "dimensionless-blind-v1.2"
    write_json(out / "independence_manifest.json", manifest)

    q = 2.5
    primary = spectrum_at_q(cfg, q, force_build=args.force_build)
    py = spectrum_at_q(cfg, q, force_python=True)
    native_available = primary["backend"] == "cpp"
    parity = {"native_backend_available": native_available}
    if native_available:
        parity.update({
            "gap_rel": abs(primary["gap_after_neutral"] - py["gap_after_neutral"]) / max(abs(py["gap_after_neutral"]), 1e-12),
            "sigma_abs": abs(primary["spectral_abscissa"] - py["spectral_abscissa"]),
            "interaction_norm_rel": abs(primary["interaction_jacobian_norm"] - py["interaction_jacobian_norm"]) / max(abs(py["interaction_jacobian_norm"]), 1e-12),
        })
        parity["ok"] = parity["gap_rel"] < 2e-5 and parity["sigma_abs"] < 2e-5 and parity["interaction_norm_rel"] < 2e-5
    else:
        parity.update({"ok": None, "note": "Native extension unavailable in this environment; Python reference path passed."})
    write_json(out / "backend_parity.json", {"primary": primary, "python": py, "parity": parity})

    iso = spectrum_at_q({**cfg, "image_shell": 0}, 3.0, force_python=True)
    isolation = {"interaction_norm": iso["interaction_jacobian_norm"], "ok": iso["interaction_jacobian_norm"] == 0.0}
    write_json(out / "isolation_probe.json", isolation)

    noise_cfg = {**cfg, "fd_eps_over_core": 1e-4}
    strong = spectrum_at_q(noise_cfg, 3.0, force_python=True)
    weak = spectrum_at_q(noise_cfg, 8.0, force_python=True)
    noise_gate = {
        "strong_ratio": strong["neutral_signal_to_fd_floor"],
        "strong_gate": strong["neutral_signal_gate_ok"],
        "weak_ratio": weak["neutral_signal_to_fd_floor"],
        "weak_gate": weak["neutral_signal_gate_ok"],
        "ok": bool(strong["neutral_signal_gate_ok"] and not weak["neutral_signal_gate_ok"]),
    }
    write_json(out / "roundoff_gate_probe.json", noise_gate)

    fourier_proj = _fourier_projection_regression()
    write_json(out / "fourier_projection_regression.json", fourier_proj)
    fourier_conv = _fourier_convergence_regression()
    write_json(out / "fourier_convergence_regression.json", fourier_conv)
    c4_accel = _c4_acceleration_regression()
    write_json(out / "c4_acceleration_regression.json", c4_accel)
    old_conv = _synthetic_old_gate_regression()
    write_json(out / "legacy_convergence_regression.json", old_conv)

    # Small physical reference probe: checks C4 leakage and finite values without using any external scale.
    fcfg = {**cfg, "q_min": 2.0, "q_max": 2.000001, "q_step": 1.0, "neutral_modes": 4, "fd_eps_over_core": 1e-3}
    fprobe = fourier_scan(
        fcfg,
        FourierSettings(max_m=3, low_mode_leakage_max=1.0, sector_leakage_max=1e-8),
        force_python=True,
        progress=False,
    )
    physical_fourier_ok = bool(
        len(fprobe["rows"]) == 1
        and math.isfinite(fprobe["rows"][0]["low_mode_projection_leakage"])
        and fprobe["rows"][0]["c4_symmetry_leakage"] < 1e-8
    )
    write_json(out / "fourier_physical_probe.json", {"row": fprobe["rows"][0], "ok": physical_fourier_ok})

    summary = {
        "dimensionless_manifest_ok": manifest["dimensionless_only"] and not manifest["external_physical_constants_used"] and not manifest["external_target_values_used"],
        "python_reference_ok": math.isfinite(py["gap_after_neutral"]) and math.isfinite(py["spectral_abscissa"]),
        "native_backend_available": native_available,
        "backend_parity_ok": parity["ok"],
        "isolation_probe_ok": isolation["ok"],
        "roundoff_gate_ok": noise_gate["ok"],
        "fourier_projection_regression_ok": fourier_proj["ok"],
        "fourier_convergence_regression_ok": fourier_conv["ok"],
        "c4_acceleration_regression_ok": c4_accel["ok"],
        "fourier_physical_probe_ok": physical_fourier_ok,
        "legacy_convergence_regression_ok": old_conv["promoted"],
    }
    required = [
        "dimensionless_manifest_ok",
        "python_reference_ok",
        "isolation_probe_ok",
        "roundoff_gate_ok",
        "fourier_projection_regression_ok",
        "fourier_convergence_regression_ok",
        "c4_acceleration_regression_ok",
        "fourier_physical_probe_ok",
        "legacy_convergence_regression_ok",
    ]
    summary["ok"] = all(bool(summary[k]) for k in required) and parity["ok"] is not False
    write_json(out / "audit_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

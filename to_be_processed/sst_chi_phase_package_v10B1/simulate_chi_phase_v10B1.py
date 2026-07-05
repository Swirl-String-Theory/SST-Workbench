#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST chi-phase package v10B.1 — simulation runner.

Runs the corrected Track B GP/NLSE vortex-ring constant extraction and writes:
  - chi_v10B1_core_constants.csv
  - chi_v10B1_convergence.csv
  - chi_v10B1_asymptotic_fit.csv
  - chi_v10B1_profile_comparison.csv
  - chi_v10B1_euler_benchmark.csv
  - chi_v10B1_energy_consistency.csv
  - chi_v10B1_convergence.png
  - chi_v10B1_run_results_summary.txt
"""
from __future__ import annotations

import argparse
import csv
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sst_chi_phase_v10B1_py as v10b

EXPORTS = Path(__file__).parent / "exports"
EXPORTS.mkdir(exist_ok=True)


def write_csv(path: Path, rows: list, fieldnames: list | None = None) -> None:
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def make_plot(rows: list[dict], path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    R = [row["R_max"] for row in rows]
    alpha_corr = [row["alpha_GP_corrected"] for row in rows]
    alpha_old = [row["alpha_GP_v10B0_coeff"] for row in rows]
    fig = plt.figure(figsize=(7.5, 4.8))
    ax = fig.add_subplot(111)
    ax.plot(R, alpha_corr, marker="o", label="v10B.1 corrected")
    ax.plot(R, alpha_old, marker="x", label="v10B.0 coefficient")
    ax.axhline(v10b.NLS_ALPHA_LEGACY, linestyle="--", label="legacy NLS 1.61")
    ax.axhline(v10b.PHI, linestyle=":", label="phi")
    ax.set_xlabel("R_max / xi")
    ax.set_ylabel("alpha_ring")
    ax.set_title("Track B GP/NLSE ring-constant convergence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r-right", type=float, default=80.0)
    ap.add_argument("--r-eval", type=float, default=12.0)
    ap.add_argument("--n-init", type=int, default=1600)
    ap.add_argument("--tol", type=float, default=1e-8)
    args = ap.parse_args()

    t0 = time.perf_counter()
    print("SST chi-phase Track B v10B.1: corrected GP/NLSE alpha_ring extraction")
    print("=" * 76)
    print("Solving GP vortex ODE (BVP)...")
    data = v10b.run_track_b(r_right=args.r_right, R_eval=args.r_eval,
                            n_init=args.n_init, tol=args.tol)
    elapsed = time.perf_counter() - t0

    cr = data["core_results_corrected_R_eval"]
    old = data["core_results_v10B0_coeff_R_eval"]
    fit12 = data["asymptotic_fit_minR12"]
    fit20 = data["asymptotic_fit_minR20"]
    ec = data["energy_consistency"]

    print(f"  BVP success: {data['success']}, nodes: {data['n_nodes_bvp']}, r_right={data['r_right']}")
    print(f"  C1* axis slope = {data['C1_star']:.7f}  (Pade: {data['pade_C1_star']:.7f})")
    print()
    print("Energy coefficient consistency:")
    print(f"  ODE nonlinear coefficient      = {ec['ODE_nonlinear_coeff']:.3f}")
    print(f"  expected energy coefficient    = {ec['energy_interaction_coeff_expected']:.3f}")
    print(f"  used energy coefficient        = {ec['energy_interaction_coeff_used']:.3f}")
    print(f"  v10B.0 used                    = {ec['v10B0_coeff']:.3f}")
    print(f"  consistency check              = {ec['coeff_consistent']}")
    print()
    print(f"Corrected core constant decomposition (R_max={cr['R_max_used']:.1f}):")
    print(f"  C_kin   = {cr['C_kin']:.7f}")
    print(f"  C_grad  = {cr['C_grad']:.7f}")
    print(f"  C_int   = {cr['C_int']:.7f}  [coefficient 1/2]")
    print(f"  C_GP    = {cr['C_GP']:.7f}")
    print(f"  alpha   = {cr['alpha_GP_a_eq_xi']:.7f}")
    print(f"  beta(q=0)= {cr['beta_GP_q0_a_eq_xi']:.7f}")
    print()
    print("For comparison, v10B.0 coefficient 1/4 at same R_max:")
    print(f"  alpha_old = {old['alpha_GP_a_eq_xi']:.7f}")
    print()
    print("Asymptotic algebraic-tail fits:")
    print(f"  minR=12: alpha_inf={fit12['alpha_inf']:.9f}, beta={fit12['beta_inf_q0']:.9f}, rms={fit12['fit_rms']:.2e}")
    print(f"  minR=20: alpha_inf={fit20['alpha_inf']:.9f}, beta={fit20['beta_inf_q0']:.9f}, rms={fit20['fit_rms']:.2e}")
    print()
    print(f"Legacy NLS target: alpha={v10b.NLS_ALPHA_LEGACY:.5f}, beta={v10b.NLS_BETA_LEGACY:.5f}")
    print(f"  delta alpha_inf(minR12)-NLS = {fit12['delta_alpha_inf_minus_NLS']:+.6f}")
    print(f"  delta beta_inf(minR12)-NLS  = {fit12['delta_beta_inf_minus_NLS']:+.6f}")
    print(f"  phi comparison: alpha_inf-phi = {fit12['alpha_inf']-v10b.PHI:+.6f}")
    print()

    write_csv(EXPORTS / "chi_v10B1_core_constants.csv", [cr])
    write_csv(EXPORTS / "chi_v10B1_core_constants_v10B0_coeff_comparison.csv", [old])
    write_csv(EXPORTS / "chi_v10B1_convergence.csv", data["convergence"])
    write_csv(EXPORTS / "chi_v10B1_asymptotic_fit.csv", [fit12, fit20])
    write_csv(EXPORTS / "chi_v10B1_profile_comparison.csv", data["profile"])
    write_csv(EXPORTS / "chi_v10B1_euler_benchmark.csv", data["euler_benchmark"])
    write_csv(EXPORTS / "chi_v10B1_energy_consistency.csv", [ec])
    make_plot(data["convergence"], EXPORTS / "chi_v10B1_convergence.png")

    summary = [
        "SST chi-phase package v10B.1 summary",
        "=" * 56,
        "",
        "Track: B — corrected GP/NLSE core energy solver",
        "Status: Research Track / CANON-compatible effective-core model",
        "",
        "Critical patch from v10B.0:",
        "  v10B.0 used interaction term (F^2-1)^2 r / 4.",
        "  For the solved ODE F''+F'/r-F/r^2+F(1-F^2)=0, variation requires",
        "  interaction term (F^2-1)^2 r / 2.",
        "",
        f"BVP success: {data['success']}",
        f"BVP nodes:   {data['n_nodes_bvp']}",
        f"C1* axis slope: {data['C1_star']:.7e}",
        "",
        f"Corrected C_GP at R={cr['R_max_used']:.1f}: {cr['C_GP']:.7e}",
        f"  C_kin:  {cr['C_kin']:.7e}",
        f"  C_grad: {cr['C_grad']:.7e}",
        f"  C_int:  {cr['C_int']:.7e}  [coefficient 1/2]",
        f"alpha_GP corrected at R={cr['R_max_used']:.1f}: {cr['alpha_GP_a_eq_xi']:.7e}",
        f"beta_GP q=0 corrected at R={cr['R_max_used']:.1f}: {cr['beta_GP_q0_a_eq_xi']:.7e}",
        "",
        f"v10B.0 coefficient comparison at R={old['R_max_used']:.1f}: alpha={old['alpha_GP_a_eq_xi']:.7e}",
        "",
        "Asymptotic fit C(R)=C_inf+A/R^2+B/R^4:",
        f"  minR=12: C_inf={fit12['C_inf']:.7e}, alpha_inf={fit12['alpha_inf']:.9f}, beta_inf={fit12['beta_inf_q0']:.9f}, rms={fit12['fit_rms']:.2e}",
        f"  minR=20: C_inf={fit20['C_inf']:.7e}, alpha_inf={fit20['alpha_inf']:.9f}, beta_inf={fit20['beta_inf_q0']:.9f}, rms={fit20['fit_rms']:.2e}",
        "",
        f"Legacy NLS alpha: {v10b.NLS_ALPHA_LEGACY:.5f}",
        f"Legacy NLS beta:  {v10b.NLS_BETA_LEGACY:.5f}",
        f"delta alpha_inf(minR12)-NLS: {fit12['delta_alpha_inf_minus_NLS']:+.6e}",
        f"delta beta_inf(minR12)-NLS:  {fit12['delta_beta_inf_minus_NLS']:+.6e}",
        f"alpha_inf(minR12)-phi:       {fit12['alpha_inf']-v10b.PHI:+.6e}",
        "",
        "Conclusion:",
        "  v10B.1 reverses the v10B.0 interpretation. With the energy term consistent",
        "  with the GP/NLSE ODE, Track B gives alpha_ring near 1.619, i.e. close to",
        "  the legacy NLS value 1.61. This is a positive Research Track result, not yet",
        "  locked CANON because the normalization/convention and asymptotic extraction",
        "  still require independent review.",
        "",
        f"Elapsed: {elapsed:.2f} s",
    ]
    (EXPORTS / "chi_v10B1_run_results_summary.txt").write_text("\n".join(summary) + "\n")

    print(f"Exports written to: {EXPORTS}")
    print(f"Elapsed: {elapsed:.2f} s")


if __name__ == "__main__":
    main()

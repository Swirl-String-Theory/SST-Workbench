#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simulation runner for SST chi-phase package v11B.0."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sst_chi_phase_v11B0_py as v11b

EXPORTS = Path(__file__).parent / "exports"
EXPORTS.mkdir(exist_ok=True)


def write_csv(path: Path, rows: list, fieldnames: list | None = None) -> None:
    if not rows:
        return
    if fieldnames is None:
        # preserve order while taking union
        keys = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
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
    alpha = [row["alpha_ring_a_eq_xi"] for row in rows]
    fig = plt.figure(figsize=(7.5, 4.8))
    ax = fig.add_subplot(111)
    ax.plot(R, alpha, marker="o", label="v11B.0 SST->GP envelope")
    ax.axhline(v11b.NLS_ALPHA_LEGACY, linestyle="--", label="legacy NLS 1.61")
    ax.axhline(v11b.PHI, linestyle=":", label="phi")
    ax.set_xlabel("R_max / xi")
    ax.set_ylabel("alpha_ring")
    ax.set_title("v11B.0 core-envelope GP/NLSE alpha_ring convergence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r-right", type=float, default=80.0)
    ap.add_argument("--r-eval", type=float, default=15.5)
    ap.add_argument("--n-init", type=int, default=1600)
    ap.add_argument("--tol", type=float, default=1e-8)
    args = ap.parse_args()

    t0 = time.perf_counter()
    print("SST chi-phase package v11B.0")
    print("Track B: SST core-envelope -> GP/NLSE vortex ODE reduction audit")
    print("=" * 78)
    data = v11b.run_v11B0(r_right=args.r_right, R_eval=args.r_eval,
                          n_init=args.n_init, tol=args.tol)
    elapsed = time.perf_counter() - t0

    core = data["core_results"]
    fit12 = data["asymptotic_fit_minR12"]
    fit20 = data["asymptotic_fit_minR20"]
    residual = data["residual"]
    el = data["euler_lagrange"][0]

    print(f"BVP success: {data['success']}  nodes={data['n_nodes_bvp']}  C1*={data['C1_star']:.8f}")
    print("Euler-Lagrange reduction:")
    print(f"  k_phase = B/A*n^2 = {el['k_phase_B_over_A_n2']:.6f}")
    print(f"  k_nonlinear = C/A = {el['k_nonlinear_C_over_A']:.6f}")
    print(f"  energy interaction coeff = C/(2A) = {el['energy_interaction_coeff_C_over_2A']:.6f}")
    print(f"  GP locked: {el['gp_ode_locked']}")
    print()
    print(f"Core constants at R={core['R_max_used']:.1f}:")
    print(f"  C_core = {core['C_core']:.9f}")
    print(f"  alpha_ring = {core['alpha_ring_a_eq_xi']:.9f}")
    print(f"  beta_ring(q=0) = {core['beta_ring_q0']:.9f}")
    print()
    print("Asymptotic fits:")
    print(f"  minR=12: alpha_inf={fit12['alpha_inf']:.9f}, beta={fit12['beta_inf_q0']:.9f}, rms={fit12['fit_rms']:.2e}")
    print(f"  minR=20: alpha_inf={fit20['alpha_inf']:.9f}, beta={fit20['beta_inf_q0']:.9f}, rms={fit20['fit_rms']:.2e}")
    print(f"  delta alpha_inf(minR12)-legacy NLS = {fit12['delta_alpha_inf_minus_NLS']:+.6e}")
    print(f"  alpha_inf(minR12)-phi = {fit12['alpha_inf_minus_phi']:+.6e}")
    print()
    print(f"ODE residual smoke-test RMS={residual['residual_rms']:.3e}, max={residual['residual_max_abs']:.3e}")

    write_csv(EXPORTS / "chi_v11B0_euler_lagrange_reduction.csv", data["euler_lagrange"])
    write_csv(EXPORTS / "chi_v11B0_energy_consistency.csv", data["energy_consistency"])
    write_csv(EXPORTS / "chi_v11B0_coefficient_scan.csv", data["coefficient_scan"])
    write_csv(EXPORTS / "chi_v11B0_core_constants.csv", [core])
    write_csv(EXPORTS / "chi_v11B0_convergence.csv", data["convergence"])
    write_csv(EXPORTS / "chi_v11B0_asymptotic_fit.csv", [fit12, fit20])
    write_csv(EXPORTS / "chi_v11B0_residual.csv", [residual])
    make_plot(data["convergence"], EXPORTS / "chi_v11B0_convergence.png")

    # Full JSON for precise downstream audits.
    with open(EXPORTS / "chi_v11B0_results.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

    summary = [
        "SST chi-phase package v11B.0 summary",
        "=" * 56,
        "",
        "Track: B — SST core-envelope -> GP/NLSE reduction audit",
        "Status: Strong Research Track / derived-conditional; not locked CANON",
        "",
        "Purpose:",
        "  v10B.1 computed alpha_ring^GP after fixing the energy coefficient.",
        "  v11B.0 tests the next canon gate: whether the used GP/NLSE ODE follows",
        "  as the Euler-Lagrange equation of a canonical SST core-envelope energy.",
        "",
        "Core-envelope functional:",
        "  L = A F'^2 r + B n^2 F^2/r + (C/2)(F^2-1)^2 r",
        "",
        "Euler-Lagrange result:",
        "  F'' + F'/r - (B/A)n^2 F/r^2 + (C/A)F(1-F^2)=0",
        "",
        f"Canonical GP lock: A=B=C, n=1 -> {el['gp_ode_locked']}",
        f"  k_phase={el['k_phase_B_over_A_n2']:.7e}",
        f"  k_nonlinear={el['k_nonlinear_C_over_A']:.7e}",
        f"  energy interaction coefficient={el['energy_interaction_coeff_C_over_2A']:.7e}",
        "",
        f"BVP success: {data['success']}",
        f"BVP nodes: {data['n_nodes_bvp']}",
        f"C1* axis slope: {data['C1_star']:.7e}",
        "",
        f"Corrected C_core at R={core['R_max_used']:.1f}: {core['C_core']:.7e}",
        f"  C_kin:       {core['C_kin_log_subtracted']:.7e}",
        f"  C_grad:      {core['C_grad']:.7e}",
        f"  C_depletion: {core['C_depletion']:.7e}",
        f"alpha_ring at R={core['R_max_used']:.1f}: {core['alpha_ring_a_eq_xi']:.9f}",
        f"beta_ring(q=0):        {core['beta_ring_q0']:.9f}",
        "",
        "Asymptotic fit C(R)=C_inf+A/R^2+B/R^4:",
        f"  minR=12: C_inf={fit12['C_inf']:.7e}, alpha_inf={fit12['alpha_inf']:.9f}, beta_inf={fit12['beta_inf_q0']:.9f}, rms={fit12['fit_rms']:.2e}",
        f"  minR=20: C_inf={fit20['C_inf']:.7e}, alpha_inf={fit20['alpha_inf']:.9f}, beta_inf={fit20['beta_inf_q0']:.9f}, rms={fit20['fit_rms']:.2e}",
        "",
        f"Legacy NLS alpha: {v11b.NLS_ALPHA_LEGACY:.5f}",
        f"Legacy NLS beta:  {v11b.NLS_BETA_LEGACY:.5f}",
        f"delta alpha_inf(minR12)-NLS: {fit12['delta_alpha_inf_minus_NLS']:+.6e}",
        f"alpha_inf(minR12)-phi:       {fit12['alpha_inf_minus_phi']:+.6e}",
        "",
        "Conclusion:",
        "  v11B.0 supplies the variational bridge missing from v10B.1: the solved",
        "  GP/NLSE vortex equation follows from a core-envelope energy iff SST locks",
        "  the radial-gradient, phase-gradient, and depletion stiffnesses as A=B=C.",
        "  Therefore alpha_ring^GP is derived-conditional. To upgrade to locked CANON,",
        "  a separate SST canon lemma must establish A=B=C rather than importing it as",
        "  an effective GP/NLSE closure.",
        "",
        f"Elapsed: {elapsed:.2f} s",
    ]
    (EXPORTS / "chi_v11B0_run_results_summary.txt").write_text("\n".join(summary) + "\n")

    print(f"Exports written to: {EXPORTS}")
    print(f"Elapsed: {elapsed:.2f} s")


if __name__ == "__main__":
    main()

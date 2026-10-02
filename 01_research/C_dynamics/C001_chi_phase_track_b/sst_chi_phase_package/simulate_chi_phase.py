#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase χ: verify internal torsional phase speed and horn-loop spectrum.

Research Track target:
    I_chi = rho_f ∫_A r_perp² dA
    K_chi = rho_f v_swirl² ∫_A r_perp² dA
    c_chi² = K_chi / I_chi -> v_swirl²

This script is self-contained in the same style as simulate_macro_wake.py:
    python simulate_chi_phase.py
It auto-builds the local pybind11 extension if needed, exports CSV files, and
writes diagnostic plots into ./exports/.
"""

from __future__ import annotations

import csv
import os
import time

import matplotlib.pyplot as plt
import numpy as np

from sst_chi_phase_build import MODULE_NAME, ensure_module

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

try:
    ensure_module(SCRIPT_DIR)
    import sst_chi_phase
except ImportError as exc:
    print(f"[!] C++ extension unavailable ({exc}). Using pure-Python fallback.")
    import sst_chi_phase_py as sst_chi_phase

# ==========================================================================
# SST Canonical Constants
# ==========================================================================
C = 2.99792458e8
ALPHA = 7.2973525693e-3
M_E = 9.1093837015e-31
HBAR = 1.054571817e-34

RHO_F = 7.0e-7  # kg m^-3, SST effective fluid density
V_SWIRL = ALPHA * C / 2.0
OMEGA_C = (M_E * C**2) / HBAR
R_C = V_SWIRL / OMEGA_C

# Main numerical controls
N_R = 800
N_THETA = 360
N_GRID = 4096
N_MAX = 32


def ensure_export_dir() -> str:
    export_dir = os.path.join(SCRIPT_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def run_cross_section_sweep(export_dir: str):
    print("[*] Cross-section sweep: I_chi, K_chi, c_chi/v_swirl")
    a_factors = np.array([0.05, 0.10, 0.25, 0.50, 1.00, 2.00, 4.00, 10.00], dtype=float)

    rows = []
    for factor in a_factors:
        a_core = float(factor * R_C)
        result = sst_chi_phase.compute_chi_constants(
            RHO_F,
            V_SWIRL,
            a_core,
            N_R,
            N_THETA,
        )
        row = {k: float(v) for k, v in result.items()}
        row["a_core_over_rc"] = factor
        rows.append(row)
        print(
            f"    a/r_c={factor:6.3f} | "
            f"c_num/v={row['c_chi_over_v_numeric']:.12f} | "
            f"J_rel_err={row['J_rel_error']:+.3e}"
        )

    csv_path = os.path.join(export_dir, "chi_phase_speed_sweep.csv")
    fieldnames = [
        "a_core_over_rc",
        "a_core",
        "J_analytic",
        "J_numeric",
        "J_rel_error",
        "I_chi_analytic",
        "K_chi_analytic",
        "c_chi_analytic",
        "c_chi_over_v_analytic",
        "I_chi_numeric",
        "K_chi_numeric",
        "c_chi_numeric",
        "c_chi_over_v_numeric",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: f"{row[name]:.16e}" for name in fieldnames})
    print(f"[*] CSV saved: {csv_path}")

    # Plot speed ratio
    x = np.array([row["a_core_over_rc"] for row in rows])
    y = np.array([row["c_chi_over_v_numeric"] for row in rows])
    jerr = np.abs(np.array([row["J_rel_error"] for row in rows]))

    plt.figure(figsize=(9, 5))
    plt.semilogx(x, y, "o-", label="numerical c_chi/v_swirl")
    plt.axhline(1.0, color="k", linestyle="--", label="analytic target")
    plt.xlabel(r"$a_{\rm core}/r_c$")
    plt.ylabel("c_chi / v_swirl")
    plt.title("Internal torsional phase speed: c_chi^2 = K_chi / I_chi")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_phase_speed_sweep.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    plt.figure(figsize=(9, 5))
    plt.loglog(x, jerr, "s-", label=r"$|J_{num}/J_{ana}-1|$")
    plt.xlabel(r"$a_{\rm core}/r_c$")
    plt.ylabel("absolute relative error")
    plt.title("Quadrature error for transverse moment integral")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_cross_section_moment_error.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    max_speed_error = float(np.max(np.abs(y - 1.0)))
    max_moment_error = float(np.max(jerr))
    return max_speed_error, max_moment_error, csv_path


def run_horn_loop_spectrum(export_dir: str):
    print("[*] Horn-loop spectrum test: L_chi = 2π r_c")
    l_chi = 2.0 * np.pi * R_C

    omega_cont = np.array(
        sst_chi_phase.continuous_phase_spectrum(V_SWIRL, float(l_chi), N_MAX, 0.0),
        dtype=float,
    )
    omega_disc = np.array(
        sst_chi_phase.discrete_phase_spectrum(V_SWIRL, float(l_chi), N_GRID, N_MAX, 0.0),
        dtype=float,
    )
    n = np.arange(1, N_MAX + 1, dtype=float)
    target = n * OMEGA_C

    ratio_cont = omega_cont / target
    ratio_disc = omega_disc / target

    csv_path = os.path.join(export_dir, "chi_horn_loop_spectrum.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "n",
            "omega_continuous_rad_s",
            "omega_discrete_rad_s",
            "target_n_omega_c_rad_s",
            "continuous_ratio",
            "discrete_ratio",
            "discrete_rel_error",
        ])
        for i in range(N_MAX):
            writer.writerow([
                int(n[i]),
                f"{omega_cont[i]:.16e}",
                f"{omega_disc[i]:.16e}",
                f"{target[i]:.16e}",
                f"{ratio_cont[i]:.16e}",
                f"{ratio_disc[i]:.16e}",
                f"{(ratio_disc[i] - 1.0):+.16e}",
            ])
    print(f"[*] CSV saved: {csv_path}")

    plt.figure(figsize=(9, 5))
    plt.plot(n, ratio_cont, "k--", label="continuous exact")
    plt.plot(n, ratio_disc, "ro-", label=f"finite difference, N={N_GRID}")
    plt.axhline(1.0, color="k", linewidth=0.8)
    plt.xlabel("mode number n")
    plt.ylabel("omega_n / (n omega_c)")
    plt.title("Horn-loop internal phase spectrum: L_chi = 2*pi*r_c")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_horn_loop_spectrum.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    max_disc_error = float(np.max(np.abs(ratio_disc - 1.0)))
    omega1_ratio = float(ratio_disc[0])
    return max_disc_error, omega1_ratio, csv_path


def main():
    print("=" * 78)
    print("SST internal torsional phase verification package")
    print("=" * 78)
    print(f"[*] Module: {MODULE_NAME}")
    print(f"[*] rho_f  = {RHO_F:.8e} kg m^-3")
    print(f"[*] v_swirl= {V_SWIRL:.8e} m s^-1")
    print(f"[*] omega_c= {OMEGA_C:.8e} s^-1")
    print(f"[*] r_c    = {R_C:.8e} m")
    print("[*] Status: Research Track sanity test, not a gauge or mass proof.")

    export_dir = ensure_export_dir()
    t0 = time.time()

    max_speed_error, max_moment_error, speed_csv = run_cross_section_sweep(export_dir)
    max_spectrum_error, omega1_ratio, spectrum_csv = run_horn_loop_spectrum(export_dir)

    elapsed = time.time() - t0
    print("=" * 78)
    print("Summary")
    print("=" * 78)
    print(f"max |c_chi/v_swirl - 1|        = {max_speed_error:.3e}")
    print(f"max |J_num/J_ana - 1|          = {max_moment_error:.3e}")
    print(f"omega_1/(omega_c), discrete    = {omega1_ratio:.12f}")
    print(f"max |omega_n/(n omega_c)-1|    = {max_spectrum_error:.3e}")
    print(f"speed sweep csv                = {speed_csv}")
    print(f"horn spectrum csv              = {spectrum_csv}")
    print(f"elapsed                        = {elapsed:.2f} s")

    # Assertions: strict for analytic speed cancellation, practical for numeric spectra.
    if max_speed_error > 1e-12:
        raise AssertionError("c_chi/v_swirl should cancel to machine precision.")
    if max_moment_error > 1e-5:
        raise AssertionError("Cross-section quadrature error exceeds tolerance.")
    if abs(omega1_ratio - 1.0) > 1e-6:
        raise AssertionError("Discrete omega_1 does not reproduce omega_c within tolerance.")
    if max_spectrum_error > 2e-4:
        raise AssertionError("Discrete phase-ring spectrum error exceeds tolerance.")

    print("[*] PASS: internal chi-phase speed and horn-loop spectrum verified.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SST chi-phase v4: four-profile core admissibility selector.

v1/v2 are archived as shared-moment arithmetic checks. v3 extracted profile-
dependent torsional stiffness. v4 adds explicit admissibility diagnostics for
four candidate radial profiles:

  1. uniform boundary
  2. solid-body boundary
  3. regularized 1/r boundary
  4. Gaussian core max

The package computes:
  I_chi = rho_f ∫ r_perp^2 dA
  K_chi = rho_f ∫ v_theta(r)^2 r_perp^2 dA
  c_chi = sqrt(K_chi/I_chi)
  Gamma(a) = 2π a v_theta(a)
  E_kin/L = 1/2 rho_f ∫ v_theta(r)^2 dA
  axis regularity, boundary circulation match, exterior 1/r slope match.

Outputs are written to ./exports.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import time
from typing import Any, Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
EXPORT_DIR = os.path.join(SCRIPT_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# Canonical constants used for scaling / reporting only.
C = 2.99792458e8
ALPHA = 7.2973525693e-3
M_E = 9.1093837015e-31
HBAR = 1.054571817e-34
RHO_F = 7.0e-7

V_SWIRL = ALPHA * C / 2.0
OMEGA_C = (M_E * C**2) / HBAR
R_C = V_SWIRL / OMEGA_C


def load_backend(force_python: bool = False):
    if force_python:
        import sst_chi_phase_v4_py as backend
        return backend, "python"
    try:
        from sst_chi_phase_v4_build import import_module
        backend = import_module(auto_build=True, script_dir=SCRIPT_DIR)
        return backend, "cpp"
    except Exception as exc:
        print(f"[!] C++ backend unavailable ({exc}). Falling back to pure Python.")
        import sst_chi_phase_v4_py as backend
        return backend, "python"


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"[*] CSV saved: {path}")


def params_repr(params: Dict[str, float]) -> str:
    if not params:
        return "{}"
    return ", ".join(f"{k}={v:g}" for k, v in sorted(params.items()))


def profile_set(backend, include_extended: bool = False):
    raw = backend.extended_profiles() if include_extended else backend.default_four_profiles()
    return [(str(p), str(n), dict(d), str(label)) for p, n, d, label in raw]


def run_admissibility(backend, include_extended: bool, n_radial: int) -> List[Dict[str, Any]]:
    print("[*] v4 four-profile core admissibility test")
    rows: List[Dict[str, Any]] = []
    for profile, norm, params, label in profile_set(backend, include_extended):
        row = dict(backend.profile_metrics(profile, R_C, RHO_F, V_SWIRL, norm, params, n_radial))
        row["label"] = label
        row["params_repr"] = params_repr(params)
        rows.append(row)
        print(
            f"    {label:42s} | c/v={row['c_over_v_ref']:.12f} | "
            f"Gamma/Gamma_ref={row['gamma_boundary_over_ref']:.6f} | "
            f"axis={int(row['axis_regular'])} boundary={int(row['boundary_matches'])} "
            f"slope={int(row['exterior_slope_matches'])} energy={int(row['finite_energy'])} | "
            f"score={int(row['admissibility_score'])}/4"
        )

    fields = [
        "label", "profile", "normalization", "params_repr", "calibration_mode",
        "a_core", "rho_f", "v_ref", "scale", "I_chi", "K_chi", "c_chi", "c_over_v_ref",
        "J_numeric", "J_analytic_disk", "J_rel_error", "Kgeom", "Kgeom_over_J",
        "Egeom", "energy_per_length", "gamma_boundary", "gamma_ref", "gamma_boundary_over_ref",
        "boundary_over_v", "center_over_v", "max_over_v", "boundary_log_slope",
        "axis_regular", "boundary_matches", "exterior_slope_matches", "finite_energy",
        "r2_rms_matches_ref", "admissibility_score", "n_radial",
    ]
    write_csv(os.path.join(EXPORT_DIR, "chi_v4_profile_admissibility.csv"), rows, fields)
    return rows


def plot_profiles(backend, rows: List[Dict[str, Any]]):
    xs = np.linspace(0, 1, 600)
    plt.figure(figsize=(12, 6))
    for row in rows:
        params = {}
        # Reconstruct params from label/profile for plotting.
        if row["profile"] == "irrotational_reg":
            params = {"eps": 0.05}
        elif row["profile"] == "gaussian_core":
            params = {"sigma": 0.35}
        elif row["profile"] == "rankine_matched":
            params = {"core": 0.35}
        scale = float(row["scale"])
        ys = [scale * backend.raw_profile(str(row["profile"]), float(x), params) for x in xs]
        plt.plot(xs, ys, label=row["label"])
    plt.xlabel(r"$x=r/a_{core}$")
    plt.ylabel(r"$v_\theta(r)/v_{ref}$")
    plt.title("v4 radial core profiles after selected normalization")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_profiles.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def plot_speed_and_energy(rows: List[Dict[str, Any]]):
    labels = [r["label"] for r in rows]
    x = np.arange(len(rows))
    c_ratios = np.array([float(r["c_over_v_ref"]) for r in rows])
    energy = np.array([float(r["energy_per_length"]) for r in rows])
    gamma_ratio = np.array([float(r["gamma_boundary_over_ref"]) for r in rows])

    plt.figure(figsize=(12, 6))
    plt.bar(x, c_ratios)
    plt.axhline(1.0, color="k", linestyle="--", label=r"$c_\chi/v_{ref}=1$")
    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel(r"$c_\chi/v_{ref}$")
    plt.title("v4 profile-derived torsional phase speed")
    plt.legend()
    plt.grid(axis="y", alpha=0.4)
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_profile_speed_ratio.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")

    plt.figure(figsize=(12, 6))
    plt.bar(x, energy / energy[0])
    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel(r"$(E_{kin}/L)/(E_{uniform}/L)$")
    plt.title("v4 kinetic energy per length relative to uniform profile")
    plt.grid(axis="y", alpha=0.4)
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_energy_per_length_ratio.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")

    plt.figure(figsize=(12, 6))
    plt.bar(x, gamma_ratio)
    plt.axhline(1.0, color="k", linestyle="--", label=r"$\Gamma(a)=2\pi a v_{ref}$")
    plt.xticks(x, labels, rotation=25, ha="right")
    plt.ylabel(r"$\Gamma(a)/\Gamma_{ref}$")
    plt.title("v4 boundary circulation matching")
    plt.legend()
    plt.grid(axis="y", alpha=0.4)
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_boundary_circulation.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def plot_admissibility(rows: List[Dict[str, Any]]):
    labels = [r["label"] for r in rows]
    tests = ["axis_regular", "boundary_matches", "exterior_slope_matches", "finite_energy", "r2_rms_matches_ref"]
    data = np.array([[int(r[t]) for t in tests] for r in rows], dtype=float)
    plt.figure(figsize=(11, 5.5))
    plt.imshow(data.T, aspect="auto", vmin=0, vmax=1)
    plt.yticks(np.arange(len(tests)), [t.replace("_", " ") for t in tests])
    plt.xticks(np.arange(len(labels)), labels, rotation=25, ha="right")
    plt.title("v4 admissibility matrix: 1=passes diagnostic, 0=fails")
    plt.colorbar(label="pass")
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_admissibility_matrix.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def run_spectra(backend, rows: List[Dict[str, Any]], n_max: int, n_grid: int) -> List[Dict[str, Any]]:
    print("[*] v4 horn-loop spectrum using profile-derived c_chi")
    out: List[Dict[str, Any]] = []
    plt.figure(figsize=(12, 6))
    for row in rows:
        spec = backend.horn_loop_frequency_ratios(float(row["c_over_v_ref"]), n_max, n_grid)
        ns, vals = [], []
        for srow in spec:
            srow = dict(srow)
            srow["label"] = row["label"]
            srow["profile"] = row["profile"]
            srow["normalization"] = row["normalization"]
            srow["c_over_v_ref"] = row["c_over_v_ref"]
            out.append(srow)
            ns.append(srow["n"])
            vals.append(srow["fd_ratio"])
        plt.plot(ns, vals, marker="o", label=row["label"])
    plt.axhline(1.0, color="k", linestyle="--", label=r"$\omega_n/(n\omega_c)=1$")
    plt.xlabel("mode number n")
    plt.ylabel(r"$\omega_n/(n\omega_c)$")
    plt.title(r"v4 horn-loop spectra: only profiles with $c_\chi=v_{ref}$ sit on 1")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_profile_spectrum.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")

    write_csv(os.path.join(EXPORT_DIR, "chi_v4_profile_spectrum.csv"), out,
              ["label", "profile", "normalization", "c_over_v_ref", "n", "continuous_ratio", "fd_ratio", "fd_relative_error_vs_cont"])
    return out


def run_convergence(backend, n_max: int):
    rows = [dict(r) for r in backend.spectrum_convergence(1.0, n_max, [128,256,512,1024,2048,4096,8192])]
    write_csv(os.path.join(EXPORT_DIR, "chi_v4_spectrum_convergence.csv"), rows,
              ["N", "max_rel_error", "prediction", "c_over_v"])
    N = np.array([r["N"] for r in rows], dtype=float)
    err = np.array([r["max_rel_error"] for r in rows], dtype=float)
    pred = np.array([r["prediction"] for r in rows], dtype=float)
    plt.figure(figsize=(10, 6))
    plt.loglog(N, err, "o-", label="observed max error")
    plt.loglog(N, pred, "k--", label="central-difference prediction")
    plt.xlabel("periodic grid size N")
    plt.ylabel("max relative spectrum error")
    plt.title("v4 finite-difference convergence control")
    plt.legend()
    plt.grid(True, which="both")
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v4_spectrum_convergence.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")
    return rows


def write_summary(backend_name: str, rows: List[Dict[str, Any]], conv_rows: List[Dict[str, Any]], elapsed: float):
    best = max(rows, key=lambda r: int(r["admissibility_score"]))
    closest = min(rows, key=lambda r: abs(float(r["c_over_v_ref"]) - 1.0))
    summary_path = os.path.join(EXPORT_DIR, "chi_v4_run_results_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("SST chi-phase v4 four-profile core admissibility summary\n")
        f.write("=======================================================\n")
        f.write(f"backend                                      = {backend_name}\n")
        f.write(f"rho_f                                        = {RHO_F:.16e} kg m^-3\n")
        f.write(f"v_swirl                                      = {V_SWIRL:.16e} m s^-1\n")
        f.write(f"omega_c                                      = {OMEGA_C:.16e} s^-1\n")
        f.write(f"r_c                                          = {R_C:.16e} m\n\n")
        f.write("Key equation:\n")
        f.write("c_chi^2 = (int_A v_theta(r)^2 r_perp^2 dA) / (int_A r_perp^2 dA)\n\n")
        for r in rows:
            f.write(
                f"{r['label']:<44s} c/v={float(r['c_over_v_ref']):.16e} "
                f"Gamma/Gamma_ref={float(r['gamma_boundary_over_ref']):.8e} "
                f"slope={float(r['boundary_log_slope']):.8e} "
                f"score={int(r['admissibility_score'])}/4\n"
            )
        f.write("\n")
        f.write(f"best admissibility score profile              = {best['label']} ({int(best['admissibility_score'])}/4)\n")
        f.write(f"closest profile to c/v=1                      = {closest['label']} ({float(closest['c_over_v_ref']):.16e})\n")
        f.write(f"finest-grid FD convergence error              = {float(conv_rows[-1]['max_rel_error']):.16e}\n")
        f.write(f"elapsed                                      = {elapsed:.2f} s\n\n")
        f.write("Interpretation:\n")
        f.write("PASS means v4 successfully distinguishes profile-derived c_chi values and\n")
        f.write("documents which profiles satisfy axis regularity, boundary circulation,\n")
        f.write("exterior 1/r slope matching, and finite-energy diagnostics. It does not prove\n")
        f.write("Q_chi->Q_em or SU(2)/SU(3).\n")
    print(f"[*] Summary saved: {summary_path}")
    return summary_path


def main():
    parser = argparse.ArgumentParser(description="SST chi-phase v4 four-profile core admissibility selector")
    parser.add_argument("--python", action="store_true", help="force pure-Python backend")
    parser.add_argument("--extended", action="store_true", help="also include Rankine and calibration reference profiles")
    parser.add_argument("--n-radial", type=int, default=200000, help="radial midpoint samples")
    parser.add_argument("--n-grid", type=int, default=4096, help="periodic phase grid for spectrum")
    parser.add_argument("--n-max", type=int, default=32, help="max mode number")
    args = parser.parse_args()

    t0 = time.time()
    backend, backend_name = load_backend(args.python)

    print("=" * 84)
    print("SST chi-phase v4: four-profile core admissibility selector")
    print("=" * 84)
    print(f"[*] backend = {backend_name}")
    print(f"[*] rho_f   = {RHO_F:.8e} kg m^-3")
    print(f"[*] v_swirl = {V_SWIRL:.8e} m s^-1")
    print(f"[*] omega_c = {OMEGA_C:.8e} s^-1")
    print(f"[*] r_c     = {R_C:.8e} m")
    print("[*] Status: Research Track admissibility selector; v1/v2 archived as arithmetic checks.")

    rows = run_admissibility(backend, args.extended, args.n_radial)
    plot_profiles(backend, rows)
    plot_speed_and_energy(rows)
    plot_admissibility(rows)
    run_spectra(backend, rows, args.n_max, args.n_grid)
    conv_rows = run_convergence(backend, args.n_max)
    elapsed = time.time() - t0
    summary_path = write_summary(backend_name, rows, conv_rows, elapsed)

    print("=" * 84)
    print("Summary")
    print("=" * 84)
    for r in rows:
        print(f"{r['label']:<44s} c/v={float(r['c_over_v_ref']):.12f} score={int(r['admissibility_score'])}/4")
    print(f"summary = {summary_path}")
    print("[*] PASS: v4 admissibility tests completed successfully.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SST chi-phase package v6: smooth-matched polynomial root selector.

This script solves the condition c_chi/v_ref = 1 inside the smooth-matched
polynomial core family found in v5. It performs an analytic check, a bisection
root check, a comparison with the golden ratio, and simple energy diagnostics.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import time
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

from sst_chi_phase_v6_py import (
    A0_STAR_ANALYTIC,
    PHI,
    build_report_points,
    bisection_root,
    c_over_v_analytic,
    c2_over_v2_analytic,
    c2_over_v2_numeric,
    curvature_energy_analytic,
    energy_minima,
    grad_energy_analytic,
    point_result,
    profile_curve,
    root_residual,
    shape_energy_analytic,
    smooth_matched_poly,
    sweep_a0,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(SCRIPT_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# SST constants retained for continuity and report metadata only.
C = 2.99792458e8
ALPHA = 7.2973525693e-3
M_E = 9.1093837015e-31
HBAR = 1.054571817e-34
RHO_F = 7.0e-7
V_SWIRL = ALPHA * C / 2.0
OMEGA_C = (M_E * C**2) / HBAR
R_C = V_SWIRL / OMEGA_C


def try_cpp_backend(force_python: bool = False):
    if force_python:
        return None, "python-forced"
    try:
        from sst_chi_phase_v6_build import import_module
        return import_module(auto_build=True, script_dir=SCRIPT_DIR), "cpp"
    except Exception as exc:
        print(f"[!] C++ backend unavailable ({exc}). Using pure Python backend.")
        return None, "python-fallback"


def write_csv(path: str, rows: List[Dict[str, object]]):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[*] CSV saved: {path}")


def normalize(values: np.ndarray) -> np.ndarray:
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if abs(vmax - vmin) < 1e-30:
        return np.zeros_like(values)
    return (values - vmin) / (vmax - vmin)


def plot_root_sweep(rows: List[Dict[str, float]]):
    a = np.array([r["a0"] for r in rows], dtype=float)
    c = np.array([r["c_over_v"] for r in rows], dtype=float)
    residual = np.array([r["residual_c2_minus_1"] for r in rows], dtype=float)

    plt.figure(figsize=(10, 6))
    plt.plot(a, c, label=r"smooth-matched $c_\chi/v_{\rm ref}$")
    plt.axhline(1.0, color="k", linestyle="--", label=r"target $c_\chi/v=1$")
    plt.axvline(A0_STAR_ANALYTIC, color="r", linestyle="-", label=rf"$a_0^\star={A0_STAR_ANALYTIC:.6f}$")
    plt.axvline(PHI, color="g", linestyle=":", label=rf"$\varphi={PHI:.6f}$")
    plt.xlabel(r"$a_0$")
    plt.ylabel(r"$c_\chi/v_{\rm ref}$")
    plt.title("v6 smooth-matched root selector")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v6_root_sweep.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")

    plt.figure(figsize=(10, 5))
    plt.plot(a, residual, label=r"$(c_\chi/v)^2-1$")
    plt.axhline(0.0, color="k", linestyle="--")
    plt.axvline(A0_STAR_ANALYTIC, color="r", linestyle="-", label=r"analytic root")
    plt.axvline(PHI, color="g", linestyle=":", label=r"golden ratio")
    plt.xlabel(r"$a_0$")
    plt.ylabel("root residual")
    plt.title("v6 root residual")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v6_root_residual.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def plot_profiles():
    plt.figure(figsize=(10, 6))
    for label, a0 in [
        (r"$a_0^\star$", A0_STAR_ANALYTIC),
        (r"$\varphi$", PHI),
        (r"v5 $a_0=1.5$", 1.5),
        (r"v5 $a_0=2.0$", 2.0),
    ]:
        x, y = profile_curve(a0, n=1200)
        plt.plot(x, y, label=f"{label} ({a0:.6f})")
    plt.xlabel(r"$x=r/a_{\rm core}$")
    plt.ylabel(r"$f(x)=v_\theta(x)/v_{\rm ref}$")
    plt.title("v6 smooth-matched polynomial profiles")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v6_selected_profiles.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def plot_energy_diagnostics(rows: List[Dict[str, float]]):
    a = np.array([r["a0"] for r in rows], dtype=float)
    eg = normalize(np.array([r["grad_energy"] for r in rows], dtype=float))
    ec = normalize(np.array([r["curvature_energy"] for r in rows], dtype=float))
    es = normalize(np.array([r["shape_energy"] for r in rows], dtype=float))
    plt.figure(figsize=(10, 6))
    plt.plot(a, eg, label=r"normalized $\int f'^2 x dx$")
    plt.plot(a, ec, label=r"normalized $\int f''^2 x dx$")
    plt.plot(a, es, label=r"normalized $\int (f-x)^2 x dx$")
    plt.axvline(A0_STAR_ANALYTIC, color="r", linestyle="-", label=r"$c/v=1$ root")
    plt.axvline(PHI, color="g", linestyle=":", label=r"$\varphi$")
    mins = energy_minima()
    plt.axvline(mins["grad_energy_min_a0"], color="C0", linestyle="--", alpha=0.65)
    plt.axvline(mins["curvature_energy_min_a0"], color="C1", linestyle="--", alpha=0.65)
    plt.axvline(mins["shape_energy_min_a0"], color="C2", linestyle="--", alpha=0.65)
    plt.xlabel(r"$a_0$")
    plt.ylabel("normalized diagnostic")
    plt.title("v6 energy/smoothness diagnostics do not automatically select the root")
    plt.grid(True)
    plt.legend(fontsize=8)
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v6_energy_diagnostics.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def plot_point_comparison(points):
    labels = [p.label.replace("_", "\n") for p in points]
    values = [p.a0 for p in points]
    colors = ["tab:red" if "root" in p.label else "tab:green" if "golden" in p.label else "tab:blue" for p in points]
    plt.figure(figsize=(11, 5))
    plt.bar(range(len(points)), values, color=colors)
    plt.axhline(PHI, color="g", linestyle=":", label=r"$\varphi$")
    plt.axhline(A0_STAR_ANALYTIC, color="r", linestyle="--", label=r"$a_0^\star$")
    plt.xticks(range(len(points)), labels, rotation=0, fontsize=8)
    plt.ylabel(r"$a_0$")
    plt.title("v6 root, golden-ratio, and diagnostic selector locations")
    plt.grid(True, axis="y", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(EXPORT_DIR, "chi_v6_selector_locations.png")
    plt.savefig(path, dpi=150)
    print(f"[*] Plot saved: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", action="store_true", help="force pure-Python backend")
    parser.add_argument("--n", type=int, default=400000, help="midpoint quadrature points for numeric confirmation")
    parser.add_argument("--sweep-count", type=int, default=501)
    args = parser.parse_args()

    t0 = time.time()
    cpp_mod, backend = try_cpp_backend(args.python)

    print("=" * 88)
    print("SST chi-phase v6 smooth-matched polynomial root selector")
    print("=" * 88)
    print(f"[*] backend = {backend}")
    print(f"[*] rho_f   = {RHO_F:.8e} kg m^-3")
    print(f"[*] v_swirl = {V_SWIRL:.8e} m s^-1")
    print(f"[*] omega_c = {OMEGA_C:.8e} s^-1")
    print(f"[*] r_c     = {R_C:.8e} m")
    print("[*] Smooth-matched family: f=x[a0+(3-2a0)x^2+(a0-2)x^4]")

    a0_star = A0_STAR_ANALYTIC
    a0_bisect = bisection_root()
    if cpp_mod is not None:
        cpp_root = float(cpp_mod.bisection_root())
        cpp_analytic = float(cpp_mod.analytic_root())
    else:
        cpp_root = float("nan")
        cpp_analytic = float("nan")

    points = build_report_points(n=args.n)
    point_rows = [p.to_dict() for p in points]
    # Add backend comparisons as metadata rows by duplicating scalar values in a compact CSV.
    write_csv(os.path.join(EXPORT_DIR, "chi_v6_key_points.csv"), point_rows)

    sweep_rows = sweep_a0(0.0, 3.0, args.sweep_count)
    write_csv(os.path.join(EXPORT_DIR, "chi_v6_a0_sweep.csv"), sweep_rows)

    plot_root_sweep(sweep_rows)
    plot_profiles()
    plot_energy_diagnostics(sweep_rows)
    plot_point_comparison(points)

    phi_c = c_over_v_analytic(PHI)
    phi_c2 = c2_over_v2_analytic(PHI)
    star_numeric_c2 = c2_over_v2_numeric(a0_star, n=args.n)
    root_err = abs(a0_bisect - a0_star)
    phi_delta = a0_star - PHI
    elapsed = time.time() - t0

    summary_path = os.path.join(EXPORT_DIR, "chi_v6_run_results_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("SST chi-phase v6 smooth-matched polynomial root summary\n")
        f.write("=======================================================\n")
        f.write(f"backend                                      = {backend}\n")
        f.write(f"rho_f                                        = {RHO_F:.16e} kg m^-3\n")
        f.write(f"v_swirl                                      = {V_SWIRL:.16e} m s^-1\n")
        f.write(f"omega_c                                      = {OMEGA_C:.16e} s^-1\n")
        f.write(f"r_c                                          = {R_C:.16e} m\n\n")
        f.write("Smooth-matched family:\n")
        f.write("f_a(x) = x [ a0 + (3 - 2 a0) x^2 + (a0 - 2) x^4 ]\n")
        f.write("with f(0)=0, f(1)=1, f'(1)=-1.\n\n")
        f.write("Analytic result:\n")
        f.write("(c_chi/v_ref)^2 = (2 a0^2 + 13 a0 + 78) / 105\n")
        f.write("c_chi/v_ref = 1 -> 2 a0^2 + 13 a0 - 27 = 0\n\n")
        f.write(f"a0_star analytic                            = {a0_star:.16e}\n")
        f.write(f"a0_star bisection                           = {a0_bisect:.16e}\n")
        f.write(f"absolute root difference                    = {root_err:.16e}\n")
        if cpp_mod is not None:
            f.write(f"cpp analytic root                           = {cpp_analytic:.16e}\n")
            f.write(f"cpp bisection root                          = {cpp_root:.16e}\n")
        f.write(f"golden ratio phi                            = {PHI:.16e}\n")
        f.write(f"a0_star - phi                               = {phi_delta:.16e}\n")
        f.write(f"c(phi)/v_ref                                = {phi_c:.16e}\n")
        f.write(f"(c(phi)/v_ref)^2                            = {phi_c2:.16e}\n")
        f.write(f"c(phi)/v_ref - 1                            = {phi_c - 1.0:.16e}\n")
        f.write(f"numeric c2(a0_star)-1                       = {star_numeric_c2 - 1.0:.16e}\n\n")
        mins = energy_minima()
        f.write("Simple diagnostic minima, not physical proof:\n")
        f.write(f"grad energy min a0                          = {mins['grad_energy_min_a0']:.16e}\n")
        f.write(f"curvature energy min a0                     = {mins['curvature_energy_min_a0']:.16e}\n")
        f.write(f"shape energy min a0                         = {mins['shape_energy_min_a0']:.16e}\n")
        f.write(f"elapsed                                      = {elapsed:.2f} s\n\n")
        f.write("Interpretation:\n")
        f.write("v6 confirms that the smooth-matched family has an exact c_chi/v_ref=1 root.\n")
        f.write("The root is close to, but not equal to, the golden ratio. This is a closure\n")
        f.write("selector inside one admissible profile family, not yet a derivation from an\n")
        f.write("Euler/NLSE variational core equation.\n")

    print(f"[*] Summary saved: {summary_path}")
    print("=" * 88)
    print("Summary")
    print("=" * 88)
    print(f"a0_star analytic     = {a0_star:.16f}")
    print(f"a0_star bisection    = {a0_bisect:.16f}")
    print(f"phi                  = {PHI:.16f}")
    print(f"a0_star - phi        = {phi_delta:.16e}")
    print(f"c(phi)/v_ref         = {phi_c:.16f}")
    print(f"numeric c2(root)-1   = {star_numeric_c2 - 1.0:.3e}")
    print(f"elapsed              = {elapsed:.2f} s")
    print("[*] PASS: v6 root selector completed.")


if __name__ == "__main__":
    main()

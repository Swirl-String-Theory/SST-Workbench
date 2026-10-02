#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase χ v2: robust internal torsional phase verification package.

Research Track target:
    I_chi = rho_f ∫_A r_perp² dA
    K_chi = rho_f v_swirl² ∫_A r_perp² dA
    c_chi² = K_chi / I_chi -> v_swirl²

v2 extends v1 from a circular tube to several cross-section geometries:
    - circles over a_core / r_c sweep
    - annuli with different inner radii
    - ellipses / anisotropic cross-sections
    - periodic phase-ring spectrum convergence

The package is intentionally a sanity verifier for the local chi-sector only.
It does not prove Q_chi -> Q_em and does not derive SU(2)/SU(3).
"""

from __future__ import annotations

import argparse
import csv
import os
import time
from typing import Any, Dict, Iterable, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sst_chi_phase_v2_build import MODULE_NAME, ensure_module

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)


def load_kernel(force_python: bool = False):
    if force_python:
        print("[*] Using pure-Python fallback by request.")
        import sst_chi_phase_v2_py as kernel
        return kernel, "python"
    try:
        ensure_module(SCRIPT_DIR)
        import sst_chi_phase_v2 as kernel
        return kernel, "cpp"
    except Exception as exc:  # build/import failure; fallback keeps package self-contained
        print(f"[!] C++ extension unavailable ({exc}). Using pure-Python fallback.")
        import sst_chi_phase_v2_py as kernel
        return kernel, "python"


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

# Main numerical controls. Keep these moderate so the pure-Python fallback remains usable.
N_R = 900
N_THETA = 360
N_GRID_REFERENCE = 4096
N_MAX = 32


def ensure_export_dir() -> str:
    export_dir = os.path.join(SCRIPT_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def as_float_dict(d: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for k, v in d.items():
        if isinstance(v, str):
            continue
        out[k] = float(v)
    return out


def write_csv(path: str, fieldnames: Iterable[str], rows: List[Dict[str, Any]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            clean = {}
            for name in fieldnames:
                value = row.get(name, "")
                if isinstance(value, float):
                    clean[name] = f"{value:.16e}"
                else:
                    clean[name] = value
            writer.writerow(clean)


def run_shape_sweep(kernel, export_dir: str) -> Tuple[float, float, str]:
    """Cross-section robustness test for circle / annulus / ellipse."""
    print("[*] v2 shape sweep: circle / annulus / ellipse")

    rows: List[Dict[str, Any]] = []

    # Circle radius sweep, including the original v1 sweep logic.
    for factor in [0.05, 0.10, 0.25, 0.50, 1.00, 2.00, 4.00, 10.00]:
        a = factor * R_C
        result = kernel.compute_chi_from_shape("circle", RHO_F, V_SWIRL, a, 0.0, N_R, N_THETA)
        row = dict(result)
        row.update({
            "case": f"circle_a_over_rc_{factor:g}",
            "shape": "circle",
            "a_over_rc": factor,
            "b_over_rc": 0.0,
            "inner_over_outer": 0.0,
        })
        rows.append(row)

    # Annuli at fixed outer radius r_c, varying hole size.
    outer = 1.0 * R_C
    for inner_ratio in [0.10, 0.25, 0.50, 0.75, 0.90]:
        inner = inner_ratio * outer
        result = kernel.compute_chi_from_shape("annulus", RHO_F, V_SWIRL, inner, outer, N_R, N_THETA)
        row = dict(result)
        row.update({
            "case": f"annulus_inner_over_outer_{inner_ratio:g}",
            "shape": "annulus",
            "a_over_rc": inner / R_C,
            "b_over_rc": outer / R_C,
            "inner_over_outer": inner_ratio,
        })
        rows.append(row)

    # Ellipse with fixed major semiaxis r_c and aspect sweep.
    a = 1.0 * R_C
    for aspect in [0.25, 0.3333333333, 0.50, 0.75, 1.00, 1.50, 2.00, 4.00]:
        b = aspect * a
        result = kernel.compute_chi_from_shape("ellipse", RHO_F, V_SWIRL, a, b, N_R, N_THETA)
        row = dict(result)
        row.update({
            "case": f"ellipse_b_over_a_{aspect:g}",
            "shape": "ellipse",
            "a_over_rc": a / R_C,
            "b_over_rc": b / R_C,
            "inner_over_outer": 0.0,
        })
        rows.append(row)

    fieldnames = [
        "case", "shape", "a_over_rc", "b_over_rc", "inner_over_outer",
        "J_analytic", "J_numeric", "J_rel_error",
        "I_chi_analytic", "K_chi_analytic", "c_chi_analytic", "c_chi_over_v_analytic",
        "I_chi_numeric", "K_chi_numeric", "c_chi_numeric", "c_chi_over_v_numeric",
    ]
    csv_path = os.path.join(export_dir, "chi_v2_shape_sweep.csv")
    write_csv(csv_path, fieldnames, rows)
    print(f"[*] CSV saved: {csv_path}")

    c_errors = np.array([abs(float(r["c_chi_over_v_numeric"]) - 1.0) for r in rows])
    j_errors = np.array([abs(float(r["J_rel_error"])) for r in rows])

    print(f"    max |c_chi/v_swirl - 1| = {np.max(c_errors):.3e}")
    print(f"    max |J_num/J_ana - 1|   = {np.max(j_errors):.3e}")

    labels = [r["case"].replace("_", "\n") for r in rows]
    x = np.arange(len(rows))

    plt.figure(figsize=(13, 5))
    plt.plot(x, [float(r["c_chi_over_v_numeric"]) for r in rows], "o-", label="canonical shared-moment c_chi/v")
    plt.axhline(1.0, color="k", linestyle="--", label="target")
    plt.xticks(x, labels, rotation=75, ha="right", fontsize=7)
    plt.ylabel(r"$c_\chi/v_{\rm swirl}$")
    plt.title("v2 shape robustness: canonical shared-moment phase speed")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_v2_shape_speed_ratio.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    plt.figure(figsize=(13, 5))
    plt.semilogy(x, j_errors, "s-", label=r"$|J_{num}/J_{ana}-1|$")
    plt.xticks(x, labels, rotation=75, ha="right", fontsize=7)
    plt.ylabel("absolute relative error")
    plt.title("v2 quadrature error for cross-section moment integral")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_v2_shape_moment_error.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    return float(np.max(c_errors)), float(np.max(j_errors)), csv_path


def run_anisotropic_ellipse_test(kernel, export_dir: str) -> Tuple[float, str]:
    """Tests whether anisotropic second-moment tensors split c_chi.

    Canonical SST shared-tensor ansatz: K_axis = rho v^2 M_axis, so both speeds
    remain v_swirl even for an elliptical cross-section. The counterfactual column
    deliberately violates the shared-moment assumption to show the falsifier.
    """
    print("[*] v2 anisotropic ellipse tensor test")
    rows: List[Dict[str, Any]] = []
    a = 1.0 * R_C
    for aspect in [0.25, 0.3333333333, 0.50, 0.75, 1.00, 1.50, 2.00, 3.00, 4.00]:
        b = aspect * a
        row = dict(kernel.anisotropic_ellipse_speed_check(RHO_F, V_SWIRL, a, b))
        row["case"] = f"ellipse_tensor_b_over_a_{aspect:g}"
        rows.append(row)
        print(
            f"    b/a={aspect:6.3f} | canonical=({row['canonical_cx_over_v']:.12f}, "
            f"{row['canonical_cy_over_v']:.12f}) | counterfactual split={row['counterfactual_split_abs']:.3e}"
        )

    fieldnames = [
        "case", "aspect_b_over_a", "M_xx", "M_yy",
        "canonical_cx_over_v", "canonical_cy_over_v",
        "counterfactual_cx_over_v", "counterfactual_cy_over_v", "counterfactual_split_abs",
    ]
    csv_path = os.path.join(export_dir, "chi_v2_anisotropic_ellipse_tensor.csv")
    write_csv(csv_path, fieldnames, rows)
    print(f"[*] CSV saved: {csv_path}")

    aspects = np.array([float(r["aspect_b_over_a"]) for r in rows])
    cx = np.array([float(r["canonical_cx_over_v"]) for r in rows])
    cy = np.array([float(r["canonical_cy_over_v"]) for r in rows])
    cfx = np.array([float(r["counterfactual_cx_over_v"]) for r in rows])
    cfy = np.array([float(r["counterfactual_cy_over_v"]) for r in rows])

    plt.figure(figsize=(10, 5))
    plt.semilogx(aspects, cx, "o-", label="canonical x-axis")
    plt.semilogx(aspects, cy, "s-", label="canonical y-axis")
    plt.semilogx(aspects, cfx, "o--", label="counterfactual x-axis")
    plt.semilogx(aspects, cfy, "s--", label="counterfactual y-axis")
    plt.axhline(1.0, color="k", linewidth=0.8)
    plt.xlabel("ellipse aspect ratio b/a")
    plt.ylabel(r"axis speed / $v_{\rm swirl}$")
    plt.title("v2 anisotropic ellipse: shared-moment ansatz versus counterfactual split")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_v2_anisotropic_ellipse_speed.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    canonical_split = float(np.max(np.maximum(np.abs(cx - 1.0), np.abs(cy - 1.0))))
    return canonical_split, csv_path


def run_horn_loop_spectrum(kernel, export_dir: str) -> Tuple[float, float, str]:
    print("[*] v2 horn-loop spectrum at reference grid")
    l_chi = 2.0 * np.pi * R_C
    omega_cont = np.array(kernel.continuous_phase_spectrum(V_SWIRL, float(l_chi), N_MAX, 0.0), dtype=float)
    omega_disc = np.array(kernel.discrete_phase_spectrum(V_SWIRL, float(l_chi), N_GRID_REFERENCE, N_MAX, 0.0), dtype=float)
    n = np.arange(1, N_MAX + 1, dtype=float)
    target = n * OMEGA_C
    ratio_cont = omega_cont / target
    ratio_disc = omega_disc / target

    rows = []
    for i in range(N_MAX):
        rows.append({
            "n": int(n[i]),
            "omega_continuous_rad_s": float(omega_cont[i]),
            "omega_discrete_rad_s": float(omega_disc[i]),
            "target_n_omega_c_rad_s": float(target[i]),
            "continuous_ratio": float(ratio_cont[i]),
            "discrete_ratio": float(ratio_disc[i]),
            "discrete_rel_error": float(ratio_disc[i] - 1.0),
        })
    csv_path = os.path.join(export_dir, "chi_v2_horn_loop_spectrum.csv")
    write_csv(csv_path, rows[0].keys(), rows)
    print(f"[*] CSV saved: {csv_path}")

    plt.figure(figsize=(10, 5))
    plt.plot(n, ratio_cont, "k--", label="continuous exact")
    plt.plot(n, ratio_disc, "ro-", label=f"finite difference, N={N_GRID_REFERENCE}")
    plt.axhline(1.0, color="k", linewidth=0.8)
    plt.xlabel("mode number n")
    plt.ylabel(r"$\omega_n/(n\omega_c)$")
    plt.title(r"v2 horn-loop spectrum: $L_\chi=2\pi r_c$")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_v2_horn_loop_spectrum.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    max_error = float(np.max(np.abs(ratio_disc - 1.0)))
    omega1_ratio = float(ratio_disc[0])
    return max_error, omega1_ratio, csv_path


def run_spectrum_convergence(kernel, export_dir: str) -> Tuple[float, str]:
    print("[*] v2 periodic phase-ring spectral convergence")
    l_chi = 2.0 * np.pi * R_C
    grids = [128, 256, 512, 1024, 2048, 4096, 8192]
    rows = []
    for n_grid in grids:
        summary = dict(kernel.spectrum_error_summary(V_SWIRL, float(l_chi), n_grid, N_MAX, 0.0))
        # Leading-order central-difference error at highest mode n=N_MAX:
        x = np.pi * N_MAX / n_grid
        predicted = abs(np.sin(x) / x - 1.0)
        summary["predicted_high_mode_error"] = predicted
        rows.append(summary)
        print(
            f"    N={n_grid:5d} | max rel error={summary['max_abs_rel_error']:.3e} | "
            f"prediction={predicted:.3e}"
        )

    fieldnames = ["n_grid", "n_max", "omega1_ratio_disc_over_cont", "max_abs_rel_error", "predicted_high_mode_error"]
    csv_path = os.path.join(export_dir, "chi_v2_spectrum_convergence.csv")
    write_csv(csv_path, fieldnames, rows)
    print(f"[*] CSV saved: {csv_path}")

    n_grid_arr = np.array([float(r["n_grid"]) for r in rows])
    err_arr = np.array([float(r["max_abs_rel_error"]) for r in rows])
    pred_arr = np.array([float(r["predicted_high_mode_error"]) for r in rows])

    plt.figure(figsize=(9, 5))
    plt.loglog(n_grid_arr, err_arr, "o-", label="observed max error")
    plt.loglog(n_grid_arr, pred_arr, "k--", label="central-difference prediction")
    plt.xlabel("periodic grid size N")
    plt.ylabel("max relative spectrum error")
    plt.title("v2 spectrum convergence: finite-difference dispersion is numerical")
    plt.grid(True, which="both")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(export_dir, "chi_v2_spectrum_convergence.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    return float(err_arr[-1]), csv_path


def write_summary(export_dir: str, lines: List[str]) -> str:
    path = os.path.join(export_dir, "chi_v2_run_results_summary.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[*] Summary saved: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="SST chi-phase v2 verification package")
    parser.add_argument("--python", action="store_true", help="force pure-Python fallback")
    parser.add_argument("--show", action="store_true", help="show plots interactively after saving")
    args = parser.parse_args()

    kernel, backend = load_kernel(force_python=args.python)
    print("=" * 84)
    print("SST internal torsional chi-phase verification package v2")
    print("=" * 84)
    print(f"[*] backend = {backend} ({MODULE_NAME if backend == 'cpp' else 'sst_chi_phase_v2_py'})")
    print(f"[*] rho_f   = {RHO_F:.8e} kg m^-3")
    print(f"[*] v_swirl = {V_SWIRL:.8e} m s^-1")
    print(f"[*] omega_c = {OMEGA_C:.8e} s^-1")
    print(f"[*] r_c     = {R_C:.8e} m")
    print("[*] Status: Research Track verifier, not Q_chi->Q_em or SU(2)/SU(3) proof.")

    export_dir = ensure_export_dir()
    t0 = time.time()

    max_shape_speed_error, max_shape_moment_error, shape_csv = run_shape_sweep(kernel, export_dir)
    max_aniso_canonical_split, aniso_csv = run_anisotropic_ellipse_test(kernel, export_dir)
    max_horn_error, omega1_ratio, horn_csv = run_horn_loop_spectrum(kernel, export_dir)
    finest_grid_spectrum_error, conv_csv = run_spectrum_convergence(kernel, export_dir)

    elapsed = time.time() - t0

    lines = [
        "SST chi-phase v2 verification summary",
        "====================================",
        f"backend                                      = {backend}",
        f"rho_f                                        = {RHO_F:.16e} kg m^-3",
        f"v_swirl                                      = {V_SWIRL:.16e} m s^-1",
        f"omega_c                                      = {OMEGA_C:.16e} s^-1",
        f"r_c                                          = {R_C:.16e} m",
        "",
        f"max shape |c_chi/v_swirl - 1|                = {max_shape_speed_error:.16e}",
        f"max shape |J_num/J_ana - 1|                  = {max_shape_moment_error:.16e}",
        f"max anisotropic canonical axis split         = {max_aniso_canonical_split:.16e}",
        f"omega_1/(omega_c), N={N_GRID_REFERENCE}       = {omega1_ratio:.16e}",
        f"max horn |omega_n/(n omega_c)-1|              = {max_horn_error:.16e}",
        f"finest-grid spectrum convergence error        = {finest_grid_spectrum_error:.16e}",
        f"elapsed                                      = {elapsed:.2f} s",
        "",
        "Exports:",
        f"shape_csv                                    = {shape_csv}",
        f"anisotropic_csv                              = {aniso_csv}",
        f"horn_csv                                     = {horn_csv}",
        f"convergence_csv                              = {conv_csv}",
        "",
        "Interpretation:",
        "PASS means the local internal chi-phase speed c_chi=v_swirl is stable under",
        "circle/annulus/ellipse cross-section changes, provided the same transverse",
        "moment or tensor controls both I_chi and K_chi. This supports the local",
        "U(1)_chi mechanics only; Q_chi->Q_em remains a separate R-phase coupling test.",
    ]
    summary_path = write_summary(export_dir, lines)

    print("=" * 84)
    print("Summary")
    print("=" * 84)
    for line in lines[9:16]:
        print(line)
    print(f"summary                                      = {summary_path}")

    # Pass/fail assertions. These are intentionally strict on the algebraic speed
    # cancellation and practical on quadrature/spectrum discretization.
    if max_shape_speed_error > 1e-12:
        raise AssertionError("Canonical c_chi/v_swirl should cancel to machine precision for all shapes.")
    if max_shape_moment_error > 2e-5:
        raise AssertionError("Cross-section quadrature error exceeds tolerance.")
    if max_aniso_canonical_split > 1e-12:
        raise AssertionError("Anisotropic shared-tensor speed should not split.")
    if abs(omega1_ratio - 1.0) > 1e-6:
        raise AssertionError("Discrete omega_1 does not reproduce omega_c within tolerance.")
    if max_horn_error > 2e-4:
        raise AssertionError("Reference-grid phase-ring spectrum error exceeds tolerance.")
    if finest_grid_spectrum_error > 6e-5:
        raise AssertionError("Finest-grid spectrum convergence error exceeds tolerance.")

    print("[*] PASS: v2 chi-phase robustness tests completed successfully.")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()

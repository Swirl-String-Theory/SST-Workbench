#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SST ideal-trefoil Biot-Savart closure package v2.

Flat, v6-style runner: loads embedded ideal.txt, optionally builds a local pybind11
C++ backend, scans the SST core radius a/r_c, and writes exports/ diagnostics.
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from sst_trefoil_biot_py import (
    DEFAULT_CONSTANTS,
    scan_closure,
    save_xyz,
    write_csv,
    write_json,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EXPORT_DIR = SCRIPT_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def try_cpp_backend(force_python: bool = False):
    if force_python:
        return None, "python-forced"
    try:
        from sst_trefoil_biot_build import import_module
        return import_module(auto_build=True, script_dir=str(SCRIPT_DIR)), "cpp"
    except Exception as exc:
        print(f"[!] C++ backend unavailable ({exc}). Using pure Python backend.")
        return None, "python-fallback"


def plot_energy_scan(rows, a_star: float):
    xs = np.array([r["a_over_rc"] for r in rows], dtype=float)
    ys = np.array([r["E_total_J"] for r in rows], dtype=float)
    ebs = np.array([r["E_bs_J"] for r in rows], dtype=float)
    ecore = np.array([r["E_core_J"] for r in rows], dtype=float)

    plt.figure(figsize=(10, 6))
    plt.loglog(xs, ys, marker="o", linewidth=1, label=r"$E_{\rm total}$")
    plt.loglog(xs, ebs, linewidth=1, label=r"$E_{\rm BS}$")
    plt.loglog(xs, ecore, linewidth=1, label=r"$E_{\rm core}$")
    plt.axvline(a_star, color="k", linestyle="--", label=rf"$a_\star/r_c={a_star:.6g}$")
    plt.xlabel(r"$a/r_c$")
    plt.ylabel("Energy [J]")
    plt.title("SST ideal trefoil Biot-Savart closure scan")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend()
    plt.tight_layout()
    path = EXPORT_DIR / "trefoil_biot_energy_scan.png"
    plt.savefig(path, dpi=180)
    print(f"[*] Plot saved: {path}")


def plot_points(points):
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="3d")
    p = np.vstack([points, points[0]])
    ax.plot(p[:, 0], p[:, 1], p[:, 2], linewidth=1.1)
    ax.set_title("Embedded ideal trefoil sample from ideal.txt")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    try:
        ax.set_box_aspect((np.ptp(p[:, 0]), np.ptp(p[:, 1]), np.ptp(p[:, 2])))
    except Exception:
        pass
    plt.tight_layout()
    path = EXPORT_DIR / "trefoil_geometry.png"
    plt.savefig(path, dpi=180)
    print(f"[*] Plot saved: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", action="store_true", help="force pure-Python backend")
    parser.add_argument("--knot-id", default="3:1:1", help="ideal.txt Id, default trefoil 3:1:1")
    parser.add_argument("--n", type=int, default=384, help="Fourier sample count")
    parser.add_argument("--samples", type=int, default=60, help="a/r_c scan count")
    parser.add_argument("--a-min", type=float, default=0.20)
    parser.add_argument("--a-max", type=float, default=3.00)
    parser.add_argument("--mode", choices=["regularized", "cutoff"], default="regularized")
    parser.add_argument("--pressure-penalty-lambda", type=float, default=10.0)
    args = parser.parse_args()

    t0 = time.time()
    cpp_mod, backend = try_cpp_backend(args.python)

    print("=" * 88)
    print("SST ideal-trefoil Biot-Savart closure package v2")
    print("=" * 88)
    print(f"[*] backend = {backend}")
    print(f"[*] ideal  = {SCRIPT_DIR / 'ideal.txt'}")
    print(f"[*] knot   = {args.knot_id}")
    print(f"[*] n      = {args.n}")
    print(f"[*] rho_f  = {DEFAULT_CONSTANTS.rho_f:.8e} kg m^-3")
    print(f"[*] v_swirl= {DEFAULT_CONSTANTS.v_swirl:.8e} m s^-1")
    print(f"[*] r_c    = {DEFAULT_CONSTANTS.r_c:.8e} m")
    print(f"[*] Gamma0 = {DEFAULT_CONSTANTS.gamma_0:.8e} m^2 s^-1")

    summary, rows, points = scan_closure(
        ideal_path=SCRIPT_DIR / "ideal.txt",
        knot_id=args.knot_id,
        n=args.n,
        a_min=args.a_min,
        a_max=args.a_max,
        samples=args.samples,
        mode=args.mode,
        pressure_penalty_lambda=args.pressure_penalty_lambda,
        cpp_mod=cpp_mod,
    )
    summary["backend"] = backend
    summary["elapsed_s"] = time.time() - t0

    write_csv(EXPORT_DIR / "trefoil_biot_energy_scan.csv", rows)
    write_json(EXPORT_DIR / "trefoil_biot_summary.json", summary)
    save_xyz(EXPORT_DIR / f"{args.knot_id.replace(':', '_')}_points.xyz", points)
    plot_energy_scan(rows, summary["best"]["a_over_rc"])
    plot_points(points)

    text_path = EXPORT_DIR / "trefoil_biot_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST ideal-trefoil Biot-Savart closure package v2\n")
        f.write("====================================================\n")
        f.write(f"backend                                      = {backend}\n")
        f.write(f"knot_id                                      = {summary['knot_id']}\n")
        f.write(f"declared ropelength L                        = {summary['declared_L']}\n")
        f.write(f"declared thickness diameter proxy D          = {summary['declared_D']}\n")
        f.write(f"sample_N                                     = {summary['sample_N']}\n")
        f.write(f"polyline_L_dim                               = {summary['polyline_L_dim']:.16e}\n")
        f.write(f"fourier_closure_error_dim                    = {summary['fourier_closure_error_dim']:.16e}\n")
        f.write(f"rho_f                                        = {DEFAULT_CONSTANTS.rho_f:.16e} kg m^-3\n")
        f.write(f"v_swirl                                      = {DEFAULT_CONSTANTS.v_swirl:.16e} m s^-1\n")
        f.write(f"r_c                                          = {DEFAULT_CONSTANTS.r_c:.16e} m\n")
        f.write(f"Gamma0                                       = {DEFAULT_CONSTANTS.gamma_0:.16e} m^2 s^-1\n")
        f.write(f"natural_length                               = {DEFAULT_CONSTANTS.natural_length:.16e} m\n\n")
        b = summary["best"]
        f.write("Best closure point:\n")
        f.write(f"a_star/r_c                                   = {b['a_over_rc']:.16e}\n")
        f.write(f"a_star                                       = {b['a_phys_m']:.16e} m\n")
        f.write(f"chi_eff                                      = {summary['chi_eff']:.16e}\n")
        f.write(f"1/(2*pi)                                     = {summary['chi_req_1_over_2pi']:.16e}\n")
        f.write(f"E_total                                      = {b['E_total_J']:.16e} J\n")
        f.write(f"E_BS                                         = {b['E_bs_J']:.16e} J\n")
        f.write(f"E_core                                       = {b['E_core_J']:.16e} J\n")
        f.write(f"elapsed                                      = {summary['elapsed_s']:.2f} s\n\n")
        f.write("Interpretation:\n")
        f.write("This is a research-track numerical closure scan. It uses the embedded ideal.txt\n")
        f.write("trefoil Fourier representative and a pybind11 Biot-Savart kernel, but it is not\n")
        f.write("a proof that the physical Euler/NLSE variational selector chooses this radius.\n")
    print(f"[*] Summary saved: {text_path}")

    print("=" * 88)
    print("Summary")
    print("=" * 88)
    print(f"a_star/r_c         = {summary['best']['a_over_rc']:.16f}")
    print(f"a_star             = {summary['best']['a_phys_m']:.8e} m")
    print(f"chi_eff            = {summary['chi_eff']:.16f}")
    print(f"1/(2*pi)           = {summary['chi_req_1_over_2pi']:.16f}")
    print(f"E_total            = {summary['best']['E_total_J']:.8e} J")
    print(f"elapsed            = {summary['elapsed_s']:.2f} s")
    print("[*] PASS: trefoil Biot-Savart closure scan completed.")


if __name__ == "__main__":
    main()

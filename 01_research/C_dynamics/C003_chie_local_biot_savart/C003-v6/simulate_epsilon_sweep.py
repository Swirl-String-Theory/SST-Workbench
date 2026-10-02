#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSTcore chi_E run 1: epsilon/softening sweep.

Purpose
-------
Probe whether the regularized circular-filament kinetic factor at the horn limit
(lambda=1) is robust against the softening choice epsilon=a_soft/a0.

This is a diagnostic only.  A match to 2*pi obtained by tuning epsilon is a
calibration, not a derivation.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from sst_horn_torus_chiE import (
    EnergyMassMode,
    HornTorusParams,
    evaluate_horn_torus,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", action="store_true", help="force pure-Python backend")
    parser.add_argument("--lambda", dest="lambda_", type=float, default=1.0, help="R/a0; default horn threshold")
    parser.add_argument("--eps-min", type=float, default=0.20)
    parser.add_argument("--eps-max", type=float, default=2.00)
    parser.add_argument("--eps-count", type=int, default=37)
    parser.add_argument("--n", type=int, default=32768, help="quadrature panels")
    parser.add_argument("--mass-mode", default=EnergyMassMode.KINETIC_PLUS_CAVITY.value,
                        choices=[m.value for m in EnergyMassMode])
    args = parser.parse_args()

    t0 = time.time()
    cpp_mod, backend = try_cpp_backend(args.python)
    eps_values = np.linspace(args.eps_min, args.eps_max, args.eps_count)

    rows = []
    for eps in eps_values:
        p = HornTorusParams(lambda_=args.lambda_, epsilon=float(eps), quadrature_n=args.n, mass_mode=args.mass_mode)
        r = evaluate_horn_torus(p, kernel="regularized", cpp_mod=cpp_mod)
        rows.append(asdict(r))

    # Useful selectors for quick review.
    best_kinetic = min(rows, key=lambda x: abs(x["chi_K"] - x["target_chi_E"]))
    best_hollow = min(rows, key=lambda x: abs(x["chi_E_hollow_total"] - x["target_chi_E"]))
    best_selected = min(rows, key=lambda x: abs(x["chi_E"] - x["target_chi_E"]))

    summary = {
        "run": "epsilon_sweep",
        "backend": backend,
        "lambda_": args.lambda_,
        "eps_min": args.eps_min,
        "eps_max": args.eps_max,
        "eps_count": args.eps_count,
        "quadrature_n": args.n,
        "mass_mode": args.mass_mode,
        "best_kinetic_to_2pi": best_kinetic,
        "best_hollow_to_2pi": best_hollow,
        "best_selected_to_2pi": best_selected,
        "elapsed_s": time.time() - t0,
        "status": "RESEARCH-TRACK / EPSILON ROBUSTNESS / NOT CANONIZED",
        "interpretation": (
            "This sweep tests whether chi_K or chi_E_hollow approaches 2*pi without tuning epsilon. "
            "If matching requires a special epsilon, the match is calibrated, not derived."
        ),
    }

    csv_path = EXPORT_DIR / "epsilon_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_json(EXPORT_DIR / "epsilon_sweep_summary.json", summary)

    eps = np.array([r["epsilon"] for r in rows])
    target = rows[0]["target_chi_E"]
    plt.figure(figsize=(10, 6))
    plt.plot(eps, [r["chi_K"] for r in rows], marker="o", linewidth=1, label=r"$\chi_K$ kinetic")
    plt.plot(eps, [r["chi_E_hollow_total"] for r in rows], marker="s", linewidth=1, label=r"$\chi_E^{\rm hollow}$")
    if args.mass_mode != EnergyMassMode.KINETIC_PLUS_CAVITY.value:
        plt.plot(eps, [r["chi_E"] for r in rows], marker="^", linewidth=1, label=rf"selected {args.mass_mode}")
    plt.axhline(target, linestyle="--", label=r"target $2\pi$")
    plt.xlabel(r"$\epsilon=a_{\rm soft}/a_0$")
    plt.ylabel("dimensionless energy factor")
    plt.title(rf"SST horn-torus epsilon sweep at $\lambda={args.lambda_}$")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plot_path = EXPORT_DIR / "epsilon_sweep.png"
    plt.savefig(plot_path, dpi=180)
    print(f"[*] Plot saved: {plot_path}")

    text_path = EXPORT_DIR / "epsilon_sweep_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST horn-torus epsilon sweep\n")
        f.write("==============================\n")
        f.write(f"backend              = {backend}\n")
        f.write(f"lambda               = {args.lambda_}\n")
        f.write(f"eps range            = [{args.eps_min}, {args.eps_max}]\n")
        f.write(f"eps count            = {args.eps_count}\n")
        f.write(f"quadrature_n         = {args.n}\n")
        f.write(f"mass_mode            = {args.mass_mode}\n")
        f.write(f"best kinetic epsilon = {best_kinetic['epsilon']:.16e}\n")
        f.write(f"best kinetic chi_K   = {best_kinetic['chi_K']:.16e}\n")
        f.write(f"best hollow epsilon  = {best_hollow['epsilon']:.16e}\n")
        f.write(f"best hollow chi_E    = {best_hollow['chi_E_hollow_total']:.16e}\n")
        f.write(f"target 2*pi          = {target:.16e}\n")
        f.write("\nInterpretation:\n")
        f.write(summary["interpretation"] + "\n")
    print(f"[*] Summary saved: {text_path}")
    print("[*] PASS: epsilon sweep completed")


if __name__ == "__main__":
    main()

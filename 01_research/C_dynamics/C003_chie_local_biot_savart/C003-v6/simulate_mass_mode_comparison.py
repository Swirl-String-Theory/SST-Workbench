#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSTcore chi_E run 2: mass-energy interpretation comparison.

Compares kinetic-only, strict hollow-core total, vacuum-subtracted, and calibrated
target-renormalized mass modes over lambda.  The target-renormalized mode is
included only to report the subtraction needed to force chi_E=2*pi.
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
    parser.add_argument("--lambda-min", type=float, default=1.0)
    parser.add_argument("--lambda-max", type=float, default=8.0)
    parser.add_argument("--lambda-count", type=int, default=33)
    parser.add_argument("--epsilon", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=32768, help="quadrature panels")
    args = parser.parse_args()

    t0 = time.time()
    cpp_mod, backend = try_cpp_backend(args.python)
    lambdas = np.linspace(args.lambda_min, args.lambda_max, args.lambda_count)
    modes = [
        EnergyMassMode.KINETIC_ONLY,
        EnergyMassMode.KINETIC_PLUS_CAVITY,
        EnergyMassMode.VACUUM_SUBTRACTED,
        EnergyMassMode.TARGET_RENORMALIZED,
    ]

    rows = []
    for lam in lambdas:
        for mode in modes:
            p = HornTorusParams(lambda_=float(lam), epsilon=args.epsilon, quadrature_n=args.n, mass_mode=mode.value)
            r = evaluate_horn_torus(p, kernel="regularized", cpp_mod=cpp_mod)
            d = asdict(r)
            d["mode_label"] = mode.value
            rows.append(d)

    horn_rows = [r for r in rows if abs(r["lambda_"] - args.lambda_min) < 1e-14]
    summary = {
        "run": "mass_mode_comparison",
        "backend": backend,
        "lambda_min": args.lambda_min,
        "lambda_max": args.lambda_max,
        "lambda_count": args.lambda_count,
        "epsilon": args.epsilon,
        "quadrature_n": args.n,
        "horn_rows": horn_rows,
        "elapsed_s": time.time() - t0,
        "status": "RESEARCH-TRACK / MASS-MODE COMPARISON / NOT CANONIZED",
        "interpretation": (
            "kinetic_plus_cavity is the strict hollow-core total. vacuum_subtracted equals kinetic-only but records "
            "-P_vac V_cav as a subtraction. target_renormalized reports the calibrated subtraction needed to force 2*pi."
        ),
    }

    csv_path = EXPORT_DIR / "mass_mode_comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_json(EXPORT_DIR / "mass_mode_comparison_summary.json", summary)

    plt.figure(figsize=(10, 6))
    target = rows[0]["target_chi_E"]
    for mode in modes:
        subset = [r for r in rows if r["mode_label"] == mode.value]
        plt.plot([r["lambda_"] for r in subset], [r["chi_E"] for r in subset], marker="o", linewidth=1, label=mode.value)
    plt.axhline(target, linestyle="--", label=r"target $2\pi$")
    plt.xlabel(r"$\lambda=R/a_0$")
    plt.ylabel(r"selected $\chi_E$")
    plt.title("SST horn-torus mass-mode comparison")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plot_path = EXPORT_DIR / "mass_mode_comparison.png"
    plt.savefig(plot_path, dpi=180)
    print(f"[*] Plot saved: {plot_path}")

    text_path = EXPORT_DIR / "mass_mode_comparison_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST horn-torus mass-mode comparison\n")
        f.write("====================================\n")
        f.write(f"backend        = {backend}\n")
        f.write(f"lambda range   = [{args.lambda_min}, {args.lambda_max}]\n")
        f.write(f"lambda count   = {args.lambda_count}\n")
        f.write(f"epsilon        = {args.epsilon}\n")
        f.write(f"quadrature_n   = {args.n}\n")
        f.write(f"target 2*pi    = {target:.16e}\n\n")
        f.write("Horn-row selected chi_E by mode:\n")
        for row in horn_rows:
            f.write(f"{row['mode_label']:24s} chi_E={row['chi_E']:.16e} residual={row['target_residual']:.16e} chi_ren={row['chi_renormalization']:.16e}\n")
        f.write("\nInterpretation:\n")
        f.write(summary["interpretation"] + "\n")
    print(f"[*] Summary saved: {text_path}")
    print("[*] PASS: mass-mode comparison completed")


if __name__ == "__main__":
    main()

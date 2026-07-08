#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from sst_horn_torus_chiE import (
    HornTorusParams,
    evaluate_horn_torus,
    scan_lambda,
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


def plot_scan(rows, path: Path):
    lam = np.array([r.lambda_ for r in rows], dtype=float)
    chi_k = np.array([r.chi_K for r in rows], dtype=float)
    chi_c = np.array([r.chi_cavitation for r in rows], dtype=float)
    chi_e = np.array([r.chi_E_hollow for r in rows], dtype=float)
    target = rows[0].target_chi_E if rows else 2.0 * np.pi

    plt.figure(figsize=(10, 6))
    plt.plot(lam, chi_k, marker="o", linewidth=1, label=r"$\chi_K$ kinetic")
    plt.plot(lam, chi_c, linewidth=1, label=r"$\chi_{\rm cav}$")
    plt.plot(lam, chi_e, marker="s", linewidth=1, label=r"$\chi_E^{\rm hollow}$")
    plt.axhline(target, color="k", linestyle="--", label=r"target $2\pi$")
    plt.xlabel(r"$\lambda = R/a_0$")
    plt.ylabel("dimensionless energy factor")
    plt.title("SST horn-torus closed-loop chi_E diagnostic")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    print(f"[*] Plot saved: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", action="store_true", help="force pure-Python backend")
    parser.add_argument("--kernel", choices=["regularized", "thin"], default="regularized")
    parser.add_argument("--lambda-min", type=float, default=1.0)
    parser.add_argument("--lambda-max", type=float, default=8.0)
    parser.add_argument("--lambda-count", type=int, default=33)
    parser.add_argument("--epsilon", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=32768, help="quadrature points")
    parser.add_argument("--core-constant", type=float, default=1.75)
    args = parser.parse_args()

    t0 = time.time()
    cpp_mod, backend = try_cpp_backend(args.python)
    base = HornTorusParams(
        lambda_=args.lambda_min,
        epsilon=args.epsilon,
        quadrature_n=args.n,
        core_constant=args.core_constant,
    )
    rows = scan_lambda(
        args.lambda_min,
        args.lambda_max,
        args.lambda_count,
        base,
        kernel=args.kernel,
        cpp_mod=cpp_mod,
    )
    horn = evaluate_horn_torus(base, kernel=args.kernel, cpp_mod=cpp_mod)

    summary = {
        "backend": backend,
        "kernel": args.kernel,
        "params": asdict(base),
        "horn_lambda_result": asdict(horn),
        "min_total_row": asdict(min(rows, key=lambda r: r.chi_E_hollow)),
        "min_kinetic_row": asdict(min(rows, key=lambda r: r.chi_K)),
        "elapsed_s": time.time() - t0,
        "status": "RESEARCH-TRACK / FALSIFICATION TEST / NOT CANONIZED",
        "interpretation": (
            "The hollow-core total includes positive cavitation work. If this work counts "
            "as inertial rest energy, the horn limit cannot match 2*pi whenever chi_cav > 2*pi."
        ),
    }

    write_csv(EXPORT_DIR / "horn_torus_chiE_scan.csv", rows)
    write_json(EXPORT_DIR / "horn_torus_chiE_summary.json", summary)
    plot_scan(rows, EXPORT_DIR / "horn_torus_chiE_scan.png")

    text_path = EXPORT_DIR / "horn_torus_chiE_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST horn-torus closed-loop chi_E diagnostic\n")
        f.write("============================================\n")
        f.write(f"backend                         = {backend}\n")
        f.write(f"kernel                          = {args.kernel}\n")
        f.write(f"lambda_min                      = {args.lambda_min}\n")
        f.write(f"lambda_max                      = {args.lambda_max}\n")
        f.write(f"lambda_count                    = {args.lambda_count}\n")
        f.write(f"epsilon                         = {args.epsilon}\n")
        f.write(f"quadrature_n                    = {args.n}\n\n")
        f.write("Horn-limit row:\n")
        f.write(f"chi_K                           = {horn.chi_K:.16e}\n")
        f.write(f"chi_cavitation                  = {horn.chi_cavitation:.16e}\n")
        f.write(f"chi_E_hollow                    = {horn.chi_E_hollow:.16e}\n")
        f.write(f"target 2*pi                     = {horn.target_chi_E:.16e}\n")
        f.write(f"residual kinetic to 2pi          = {horn.residual_kinetic_to_2pi:.16e}\n")
        f.write(f"residual total to 2pi            = {horn.residual_total_to_2pi:.16e}\n")
        f.write("\nInterpretation:\n")
        f.write(summary["interpretation"] + "\n")
    print(f"[*] Summary saved: {text_path}")

    print("=" * 88)
    print("SST horn-torus chi_E diagnostic")
    print("=" * 88)
    print(f"backend              = {backend}")
    print(f"kernel               = {args.kernel}")
    print(f"chi_K(lambda_min)    = {horn.chi_K:.8e}")
    print(f"chi_cav(lambda_min)  = {horn.chi_cavitation:.8e}")
    print(f"chi_E_hollow         = {horn.chi_E_hollow:.8e}")
    print(f"target 2*pi          = {horn.target_chi_E:.8e}")
    print(f"residual total       = {horn.residual_total_to_2pi:.8e}")
    print("[*] PASS: horn-torus chi_E diagnostic completed.")


if __name__ == "__main__":
    main()

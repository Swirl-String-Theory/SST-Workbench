#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from sst_horn_torus_chiE import (
    EnergyMassMode,
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
    chi_hollow = np.array([r.chi_E_hollow for r in rows], dtype=float)
    chi_mass = np.array([r.chi_E for r in rows], dtype=float)
    target = rows[0].target_chi_E if rows else 2.0 * np.pi

    plt.figure(figsize=(10, 6))
    plt.plot(lam, chi_k, marker="o", linewidth=1, label=r"$\chi_K$ kinetic")
    plt.plot(lam, chi_c, linewidth=1, label=r"$\chi_{\rm cav}$")
    plt.plot(lam, chi_hollow, marker="s", linewidth=1, label=r"$\chi_E^{\rm hollow}$")
    if rows and rows[0].mass_mode != "kinetic_plus_cavity":
        plt.plot(lam, chi_mass, marker="^", linewidth=1, label=rf"$\chi_E$ selected: {rows[0].mass_mode}")
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
    parser.add_argument(
        "--mass-mode",
        default=EnergyMassMode.KINETIC_PLUS_CAVITY.value,
        choices=[m.value for m in EnergyMassMode],
        help="mass-energy interpretation mode",
    )
    args = parser.parse_args()

    t0 = time.time()
    cpp_mod, backend = try_cpp_backend(args.python)
    base = HornTorusParams(
        lambda_=args.lambda_min,
        epsilon=args.epsilon,
        quadrature_n=args.n,
        core_constant=args.core_constant,
        mass_mode=args.mass_mode,
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
        "mass_mode": args.mass_mode,
        "horn_lambda_result": asdict(horn),
        "min_hollow_total_row": asdict(min(rows, key=lambda r: r.chi_E_hollow)),
        "min_selected_mass_row": asdict(min(rows, key=lambda r: r.chi_E)),
        "min_kinetic_row": asdict(min(rows, key=lambda r: r.chi_K)),
        "elapsed_s": time.time() - t0,
        "status": "RESEARCH-TRACK / FALSIFICATION TEST / NOT CANONIZED",
        "interpretation": (
            "The runner now separates the strict hollow total from the selected mass-energy mode. "
            "kinetic_plus_cavity is the strict hollow-core total; vacuum_subtracted records a -P_vac V_cav subtraction; "
            "target_renormalized reports the calibrated subtraction needed to force 2*pi."
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
        f.write(f"quadrature_n                    = {args.n}\n")
        f.write(f"mass_mode                       = {args.mass_mode}\n\n")
        f.write("Horn-limit row:\n")
        f.write(f"chi_K                           = {horn.chi_K:.16e}\n")
        f.write(f"chi_cavitation                  = {horn.chi_cavitation:.16e}\n")
        f.write(f"chi_E_hollow                    = {horn.chi_E_hollow:.16e}\n")
        f.write(f"chi_renormalization             = {horn.chi_renormalization:.16e}\n")
        f.write(f"chi_E_selected                  = {horn.chi_E:.16e}\n")
        f.write(f"target 2*pi                     = {horn.target_chi_E:.16e}\n")
        f.write(f"residual kinetic to 2pi          = {horn.residual_kinetic_to_2pi:.16e}\n")
        f.write(f"residual hollow total to 2pi     = {horn.residual_total_to_2pi:.16e}\n")
        f.write(f"residual selected mass to 2pi    = {horn.residual_mass_to_2pi:.16e}\n")
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
    print(f"chi_renormalization  = {horn.chi_renormalization:.8e}")
    print(f"mass_mode            = {horn.mass_mode}")
    print(f"chi_E selected       = {horn.chi_E:.8e}")
    print(f"target 2*pi          = {horn.target_chi_E:.8e}")
    print(f"residual selected    = {horn.residual_mass_to_2pi:.8e}")
    print("[*] PASS: horn-torus chi_E diagnostic completed.")


if __name__ == "__main__":
    main()

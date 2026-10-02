#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from sst_solid_core_chiE import (
    TARGET_CHI_E,
    SolidCoreParams,
    alpha_required_for_target,
    evaluate_solid_core,
    result_to_dict,
    scan_alpha,
    scan_lambda,
    write_csv,
    write_json,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EXPORT_DIR = SCRIPT_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def plot_lambda_scan(rows, path: Path) -> None:
    lam = np.array([r.lambda_ for r in rows], dtype=float)
    chi_total = np.array([r.chi_E for r in rows], dtype=float)
    chi_int = np.array([r.chi_internal_rankine for r in rows], dtype=float)
    chi_ext = np.array([r.chi_external_asymptotic for r in rows], dtype=float)
    alpha_req = np.array([r.alpha_required_for_2pi for r in rows], dtype=float)

    plt.figure(figsize=(10, 6))
    plt.plot(lam, chi_total, marker="o", linewidth=1, label=r"$\chi_E^{\rm solid}$")
    plt.plot(lam, chi_int, linewidth=1, label=r"$\chi_{\rm int}$")
    plt.plot(lam, chi_ext, linewidth=1, label=r"$\chi_{\rm ext}^{\rm asym}$")
    plt.axhline(TARGET_CHI_E, linestyle="--", label=r"target $2\pi$")
    plt.xlabel(r"$\lambda=R/a_0$")
    plt.ylabel("dimensionless energy factor")
    plt.title("SST solid-core constant-density chi_E diagnostic")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(lam, alpha_req, marker="o", linewidth=1, label=r"$\alpha_E$ required for $2\pi$")
    plt.axhline(1.75, linestyle="--", label=r"solid constant-volume $7/4$")
    plt.xlabel(r"$\lambda=R/a_0$")
    plt.ylabel(r"required energy constant $\alpha_E$")
    plt.title("Required thin-ring core constant for target chi_E")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path.with_name(path.stem + "_alpha_required.png"), dpi=180)
    plt.close()


def plot_alpha_sweep(rows, path: Path) -> None:
    al = np.array([r.alpha_E for r in rows], dtype=float)
    chi = np.array([r.chi_E for r in rows], dtype=float)
    plt.figure(figsize=(10, 6))
    plt.plot(al, chi, marker="o", linewidth=1, label=r"$\chi_E^{\rm solid}(\lambda=1)$")
    plt.axhline(TARGET_CHI_E, linestyle="--", label=r"target $2\pi$")
    plt.axvline(1.75, linestyle=":", label=r"solid constant-volume $7/4$")
    plt.xlabel(r"energy constant $\alpha_E$")
    plt.ylabel("dimensionless energy factor")
    plt.title("Solid-core constant-density alpha sweep at fixed lambda")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lambda-min", type=float, default=1.0)
    parser.add_argument("--lambda-max", type=float, default=8.0)
    parser.add_argument("--lambda-count", type=int, default=33)
    parser.add_argument("--alpha", type=float, default=1.75, help="thin-ring energy constant; solid constant-volume is 7/4")
    parser.add_argument("--beta", type=float, default=0.25, help="thin-ring speed constant; solid constant-volume is 1/4")
    parser.add_argument("--alpha-min", type=float, default=1.50)
    parser.add_argument("--alpha-max", type=float, default=2.00)
    parser.add_argument("--alpha-count", type=int, default=51)
    parser.add_argument("--alpha-sweep-lambda", type=float, default=1.0)
    args = parser.parse_args()

    t0 = time.time()
    base = SolidCoreParams(alpha_E=args.alpha, beta_V=args.beta)
    rows = scan_lambda(args.lambda_min, args.lambda_max, args.lambda_count, base)
    horn = evaluate_solid_core(SolidCoreParams(lambda_=1.0, alpha_E=args.alpha, beta_V=args.beta))
    min_abs = min(rows, key=lambda r: abs(r.chi_E - TARGET_CHI_E))
    min_total = min(rows, key=lambda r: r.chi_E)

    alpha_base = SolidCoreParams(lambda_=args.alpha_sweep_lambda, alpha_E=args.alpha, beta_V=args.beta)
    alpha_rows = scan_alpha(args.alpha_min, args.alpha_max, args.alpha_count, alpha_base)
    best_alpha = min(alpha_rows, key=lambda r: abs(r.chi_E - TARGET_CHI_E))

    write_csv(EXPORT_DIR / "solid_core_constant_density_scan.csv", rows)
    write_csv(EXPORT_DIR / "solid_core_constant_density_alpha_sweep.csv", alpha_rows)
    plot_lambda_scan(rows, EXPORT_DIR / "solid_core_constant_density_scan.png")
    plot_alpha_sweep(alpha_rows, EXPORT_DIR / "solid_core_constant_density_alpha_sweep.png")

    summary = {
        "run": "solid_core_constant_density",
        "status": "RESEARCH-TRACK / ASYMPTOTIC CHECK / NOT CANONIZED",
        "model": "Rankine solid core, constant density, thin-ring constant-volume alpha_E=7/4 by default",
        "warning": "The thin-ring formula is asymptotic for lambda>>1. Horn lambda=1 is an extrapolation and must not be canonized without a finite-core toroidal solve.",
        "lambda_min": args.lambda_min,
        "lambda_max": args.lambda_max,
        "lambda_count": args.lambda_count,
        "alpha_E": args.alpha,
        "beta_V": args.beta,
        "target_chi_E": TARGET_CHI_E,
        "horn_row": result_to_dict(horn),
        "best_lambda_to_2pi": result_to_dict(min_abs),
        "min_chi_row": result_to_dict(min_total),
        "alpha_sweep_lambda": args.alpha_sweep_lambda,
        "best_alpha_to_2pi": result_to_dict(best_alpha),
        "alpha_required_at_horn": alpha_required_for_target(1.0),
        "elapsed_s": time.time() - t0,
        "interpretation": "At lambda=1 and alpha_E=7/4, the solid constant-density thin-ring extrapolation lies close to 2*pi but does not derive it. The required alpha_E is reported explicitly to expose any calibration.",
    }
    write_json(EXPORT_DIR / "solid_core_constant_density_summary.json", summary)

    text_path = EXPORT_DIR / "solid_core_constant_density_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST solid-core constant-density chi_E diagnostic\n")
        f.write("================================================\n")
        f.write(f"alpha_E                        = {args.alpha:.16e}\n")
        f.write(f"beta_V                         = {args.beta:.16e}\n")
        f.write(f"target 2*pi                    = {TARGET_CHI_E:.16e}\n\n")
        f.write("Horn extrapolation row, lambda=1:\n")
        f.write(f"Xi_internal_rankine            = {horn.Xi_internal_rankine:.16e}\n")
        f.write(f"Xi_external_asymptotic         = {horn.Xi_external_asymptotic:.16e}\n")
        f.write(f"Xi_total                       = {horn.Xi_total:.16e}\n")
        f.write(f"chi_internal_rankine           = {horn.chi_internal_rankine:.16e}\n")
        f.write(f"chi_external_asymptotic        = {horn.chi_external_asymptotic:.16e}\n")
        f.write(f"chi_E                          = {horn.chi_E:.16e}\n")
        f.write(f"residual to 2pi                = {horn.target_residual:.16e}\n")
        f.write(f"alpha_E required for 2pi       = {horn.alpha_required_for_2pi:.16e}\n\n")
        f.write("Interpretation:\n")
        f.write("Solid constant-density removes positive cavity work and replaces it with Rankine internal kinetic energy.\n")
        f.write("The default alpha_E=7/4 is a thin-ring asymptotic constant for solid core + constant volume.\n")
        f.write("Because lambda=1 is not a thin-ring regime, near agreement with 2*pi is a hint, not a derivation.\n")
    print(f"[*] Wrote {text_path}")
    print(f"horn chi_E={horn.chi_E:.12g}, residual={horn.target_residual:.6g}, alpha_required={horn.alpha_required_for_2pi:.12g}")


if __name__ == "__main__":
    main()

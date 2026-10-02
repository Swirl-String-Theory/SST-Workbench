#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSTcore chi_E bulk matrix runner.

Runs a reproducible option matrix over lambda, epsilon, quadrature resolution,
kernel, core constant, and mass-energy mode.  The output is intended to make
model choices explicit: which combinations approach 2*pi, which only do so by
calibrated target-renormalization, and how strongly results depend on numerical
or physical assumptions.

This is research-track diagnostic infrastructure, not a canon derivation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, List

import matplotlib.pyplot as plt
import numpy as np

from sst_horn_torus_chiE import (
    EnergyMassMode,
    HornTorusKernel,
    HornTorusParams,
    evaluate_horn_torus,
    write_json,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EXPORT_DIR = SCRIPT_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
TARGET = 2.0 * math.pi


def try_cpp_backend(backend: str):
    if backend == "python":
        return None, "python-forced"
    try:
        from sst_trefoil_biot_build import import_module
        return import_module(auto_build=True, script_dir=str(SCRIPT_DIR)), "cpp"
    except Exception as exc:
        if backend == "cpp":
            raise RuntimeError(f"C++ backend requested but unavailable: {exc}") from exc
        print(f"[!] C++ backend unavailable ({exc}). Using pure Python backend.")
        return None, "python-fallback"


def parse_csv_floats(text: str | None, default: Iterable[float]) -> List[float]:
    if text is None or str(text).strip() == "":
        return list(default)
    return [float(x.strip()) for x in str(text).split(",") if x.strip()]


def parse_csv_ints(text: str | None, default: Iterable[int]) -> List[int]:
    if text is None or str(text).strip() == "":
        return list(default)
    return [int(x.strip()) for x in str(text).split(",") if x.strip()]


def parse_kernels(text: str | None, default: Iterable[HornTorusKernel]) -> List[HornTorusKernel]:
    if text is None or str(text).strip() == "":
        return list(default)
    return [HornTorusKernel.from_any(x.strip()) for x in str(text).split(",") if x.strip()]


def parse_modes(text: str | None, default: Iterable[EnergyMassMode]) -> List[EnergyMassMode]:
    if text is None or str(text).strip() == "":
        return list(default)
    return [EnergyMassMode.from_any(x.strip()) for x in str(text).split(",") if x.strip()]


def quality_defaults(quality: str):
    quality = quality.lower().strip()
    if quality == "smoke":
        return {
            "n_values": [1024, 4096],
            "lambda_count": 9,
            "eps_values": [1.0],
            "core_constants": [1.75],
            "kernels": [HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT],
        }
    if quality == "standard":
        return {
            "n_values": [2048, 8192, 32768],
            "lambda_count": 33,
            "eps_values": [0.5, 1.0, 1.5, 2.0],
            "core_constants": [1.5, 1.75, 2.0],
            "kernels": [HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT, HornTorusKernel.THIN_RING_ASYMPTOTIC],
        }
    if quality == "hq":
        return {
            "n_values": [4096, 8192, 16384, 32768, 65536],
            "lambda_count": 65,
            "eps_values": [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
            "core_constants": [1.5, 1.75, 2.0],
            "kernels": [HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT, HornTorusKernel.THIN_RING_ASYMPTOTIC],
        }
    if quality == "extreme":
        return {
            "n_values": [8192, 16384, 32768, 65536, 131072],
            "lambda_count": 129,
            "eps_values": [0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0],
            "core_constants": [1.25, 1.5, 1.75, 2.0, 2.25],
            "kernels": [HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT, HornTorusKernel.THIN_RING_ASYMPTOTIC],
        }
    raise ValueError("quality must be smoke, standard, hq, or extreme")


def row_key(d: dict):
    return (
        d["kernel"],
        d["mass_mode"],
        round(float(d.get("epsilon", 0.0)), 12),
        round(float(d.get("core_constant", 0.0)), 12),
        int(d.get("quadrature_n", 0)),
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # Stable field order: keys from first row, then any extra keys.
    keys = list(rows[0].keys())
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def make_plots(rows: list[dict], ranked: list[dict], outdir: Path) -> None:
    if not rows:
        return

    # Top residual bar chart.
    top = ranked[: min(24, len(ranked))]
    plt.figure(figsize=(12, 7))
    labels = [
        f"{r['kernel_short']}\n{r['mass_mode_short']}\neps={r['epsilon']}, N={r['quadrature_n']}"
        for r in top
    ]
    vals = [abs(float(r["best_target_residual"])) for r in top]
    plt.bar(range(len(vals)), vals)
    plt.axhline(0.0, linestyle="--")
    plt.xticks(range(len(vals)), labels, rotation=80, ha="right", fontsize=8)
    plt.ylabel(r"best $|(\chi_E-2\pi)/(2\pi)|$")
    plt.title("SST chi_E bulk matrix: closest non/forced options")
    plt.tight_layout()
    plt.savefig(outdir / "bulk_matrix_chiE_ranked_residuals.png", dpi=180)

    # Mass mode curves for one representative high-N regularized epsilon=1 if present.
    reg_rows = [r for r in rows if r["kernel"] == HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT.value and abs(float(r["epsilon"]) - 1.0) < 1e-12]
    if reg_rows:
        max_n = max(int(r["quadrature_n"]) for r in reg_rows)
        subset = [r for r in reg_rows if int(r["quadrature_n"]) == max_n]
        plt.figure(figsize=(10, 6))
        for mode in sorted({r["mass_mode"] for r in subset}):
            s = sorted([r for r in subset if r["mass_mode"] == mode], key=lambda x: float(x["lambda_"]))
            plt.plot([float(r["lambda_"]) for r in s], [float(r["chi_E"]) for r in s], marker="o", linewidth=1, label=mode)
        plt.axhline(TARGET, linestyle="--", label=r"target $2\pi$")
        plt.xlabel(r"$\lambda=R/a_0$")
        plt.ylabel(r"selected $\chi_E$")
        plt.title(f"Mass-mode curves, regularized, epsilon=1, N={max_n}")
        plt.grid(True, alpha=0.35)
        plt.legend()
        plt.tight_layout()
        plt.savefig(outdir / "bulk_matrix_chiE_mass_mode_curves.png", dpi=180)

    # Convergence at lambda=1.
    horn = [r for r in rows if abs(float(r["lambda_"]) - 1.0) < 1e-12 and r["kernel"] == HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT.value]
    if horn:
        plt.figure(figsize=(10, 6))
        for mode in sorted({r["mass_mode"] for r in horn}):
            s = sorted([r for r in horn if r["mass_mode"] == mode and abs(float(r["epsilon"]) - 1.0) < 1e-12], key=lambda x: int(x["quadrature_n"]))
            if s:
                plt.semilogx([int(r["quadrature_n"]) for r in s], [float(r["chi_E"]) for r in s], marker="o", linewidth=1, label=mode)
        plt.axhline(TARGET, linestyle="--", label=r"target $2\pi$")
        plt.xlabel("quadrature_n")
        plt.ylabel(r"selected $\chi_E$ at $\lambda=1$, $\epsilon=1$")
        plt.title("Quadrature convergence at horn limit")
        plt.grid(True, alpha=0.35)
        plt.legend()
        plt.tight_layout()
        plt.savefig(outdir / "bulk_matrix_chiE_convergence_lambda1.png", dpi=180)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", choices=["smoke", "standard", "hq", "extreme"], default="smoke")
    parser.add_argument("--backend", choices=["auto", "python", "cpp"], default="auto")
    parser.add_argument("--lambda-min", type=float, default=1.0)
    parser.add_argument("--lambda-max", type=float, default=8.0)
    parser.add_argument("--lambda-count", type=int, default=None)
    parser.add_argument("--eps-values", default=None, help="comma-separated epsilon values")
    parser.add_argument("--n-values", default=None, help="comma-separated quadrature sizes")
    parser.add_argument("--core-constants", default=None, help="comma-separated thin-ring core constants")
    parser.add_argument("--kernels", default=None, help="comma-separated: regularized,thin")
    parser.add_argument("--mass-modes", default=None, help="comma-separated mass modes")
    parser.add_argument("--include-target-renormalized", action="store_true", help="include forced target mode in matrix")
    args = parser.parse_args()

    defaults = quality_defaults(args.quality)
    n_values = parse_csv_ints(args.n_values, defaults["n_values"])
    eps_values = parse_csv_floats(args.eps_values, defaults["eps_values"])
    core_constants = parse_csv_floats(args.core_constants, defaults["core_constants"])
    kernels = parse_kernels(args.kernels, defaults["kernels"])
    lambda_count = args.lambda_count or defaults["lambda_count"]
    lambdas = np.linspace(args.lambda_min, args.lambda_max, lambda_count)
    if args.lambda_min > 1.0 and 1.0 not in lambdas:
        lambdas = np.concatenate([[1.0], lambdas])
    if args.mass_modes:
        modes = parse_modes(args.mass_modes, [])
    else:
        modes = [
            EnergyMassMode.KINETIC_ONLY,
            EnergyMassMode.KINETIC_PLUS_CAVITY,
            EnergyMassMode.VACUUM_SUBTRACTED,
        ]
        if args.include_target_renormalized:
            modes.append(EnergyMassMode.TARGET_RENORMALIZED)

    t0 = time.time()
    cpp_mod, backend_label = try_cpp_backend(args.backend)

    rows: list[dict] = []
    for kernel in kernels:
        eps_iter = eps_values if kernel == HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT else [1.0]
        cc_iter = core_constants if kernel == HornTorusKernel.THIN_RING_ASYMPTOTIC else [1.75]
        for n in n_values:
            for eps in eps_iter:
                for cc in cc_iter:
                    for lam in lambdas:
                        for mode in modes:
                            p = HornTorusParams(
                                lambda_=float(lam),
                                epsilon=float(eps),
                                quadrature_n=int(n),
                                core_constant=float(cc),
                                mass_mode=mode.value,
                            )
                            r = evaluate_horn_torus(p, kernel=kernel, cpp_mod=cpp_mod)
                            d = asdict(r)
                            d["core_constant"] = float(cc)
                            d["abs_target_residual"] = abs(float(d["target_residual"]))
                            d["forced_target_mode"] = (mode == EnergyMassMode.TARGET_RENORMALIZED)
                            d["kernel_short"] = "reg" if kernel == HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT else "thin"
                            d["mass_mode_short"] = {
                                EnergyMassMode.KINETIC_ONLY: "K",
                                EnergyMassMode.KINETIC_PLUS_CAVITY: "K+C",
                                EnergyMassMode.VACUUM_SUBTRACTED: "K-Cvac",
                                EnergyMassMode.TARGET_RENORMALIZED: "forced",
                            }[mode]
                            rows.append(d)

    # Best row per option combination.
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(row_key(r), []).append(r)
    ranked = []
    for key, group in groups.items():
        best = min(group, key=lambda x: abs(float(x["target_residual"])))
        ranked.append({
            "kernel": best["kernel"],
            "kernel_short": best["kernel_short"],
            "mass_mode": best["mass_mode"],
            "mass_mode_short": best["mass_mode_short"],
            "epsilon": best["epsilon"],
            "core_constant": best.get("core_constant", ""),
            "quadrature_n": best["quadrature_n"],
            "best_lambda": best["lambda_"],
            "best_chi_E": best["chi_E"],
            "best_chi_K": best["chi_K"],
            "best_chi_cavitation": best["chi_cavitation"],
            "best_chi_renormalization": best["chi_renormalization"],
            "best_target_residual": best["target_residual"],
            "best_abs_target_residual": abs(float(best["target_residual"])),
            "forced_target_mode": best["forced_target_mode"],
        })
    ranked.sort(key=lambda x: (bool(x["forced_target_mode"]), float(x["best_abs_target_residual"])))
    nonforced = [r for r in ranked if not r["forced_target_mode"]]
    summary = {
        "run": "bulk_matrix_chiE",
        "quality": args.quality,
        "backend": backend_label,
        "lambda_min": args.lambda_min,
        "lambda_max": args.lambda_max,
        "lambda_count": lambda_count,
        "eps_values": eps_values,
        "n_values": n_values,
        "core_constants": core_constants,
        "kernels": [k.value for k in kernels],
        "mass_modes": [m.value for m in modes],
        "row_count": len(rows),
        "ranked_count": len(ranked),
        "best_nonforced_combo": nonforced[0] if nonforced else None,
        "best_overall_combo": ranked[0] if ranked else None,
        "elapsed_s": time.time() - t0,
        "status": "RESEARCH-TRACK / BULK OPTION MATRIX / NOT CANONIZED",
        "interpretation": (
            "target_renormalized is a forced diagnostic and is excluded from best_nonforced_combo. "
            "A first-principles result must approach 2*pi without this forced mode or tuned regularization."
        ),
    }

    write_csv(EXPORT_DIR / "bulk_matrix_chiE_scan.csv", rows)
    write_csv(EXPORT_DIR / "bulk_matrix_chiE_ranked_summary.csv", ranked)
    write_json(EXPORT_DIR / "bulk_matrix_chiE_summary.json", summary)
    make_plots(rows, ranked, EXPORT_DIR)

    text_path = EXPORT_DIR / "bulk_matrix_chiE_run_results_summary.txt"
    with text_path.open("w", encoding="utf-8") as f:
        f.write("SST chi_E bulk option matrix\n")
        f.write("============================\n")
        f.write(f"quality        = {args.quality}\n")
        f.write(f"backend        = {backend_label}\n")
        f.write(f"row_count      = {len(rows)}\n")
        f.write(f"elapsed_s      = {summary['elapsed_s']:.3f}\n")
        f.write("\nBest non-forced combo:\n")
        f.write(json.dumps(summary["best_nonforced_combo"], indent=2))
        f.write("\n\nInterpretation:\n")
        f.write(summary["interpretation"] + "\n")
    print(f"[*] Wrote {EXPORT_DIR / 'bulk_matrix_chiE_scan.csv'}")
    print(f"[*] Wrote {EXPORT_DIR / 'bulk_matrix_chiE_ranked_summary.csv'}")
    print(f"[*] Wrote {EXPORT_DIR / 'bulk_matrix_chiE_summary.json'}")
    print(f"[*] Summary saved: {text_path}")
    if summary["best_nonforced_combo"]:
        b = summary["best_nonforced_combo"]
        print("=" * 80)
        print("Best non-forced combo")
        print("=" * 80)
        print(f"kernel       = {b['kernel']}")
        print(f"mass_mode    = {b['mass_mode']}")
        print(f"epsilon      = {b['epsilon']}")
        print(f"core_const   = {b['core_constant']}")
        print(f"N            = {b['quadrature_n']}")
        print(f"lambda       = {b['best_lambda']}")
        print(f"chi_E        = {float(b['best_chi_E']):.16g}")
        print(f"residual     = {float(b['best_target_residual']):+.6%}")
    print("[*] PASS: chi_E bulk matrix completed")


if __name__ == "__main__":
    main()

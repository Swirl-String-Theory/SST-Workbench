#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SST chi-phase v3: profile-derived torsional stiffness extractor.

This package intentionally archives the v1/v2 shared-moment identity checks and
moves to a non-tautological test.  The kernel extracts K_chi from a resolved
radial core profile v_theta(r), instead of defining K_chi = rho*v_swirl^2*J.

Outputs:
  exports/chi_v3_profile_stiffness.csv
  exports/chi_v3_profile_speed_ratio.png
  exports/chi_v3_profile_spectrum.csv
  exports/chi_v3_profile_spectrum.png
  exports/chi_v3_spectrum_convergence.csv
  exports/chi_v3_spectrum_convergence.png
  exports/chi_v3_run_results_summary.txt
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import time
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
EXPORT_DIR = os.path.join(SCRIPT_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# ===========================================================================
# SST canonical constants used only for dimensional scaling / reporting.
# ===========================================================================
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
        import sst_chi_phase_v3_py as backend
        return backend, "python"
    try:
        from sst_chi_phase_v3_build import import_module
        backend = import_module(auto_build=True, script_dir=SCRIPT_DIR)
        return backend, "cpp"
    except Exception as exc:
        print(f"[!] C++ backend unavailable ({exc}). Falling back to pure Python.")
        import sst_chi_phase_v3_py as backend
        return backend, "python"


def default_profiles() -> List[Tuple[str, str, Dict[str, float], str]]:
    """profile, normalization, params, human label."""
    return [
        ("uniform", "boundary", {}, "uniform boundary"),
        ("solid_body", "boundary", {}, "solid-body boundary"),
        ("quadratic_core", "boundary", {}, "quadratic core boundary"),
        ("irrotational_reg", "boundary", {"eps": 0.05}, "regularized 1/r boundary, eps=0.05"),
        ("rankine", "max", {"core": 0.35}, "Rankine-like max, core=0.35"),
        ("lamb_oseen", "max", {"sigma": 0.35}, "Lamb-Oseen-like max, sigma=0.35"),
        ("gaussian_core", "max", {"sigma": 0.35}, "Gaussian core max, sigma=0.35"),
        ("gaussian_shell", "max", {"r0": 0.75, "sigma": 0.12}, "Gaussian shell max, r0=0.75"),
        # Explicit calibration mode: included to show the tautological case.
        ("solid_body", "rms_r2", {}, "solid-body r2-RMS calibration (forces c/v=1)"),
    ]


def dict_get(row: Dict[str, Any], key: str) -> Any:
    return row[key] if isinstance(row, dict) else getattr(row, key)


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"[*] CSV saved: {path}")


def run_profile_stiffness(backend, n_radial: int) -> List[Dict[str, Any]]:
    print("[*] v3 profile-derived stiffness extraction")
    rows: List[Dict[str, Any]] = []
    for profile, norm, params, label in default_profiles():
        row = dict(backend.profile_metrics(
            profile,
            R_C,
            RHO_F,
            V_SWIRL,
            norm,
            params,
            n_radial,
        ))
        row["label"] = label
        row["params_repr"] = repr(params)
        row["implied_omega1_over_omegac"] = row["c_over_v_ref"]
        row["is_calibration_mode"] = 1 if norm.lower() in {"rms_r2", "r2_rms", "weighted_rms"} else 0
        rows.append(row)
        tag = "CALIBRATION" if row["is_calibration_mode"] else "EXTRACTED"
        print(
            f"    {tag:11s} | {label:48s} | c/v = {row['c_over_v_ref']:.12f} | "
            f"Kgeom/J = {row['Kgeom_over_J']:.12f}"
        )

    csv_path = os.path.join(EXPORT_DIR, "chi_v3_profile_stiffness.csv")
    write_csv(csv_path, rows, [
        "label", "profile", "normalization", "params_repr", "is_calibration_mode",
        "a_core", "rho_f", "v_ref", "I_chi", "K_chi", "J_numeric", "J_analytic_disk",
        "J_rel_error", "Kgeom_over_J", "c_chi", "c_over_v_ref", "implied_omega1_over_omegac",
        "scale", "raw_boundary", "raw_max_abs", "raw_rms_r2", "n_radial",
    ])

    # Plot extracted ratios; mark calibration mode separately.
    labels = [r["label"] for r in rows]
    ratios = np.array([float(r["c_over_v_ref"]) for r in rows])
    colors = ["tab:orange" if r["is_calibration_mode"] else "tab:blue" for r in rows]

    plt.figure(figsize=(13, 6))
    x = np.arange(len(rows))
    plt.bar(x, ratios, color=colors)
    plt.axhline(1.0, color="k", linestyle="--", label=r"$c_\chi/v_{ref}=1$")
    plt.xticks(x, labels, rotation=35, ha="right")
    plt.ylabel(r"$c_\chi / v_{ref}$")
    plt.title("v3 profile-derived torsional phase speed: not forced to equal 1")
    plt.legend()
    plt.grid(axis="y", alpha=0.4)
    plt.tight_layout()
    plot_path = os.path.join(EXPORT_DIR, "chi_v3_profile_speed_ratio.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")
    return rows


def run_profile_spectra(backend, rows: List[Dict[str, Any]], n_grid: int, n_max: int) -> List[Dict[str, Any]]:
    print("[*] v3 horn-loop spectra using profile-derived c_chi")
    selected_labels = [
        "uniform boundary",
        "solid-body boundary",
        "regularized 1/r boundary, eps=0.05",
        "solid-body r2-RMS calibration (forces c/v=1)",
    ]
    selected = [r for r in rows if r["label"] in selected_labels]
    out: List[Dict[str, Any]] = []
    plt.figure(figsize=(12, 6))
    for row in selected:
        spec = list(backend.horn_loop_frequency_ratios(float(row["c_over_v_ref"]), n_max, n_grid))
        ns = []
        vals = []
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
    plt.title(r"v3 horn-loop spectrum: profile-derived $c_\chi$ breaks the tautology")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plot_path = os.path.join(EXPORT_DIR, "chi_v3_profile_spectrum.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")

    csv_path = os.path.join(EXPORT_DIR, "chi_v3_profile_spectrum.csv")
    write_csv(csv_path, out, [
        "label", "profile", "normalization", "c_over_v_ref", "n",
        "continuous_ratio", "fd_ratio", "fd_relative_error_vs_cont",
    ])
    return out


def run_convergence(backend, n_max: int) -> List[Dict[str, Any]]:
    print("[*] v3 finite-difference convergence control")
    rows = [dict(r) for r in backend.spectrum_convergence(1.0, n_max, [128,256,512,1024,2048,4096,8192])]
    csv_path = os.path.join(EXPORT_DIR, "chi_v3_spectrum_convergence.csv")
    write_csv(csv_path, rows, ["N", "max_rel_error", "prediction", "c_over_v"])

    N = np.array([r["N"] for r in rows], dtype=float)
    err = np.array([r["max_rel_error"] for r in rows], dtype=float)
    pred = np.array([r["prediction"] for r in rows], dtype=float)
    plt.figure(figsize=(10, 6))
    plt.loglog(N, err, "o-", label="observed max error")
    plt.loglog(N, pred, "k--", label="central-difference prediction")
    plt.xlabel("periodic grid size N")
    plt.ylabel("max relative spectrum error")
    plt.title("v3 finite-difference convergence control")
    plt.legend()
    plt.grid(True, which="both")
    plt.tight_layout()
    plot_path = os.path.join(EXPORT_DIR, "chi_v3_spectrum_convergence.png")
    plt.savefig(plot_path, dpi=150)
    print(f"[*] Plot saved: {plot_path}")
    return rows


def summarize(backend_name: str, profile_rows: List[Dict[str, Any]], conv_rows: List[Dict[str, Any]], elapsed: float) -> str:
    non_cal = [r for r in profile_rows if not r["is_calibration_mode"]]
    ratios = np.array([float(r["c_over_v_ref"]) for r in non_cal])
    labels = [r["label"] for r in non_cal]
    closest_idx = int(np.argmin(np.abs(ratios - 1.0)))
    farthest_idx = int(np.argmax(np.abs(ratios - 1.0)))
    uniform = next(r for r in profile_rows if r["label"] == "uniform boundary")
    solid = next(r for r in profile_rows if r["label"] == "solid-body boundary")
    irrot = next(r for r in profile_rows if r["label"].startswith("regularized 1/r"))
    calib = next(r for r in profile_rows if r["is_calibration_mode"])

    lines = []
    lines.append("SST chi-phase v3 profile-derived stiffness summary")
    lines.append("====================================================")
    lines.append(f"backend                                      = {backend_name}")
    lines.append(f"rho_f                                        = {RHO_F:.16e} kg m^-3")
    lines.append(f"v_swirl                                      = {V_SWIRL:.16e} m s^-1")
    lines.append(f"omega_c                                      = {OMEGA_C:.16e} s^-1")
    lines.append(f"r_c                                          = {R_C:.16e} m")
    lines.append("")
    lines.append("Key result: v3 does not define K_chi = rho*v_swirl^2*J.")
    lines.append("It extracts K_chi = rho * ∫ v_theta(r)^2 r_perp^2 dA from profiles.")
    lines.append("")
    lines.append(f"uniform boundary c/v                         = {uniform['c_over_v_ref']:.16e}")
    lines.append(f"solid-body boundary c/v                      = {solid['c_over_v_ref']:.16e}")
    lines.append(f"solid-body expected sqrt(2/3)                = {math.sqrt(2.0/3.0):.16e}")
    lines.append(f"regularized 1/r boundary c/v                 = {irrot['c_over_v_ref']:.16e}")
    lines.append(f"r2-RMS calibration mode c/v                  = {calib['c_over_v_ref']:.16e}  (forced by normalization)")
    lines.append(f"closest non-calibration profile to 1          = {labels[closest_idx]} ({ratios[closest_idx]:.16e})")
    lines.append(f"farthest non-calibration profile from 1       = {labels[farthest_idx]} ({ratios[farthest_idx]:.16e})")
    lines.append(f"max |J_num/J_ana - 1|                        = {max(abs(float(r['J_rel_error'])) for r in profile_rows):.16e}")
    lines.append(f"finest-grid FD convergence error             = {conv_rows[-1]['max_rel_error']:.16e}")
    lines.append(f"elapsed                                      = {elapsed:.2f} s")
    lines.append("")
    lines.append("Interpretation:")
    lines.append("PASS means the package can distinguish genuine profile-derived speeds from")
    lines.append("the old shared-moment identity.  Only profiles whose r^2-weighted RMS swirl")
    lines.append("speed equals v_swirl produce c_chi=v_swirl without calibration.")
    lines.append("Therefore v3 is a non-tautological stiffness extractor, not a proof of")
    lines.append("Q_chi->Q_em or SU(2)/SU(3).")

    text = "\n".join(lines)
    path = os.path.join(EXPORT_DIR, "chi_v3_run_results_summary.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[*] Summary saved: {path}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", action="store_true", help="force pure-Python backend")
    parser.add_argument("--n-radial", type=int, default=200000, help="radial midpoint samples")
    parser.add_argument("--n-grid", type=int, default=4096, help="periodic FD grid for plotted spectra")
    parser.add_argument("--n-max", type=int, default=32, help="maximum mode number")
    args = parser.parse_args()

    t0 = time.time()
    backend, backend_name = load_backend(force_python=args.python)

    print("=" * 92)
    print("SST chi-phase v3: profile-derived torsional stiffness extractor")
    print("=" * 92)
    print(f"[*] backend = {backend_name}")
    print(f"[*] rho_f   = {RHO_F:.8e} kg m^-3")
    print(f"[*] v_swirl = {V_SWIRL:.8e} m s^-1")
    print(f"[*] omega_c = {OMEGA_C:.8e} s^-1")
    print(f"[*] r_c     = {R_C:.8e} m")
    print("[*] Status: non-tautological Research Track extractor; v1/v2 are archived consistency checks.")

    profile_rows = run_profile_stiffness(backend, args.n_radial)
    run_profile_spectra(backend, profile_rows, args.n_grid, args.n_max)
    conv_rows = run_convergence(backend, args.n_max)
    summary = summarize(backend_name, profile_rows, conv_rows, time.time() - t0)

    print("=" * 92)
    print("Summary")
    print("=" * 92)
    print(summary)

    # Non-tautology PASS criteria.
    solid = next(r for r in profile_rows if r["label"] == "solid-body boundary")
    solid_err = abs(float(solid["c_over_v_ref"]) - math.sqrt(2.0/3.0))
    non_cal = [r for r in profile_rows if not r["is_calibration_mode"]]
    spread = max(float(r["c_over_v_ref"]) for r in non_cal) - min(float(r["c_over_v_ref"]) for r in non_cal)
    if solid_err < 5e-5 and spread > 0.25:
        print("[*] PASS: v3 distinguishes profile-derived stiffness from the archived identity checks.")
        return 0
    print("[!] FAIL: v3 did not show expected profile-dependent spread.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""
Publication-quality matplotlib figures for the SST-71 benchmark:
1. A_tot(omega) vs photon energy with reference -8/17
2. Control comparison (main vs no anticommutator vs non-helical)
3. Convergence plot
Saves PNG and PDF.

Use --verbose to log each saved figure; --debug for extra detail.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import numpy as np
import matplotlib.pyplot as plt

import constants

logger = logging.getLogger(__name__)

A_REF = constants.A_expected  # -8/17


def _load_csv(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load omega_eV, A_tot, and optionally Gamma columns. Returns (omega_eV, A_tot, Gamma_sum)."""
    omega, A, G_sum = [], [], []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            omega.append(float(row["omega_eV"]))
            A.append(float(row["A_tot"]))
            g1 = float(row.get("Gamma_h_plus1", 0))
            g2 = float(row.get("Gamma_h_minus1", 0))
            G_sum.append(g1 + g2)
    return np.array(omega), np.array(A), np.array(G_sum)


def plot_A_tot_vs_energy(
    csv_path: str,
    out_dir: str | None = None,
    ref_line: float = A_REF,
) -> None:
    """Figure 1: A_tot(omega) vs photon energy (eV) with horizontal reference line at -8/17."""
    omega, A, _ = _load_csv(csv_path)
    fig, ax = plt.subplots()
    ax.plot(omega, A, "o-", label=r"$A_{\mathrm{tot}}(\omega)$")
    ax.axhline(ref_line, color="gray", linestyle="--", label=r"$-8/17$")
    ax.set_xlabel("Photon energy (eV)")
    ax.set_ylabel(r"$A_{\mathrm{tot}}$")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    base = os.path.splitext(os.path.basename(csv_path))[0]
    out_dir = out_dir or os.path.dirname(csv_path)
    fig.savefig(os.path.join(out_dir, f"{base}_A_tot.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, f"{base}_A_tot.pdf"))
    plt.close(fig)


def plot_control_comparison(
    main_csv: str,
    no_anticommutator_csv: str,
    non_helical_csv: str,
    out_dir: str | None = None,
    broken_axisymmetry_csv: str | None = None,
) -> None:
    """Figure 2: Control comparison – main vs no anticommutator vs non-helical (asymmetry vs energy).
    If broken_axisymmetry_csv is provided, add it with label indicating secondary mirror-symmetric perturbation."""
    o1, A1, _ = _load_csv(main_csv)
    o2, A2, _ = _load_csv(no_anticommutator_csv)
    o3, A3, _ = _load_csv(non_helical_csv)
    fig, ax = plt.subplots()
    ax.plot(o1, A1, "o-", label="Main (helical)")
    ax.plot(o2, A2, "s-", label="No anticommutator")
    ax.plot(o3, A3, "^-", label="Non-helical")
    if broken_axisymmetry_csv and os.path.isfile(broken_axisymmetry_csv):
        o4, A4, _ = _load_csv(broken_axisymmetry_csv)
        ax.plot(o4, A4, "d-", alpha=0.8, label="Broken axisymmetry (secondary, mirror-symmetric)")
    ax.axhline(A_REF, color="gray", linestyle="--", label=r"$-8/17$")
    ax.set_xlabel("Photon energy (eV)")
    ax.set_ylabel(r"$A_{\mathrm{tot}}$")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_dir = out_dir or os.path.dirname(main_csv)
    fig.savefig(os.path.join(out_dir, "control_comparison.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, "control_comparison.pdf"))
    plt.close(fig)


def plot_stronger_control_A_tot(
    csv_path: str,
    out_dir: str | None = None,
    ref_line: float = A_REF,
) -> None:
    """A_tot(omega) for the stronger control (helical_mode_plus1) with reference line at -8/17."""
    omega, A, _ = _load_csv(csv_path)
    fig, ax = plt.subplots()
    ax.plot(omega, A, "o-", color="C3", label=r"$A_{\mathrm{tot}}(\omega)$ (helical mode +1)")
    ax.axhline(ref_line, color="gray", linestyle="--", label=r"$-8/17$")
    ax.set_xlabel("Photon energy (eV)")
    ax.set_ylabel(r"$A_{\mathrm{tot}}$")
    ax.set_title("Stronger control: one-sided Fourier perturbation (breaks m↔−m pairing)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_dir = out_dir or os.path.dirname(csv_path)
    base = os.path.splitext(os.path.basename(csv_path))[0]
    fig.savefig(os.path.join(out_dir, f"{base}_A_tot.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, f"{base}_A_tot.pdf"))
    plt.close(fig)


def _load_eps_scan_csv(path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load eps and A_tot from control_helical_mode_plus1_eps_scan.csv. Returns (eps, A_tot)."""
    eps_list, A_list = [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            eps_list.append(float(row["eps"]))
            A_list.append(float(row["A_tot"]))
    return np.array(eps_list), np.array(A_list)


def plot_stronger_control_eps_scan(
    csv_path: str,
    out_dir: str | None = None,
    ref_line: float = A_REF,
) -> None:
    """Epsilon scan at fixed photon energy: A_tot vs eps with reference -8/17.
    At eps=0 recovers main benchmark; finite eps shows deviation."""
    eps_arr, A = _load_eps_scan_csv(csv_path)
    fig, ax = plt.subplots()
    ax.plot(eps_arr, A, "o-", color="C3", label=r"$A_{\mathrm{tot}}(\varepsilon)$")
    ax.axhline(ref_line, color="gray", linestyle="--", label=r"$-8/17$")
    ax.set_xlabel(r"Perturbation strength $\varepsilon$")
    ax.set_ylabel(r"$A_{\mathrm{tot}}$")
    ax.set_title("Stronger control: epsilon scan at 30 eV (helical_mode_plus1)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_dir = out_dir or os.path.dirname(csv_path)
    fig.savefig(os.path.join(out_dir, "control_helical_mode_plus1_eps_scan.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, "control_helical_mode_plus1_eps_scan.pdf"))
    plt.close(fig)


def _load_convergence_helical_mode_plus1_csv(path: str) -> list[dict]:
    """Load convergence_study_helical_mode_plus1.csv. Returns list of row dicts."""
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def plot_convergence_helical_mode_plus1(
    convergence_csv: str,
    out_dir: str | None = None,
    ref_line: float = A_REF,
) -> None:
    """Stronger-control convergence: asymmetry vs sweep_value for R_max, N_r, N_theta, l_max (4 panels)."""
    rows = _load_convergence_helical_mode_plus1_csv(convergence_csv)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    for idx, (sweep_type, xlabel) in enumerate([
        ("R_max", r"$R_{\max}\,/\,a_0^{\mathrm{SST}}$"),
        ("N_r", r"$N_r$"),
        ("N_theta", r"$N_\theta$"),
        ("l_max", r"$l_{\max}$"),
    ]):
        ax = axes[idx]
        var_rows = [r for r in rows if r["sweep_type"] == sweep_type]
        if var_rows:
            x = [float(r["sweep_value"]) for r in var_rows]
            y = [float(r["asymmetry"]) for r in var_rows]
            ax.plot(x, y, "o-")
        ax.axhline(ref_line, color="gray", linestyle="--", label=r"$-8/17$")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r"$A_{\mathrm{tot}}$")
        ax.set_title(f"Stronger control: {sweep_type}")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.suptitle("Stronger-control convergence (30 eV, eps=0.25)")
    fig.tight_layout()
    out_dir = out_dir or os.path.dirname(convergence_csv)
    fig.savefig(os.path.join(out_dir, "convergence_helical_mode_plus1.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, "convergence_helical_mode_plus1.pdf"))
    plt.close(fig)


def plot_convergence_helical_mode_plus1_delta(
    convergence_csv: str,
    out_dir: str | None = None,
) -> None:
    """Stronger-control convergence: delta_from_minus_8_over_17 vs sweep_value for each sweep type (4 panels)."""
    rows = _load_convergence_helical_mode_plus1_csv(convergence_csv)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    for idx, (sweep_type, xlabel) in enumerate([
        ("R_max", r"$R_{\max}\,/\,a_0^{\mathrm{SST}}$"),
        ("N_r", r"$N_r$"),
        ("N_theta", r"$N_\theta$"),
        ("l_max", r"$l_{\max}$"),
    ]):
        ax = axes[idx]
        var_rows = [r for r in rows if r["sweep_type"] == sweep_type]
        if var_rows:
            x = [float(r["sweep_value"]) for r in var_rows]
            y = [float(r["delta_from_minus_8_over_17"]) for r in var_rows]
            ax.plot(x, y, "o-")
        ax.axhline(0.0, color="gray", linestyle="--", label=r"$0$ (pinned $-8/17$)")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r"$A_{\mathrm{tot}} - (-8/17)$")
        ax.set_title(f"Stronger control: {sweep_type}")
        ax.legend()
        ax.grid(True, alpha=0.3)
    fig.suptitle("Stronger-control deviation from -8/17 (30 eV, eps=0.25)")
    fig.tight_layout()
    out_dir = out_dir or os.path.dirname(convergence_csv)
    fig.savefig(os.path.join(out_dir, "convergence_helical_mode_plus1_delta.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, "convergence_helical_mode_plus1_delta.pdf"))
    plt.close(fig)


def plot_convergence(
    convergence_csv: str,
    out_dir: str | None = None,
) -> None:
    """Figure 3: Convergence – A_tot vs R_max, N_r, N_theta, l_max at representative energy."""
    rows = []
    with open(convergence_csv, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    for idx, (var, xlabel) in enumerate([
        ("R_max", r"$R_{\max}\,/\,a_0^{\mathrm{SST}}$"),
        ("N_r", r"$N_r$"),
        ("N_theta", r"$N_\theta$"),
        ("l_max", r"$l_{\max}$"),
    ]):
        ax = axes[idx]
        var_rows = [r for r in rows if r["variable"] == var]
        if var_rows:
            x = [float(r["value"]) for r in var_rows]
            y = [float(r["A_tot"]) for r in var_rows]
            ax.plot(x, y, "o-")
            ax.axhline(A_REF, color="gray", linestyle="--", label=r"$-8/17$")
            ax.set_xlabel(xlabel)
            ax.set_ylabel(r"$A_{\mathrm{tot}}$")
            ax.legend()
            ax.grid(True, alpha=0.3)
    fig.suptitle("Convergence at 30 eV")
    fig.tight_layout()
    out_dir = out_dir or os.path.dirname(convergence_csv)
    fig.savefig(os.path.join(out_dir, "convergence.png"), dpi=150)
    fig.savefig(os.path.join(out_dir, "convergence.pdf"))
    plt.close(fig)


def main() -> None:
    """Generate all figures from CSVs in the benchmark directory.
    Use --verbose to log each saved figure; --debug for extra detail.
    """
    parser = argparse.ArgumentParser(
        description="SST-71 benchmark: generate A_tot, control comparison, and convergence figures.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Log each saved figure")
    parser.add_argument("--debug", action="store_true", help="Log extra detail")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    elif args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    bench_dir = os.path.dirname(os.path.abspath(__file__))
    main_csv = os.path.join(bench_dir, "benchmark_main.csv")
    no_ac_csv = os.path.join(bench_dir, "control_no_anticommutator.csv")
    non_hel_csv = os.path.join(bench_dir, "control_non_helical.csv")
    conv_csv = os.path.join(bench_dir, "convergence_study.csv")

    if os.path.isfile(main_csv):
        plot_A_tot_vs_energy(main_csv, out_dir=bench_dir)
        logger.info("Saved A_tot vs energy figure (PNG and PDF).")
        if not args.verbose and not args.debug:
            print("Saved A_tot vs energy figure.")
    broken_ax_csv = os.path.join(bench_dir, "control_broken_axisymmetry.csv")
    if os.path.isfile(main_csv) and os.path.isfile(no_ac_csv) and os.path.isfile(non_hel_csv):
        plot_control_comparison(
            main_csv, no_ac_csv, non_hel_csv, out_dir=bench_dir,
            broken_axisymmetry_csv=broken_ax_csv,
        )
        logger.info("Saved control comparison figure (PNG and PDF).")
        if not args.verbose and not args.debug:
            print("Saved control comparison figure.")
    if os.path.isfile(conv_csv):
        plot_convergence(conv_csv, out_dir=bench_dir)
        logger.info("Saved convergence figure (PNG and PDF).")
        if not args.verbose and not args.debug:
            print("Saved convergence figure.")

    stronger_csv = os.path.join(bench_dir, "control_helical_mode_plus1.csv")
    eps_scan_csv = os.path.join(bench_dir, "control_helical_mode_plus1_eps_scan.csv")
    if os.path.isfile(stronger_csv):
        plot_stronger_control_A_tot(stronger_csv, out_dir=bench_dir)
        logger.info("Saved stronger control A_tot vs energy figure (PNG and PDF).")
        if not args.verbose and not args.debug:
            print("Saved stronger control A_tot vs energy figure.")
    if os.path.isfile(eps_scan_csv):
        plot_stronger_control_eps_scan(eps_scan_csv, out_dir=bench_dir)
        logger.info("Saved stronger control epsilon-scan figure (PNG and PDF).")
        if not args.verbose and not args.debug:
            print("Saved stronger control epsilon-scan figure.")

    conv_stronger_csv = os.path.join(bench_dir, "convergence_study_helical_mode_plus1.csv")
    if os.path.isfile(conv_stronger_csv):
        plot_convergence_helical_mode_plus1(conv_stronger_csv, out_dir=bench_dir)
        plot_convergence_helical_mode_plus1_delta(conv_stronger_csv, out_dir=bench_dir)
        logger.info("Saved stronger-control convergence figures (PNG and PDF).")
        if not args.verbose and not args.debug:
            print("Saved stronger-control convergence figures.")

    if not os.path.isfile(main_csv):
        print("Run benchmark_scan.py first to generate CSVs.")


if __name__ == "__main__":
    main()

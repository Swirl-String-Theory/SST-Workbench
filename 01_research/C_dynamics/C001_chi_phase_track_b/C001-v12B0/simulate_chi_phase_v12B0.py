#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simulation runner for SST chi-phase package v12B.0."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sst_chi_phase_v12B0_py as v12b

EXPORTS = Path(__file__).parent / "exports"
EXPORTS.mkdir(exist_ok=True)


def write_csv(path: Path, rows: list, fieldnames: list | None = None) -> None:
    if not rows:
        return
    if fieldnames is None:
        keys = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def make_plots(data: dict) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    conv = data["convergence"]
    R = [row["R_max"] for row in conv]
    raw_alpha = [row["alpha_ring_raw_R"] for row in conv]
    a_tail_1 = [row["tail_terms_1_alpha_inf_est"] for row in conv]
    a_tail_2 = [row["tail_terms_2_alpha_inf_est"] for row in conv]
    a_tail_4 = [row["tail_terms_4_alpha_inf_est"] for row in conv]

    fig = plt.figure(figsize=(8.0, 5.0))
    ax = fig.add_subplot(111)
    ax.plot(R, raw_alpha, marker="o", label="raw alpha(R)")
    ax.plot(R, a_tail_1, marker="s", label="tail-corrected 1 term")
    ax.plot(R, a_tail_2, marker="^", label="tail-corrected 2 terms")
    ax.plot(R, a_tail_4, marker="x", label="tail-corrected 4 terms")
    ax.axhline(v12b.NLS_ALPHA_LEGACY, linestyle="--", label="legacy NLS 1.61")
    ax.axhline(v12b.PHI, linestyle=":", label="phi")
    ax.set_xlabel("R_max / xi")
    ax.set_ylabel("alpha_ring estimate")
    ax.set_title("v12B.0 analytic-tail alpha_ring extraction")
    ax.legend()
    fig.tight_layout()
    fig.savefig(EXPORTS / "chi_v12B0_tail_corrected_alpha.png", dpi=160)
    plt.close(fig)

    frows = data["F_tail_validation"]
    Rf = [row["R"] for row in frows]
    fig = plt.figure(figsize=(8.0, 5.0))
    ax = fig.add_subplot(111)
    for k in [1,2,3,4]:
        ax.loglog(Rf, [row[f"abs_error_k{k}"] for row in frows], marker="o", label=f"F tail k={k}")
    ax.set_xlabel("R / xi")
    ax.set_ylabel("|F_numeric - F_asym|")
    ax.set_title("v12B.0 GP/NLSE algebraic tail validation")
    ax.legend()
    fig.tight_layout()
    fig.savefig(EXPORTS / "chi_v12B0_F_tail_error.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r-right", type=float, default=160.0)
    ap.add_argument("--n-init", type=int, default=2200)
    ap.add_argument("--tol", type=float, default=1e-8)
    args = ap.parse_args()

    t0 = time.perf_counter()
    print("SST chi-phase package v12B.0")
    print("Track B: GP/NLSE algebraic-tail and asymptotic extraction audit")
    print("=" * 78)
    data = v12b.run_v12B0(r_right=args.r_right, n_init=args.n_init, tol=args.tol)
    elapsed = time.perf_counter() - t0

    principal = data["principal_estimate"]
    fit12 = data["unconstrained_fits"][0]
    fit246 = data["unconstrained_fits"][2]
    jack = data["jackknife"][0]

    print(f"BVP success: {data['success']}  nodes={data['n_nodes_bvp']}  C1*={data['C1_star']:.8f}")
    print("Analytic tail:")
    print("  F(r)=1 -1/(2r^2) -9/(8r^4) -161/(16r^6) - ...")
    print("  C_inf-C(R)= -1/(4R^2)+1/(4R^4)+11/(6R^6)+179/(8R^8)+...")
    print()
    print("Principal analytic-tail estimate (4 terms, R>=12):")
    print(f"  alpha_inf={principal['alpha_inf_mean']:.9f}")
    print(f"  beta_inf(q=0)={principal['beta_inf_q0_mean']:.9f}")
    print(f"  std(alpha)={principal['alpha_inf_std']:.3e}")
    print(f"  delta alpha - legacy NLS={principal['delta_alpha_minus_NLS']:+.6e}")
    print(f"  alpha - phi={principal['alpha_minus_phi']:+.6e}")
    print()
    print("Unconstrained fit checks:")
    print(f"  powers 2,4 minR=12: alpha={fit12['alpha_inf']:.9f}, rms={fit12['fit_rms']:.2e}, A2={fit12['A_2']:.6f}, A4={fit12['A_4']:.6f}")
    print(f"  powers 2,4,6 minR=12: alpha={fit246['alpha_inf']:.9f}, rms={fit246['fit_rms']:.2e}, A2={fit246['A_2']:.6f}, A4={fit246['A_4']:.6f}, A6={fit246['A_6']:.6f}")
    print(f"  jackknife 2,4 minR=12: alpha_mean={jack['alpha_jackknife_mean']:.9f}, se={jack['alpha_jackknife_se']:.2e}")

    write_csv(EXPORTS / "chi_v12B0_tail_coefficients.csv", data["tail_coefficients"])
    write_csv(EXPORTS / "chi_v12B0_expected_C_fit_coefficients.csv", data["expected_C_fit_coefficients"])
    write_csv(EXPORTS / "chi_v12B0_convergence.csv", data["convergence"])
    write_csv(EXPORTS / "chi_v12B0_F_tail_validation.csv", data["F_tail_validation"])
    write_csv(EXPORTS / "chi_v12B0_unconstrained_fits.csv", data["unconstrained_fits"])
    write_csv(EXPORTS / "chi_v12B0_analytic_tail_stats.csv", data["analytic_tail_stats"])
    write_csv(EXPORTS / "chi_v12B0_jackknife.csv", data["jackknife"])
    write_csv(EXPORTS / "chi_v12B0_principal_estimate.csv", [principal])
    make_plots(data)

    with open(EXPORTS / "chi_v12B0_results.json", "w") as f:
        json.dump(data, f, indent=2, default=str)

    summary = [
        "SST chi-phase package v12B.0 summary",
        "=" * 56,
        "",
        "Track: B — GP/NLSE algebraic-tail and asymptotic alpha_ring extraction audit",
        "Status: Strong Research Track / asymptotic-extraction support; not locked CANON",
        "",
        "Purpose:",
        "  v11B.0 established the variational core-envelope gate: the GP/NLSE ODE",
        "  follows from the SST envelope functional when A=B=C. v12B.0 validates",
        "  the algebraic far-field tail used to extract alpha_ring^GP(infinity).",
        "",
        "Analytic large-r tail:",
        "  F(r)=1 - 1/(2 r^2) - 9/(8 r^4) - 161/(16 r^6) - ...",
        "",
        "Corrected GP/NLSE energy integrand:",
        "  I(r)=F^2/r + F'^2 r + 1/2(F^2-1)^2 r",
        "",
        "Energy-tail result:",
        "  I(r)-1/r = -1/(2 r^3) + 1/r^5 + 11/r^7 + 179/r^9 + ...",
        "  C_inf-C(R)= -1/(4R^2)+1/(4R^4)+11/(6R^6)+179/(8R^8)+...",
        "  C(R)=C_inf+1/(4R^2)-1/(4R^4)-11/(6R^6)-179/(8R^8)-...",
        "",
        f"BVP success: {data['success']}",
        f"BVP nodes: {data['n_nodes_bvp']}",
        f"C1* axis slope: {data['C1_star']:.7e}",
        "",
        "Principal estimate: analytic 4-term tail correction, R>=12",
        f"  alpha_inf={principal['alpha_inf_mean']:.9f}",
        f"  beta_inf(q=0)={principal['beta_inf_q0_mean']:.9f}",
        f"  std(alpha)={principal['alpha_inf_std']:.3e}",
        f"  delta alpha - legacy NLS={principal['delta_alpha_minus_NLS']:+.6e}",
        f"  alpha - phi={principal['alpha_minus_phi']:+.6e}",
        "",
        "Unconstrained fit checks:",
        f"  C=Cinf+A2/R^2+A4/R^4, minR=12: alpha={fit12['alpha_inf']:.9f}, A2={fit12['A_2']:.7f}, A4={fit12['A_4']:.7f}, rms={fit12['fit_rms']:.2e}",
        f"  expected analytic A2=+0.25, A4=-0.25 (higher terms shift finite-range fits)",
        f"  jackknife alpha mean={jack['alpha_jackknife_mean']:.9f}, se={jack['alpha_jackknife_se']:.2e}",
        "",
        "Conclusion:",
        "  v12B.0 makes the asymptotic extraction non-ad hoc. The 1/R^2+1/R^4",
        "  extrapolation follows from the algebraic GP/NLSE vortex tail, not from a",
        "  chosen plotting fit. This supports the conditional value",
        "  alpha_ring^GP(infinity) ~ 1.61935, beta_ring(q=0) ~ 0.61935.",
        "  The remaining locked-CANON gate remains the SST-internal proof that the",
        "  core-envelope stiffnesses satisfy A=B=C.",
        "",
        f"Elapsed: {elapsed:.2f} s",
    ]
    (EXPORTS / "chi_v12B0_run_results_summary.txt").write_text("\n".join(summary) + "\n")

    print(f"Exports written to: {EXPORTS}")
    print(f"Elapsed: {elapsed:.2f} s")


if __name__ == "__main__":
    main()

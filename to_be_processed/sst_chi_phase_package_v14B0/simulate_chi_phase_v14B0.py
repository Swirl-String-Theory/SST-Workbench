#!/usr/bin/env python3
"""Run the v14B.0 internal A=B=C gate audit."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

from sst_chi_phase_v14B0_py import (
    analyze_case,
    canonical_cases,
    dimensionless_reduction_table,
    proximity_metrics,
)


def write_csv(path: Path, rows):
    rows = list(rows)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="exports", help="output directory")
    parser.add_argument("--no-plots", action="store_true", help="skip PNG plots")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    out = root / args.out
    out.mkdir(parents=True, exist_ok=True)

    results = [analyze_case(c) for c in canonical_cases()]
    rows = [r.__dict__ for r in results]
    write_csv(out / "chi_v14B0_coefficient_gate.csv", rows)

    reduction = dimensionless_reduction_table()
    with (out / "chi_v14B0_dimensionless_reduction.json").open("w", encoding="utf-8") as f:
        json.dump(reduction, f, indent=2)

    metrics = proximity_metrics()
    with (out / "chi_v14B0_alpha_proximity.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    if not args.no_plots:
        names = [r.name for r in results]
        phase = [r.phase_coeff for r in results]
        depl = [r.depletion_coeff for r in results]
        x = range(len(names))
        fig = plt.figure(figsize=(10, 5))
        plt.plot(list(x), phase, marker="o", label="phase coefficient")
        plt.plot(list(x), depl, marker="s", label="depletion coefficient")
        plt.axhline(1.0, linestyle="--", linewidth=1, label="unit GP target")
        plt.xticks(list(x), names, rotation=35, ha="right")
        plt.ylabel("ODE coefficient")
        plt.title("v14B.0 coefficient gate: only A=B=C,n=1 gives the unit GP/NLSE ODE")
        plt.legend()
        plt.tight_layout()
        fig.savefig(out / "chi_v14B0_coefficient_gate.png", dpi=180)
        plt.close(fig)

    pass_case = next(r for r in results if r.name == "single_isotropic_core_modulus")
    old_case = next(r for r in results if r.name == "v10B0_old_potential_prefactor_quarter")

    summary = f"""SST chi-phase package v14B.0 summary
========================================================

Track: B — internal A=B=C gate for the GP/NLSE core-envelope reduction
Status: Derived-conditional theorem / proposed CANON gate

Core claim tested:
  If the SST resolved core envelope is a single isotropic complex order
  parameter with one stiffness modulus, then the dimensionless radial energy
  has A_grad=B_phase=C_depletion. For winding n=1 this gives exactly the
  GP/NLSE ODE used in v10B.1-v12B.0.

Radial Lagrangian convention:
  L_r = A F'^2 r + B n^2 F^2/r + (C/2)(F^2-1)^2 r

Euler-Lagrange reduction:
  F'' + F'/r - (B/A)n^2 F/r^2 + (C/A)F(1-F^2) = 0

PASS case:
  name: {pass_case.name}
  A={pass_case.A_grad}, B={pass_case.B_phase}, C={pass_case.C_depletion}, n={pass_case.n}
  phase coefficient:     {pass_case.phase_coeff:.12g}
  depletion coefficient: {pass_case.depletion_coeff:.12g}
  energy potential prefactor C/2: {pass_case.energy_potential_prefactor:.12g}
  matches unit GP ODE: {pass_case.ode_matches_unit_gp}

v10B.0 failure case:
  name: {old_case.name}
  A={old_case.A_grad}, B={old_case.B_phase}, C={old_case.C_depletion}, n={old_case.n}
  phase coefficient:     {old_case.phase_coeff:.12g}
  depletion coefficient: {old_case.depletion_coeff:.12g}
  energy potential prefactor C/2: {old_case.energy_potential_prefactor:.12g}
  matches unit GP ODE: {old_case.ode_matches_unit_gp}

Dimensionless reduction from a single isotropic envelope energy:
  E = kappa ∫ [ |grad Psi|^2 + (1/(2 xi^2))(1-|Psi|^2)^2 ] d^2x
  Psi = F(r/xi) exp(i n theta)
  => A=B=C=1 after rho=xi r, up to the common factor 2π kappa.

Alpha-ring context inherited from v12B.0:
  alpha_ring^GP(infinity) ≈ {metrics['alpha_gp_inf']:.9f}
  alpha_ring^GP - legacy NLS 1.61 = {metrics['delta_to_legacy_nls']:+.9f}
  alpha_ring^GP - phi = {metrics['delta_to_phi']:+.9f}

Canon gate:
  v14B.0 proves A=B=C only under the single-isotropic-core-envelope axiom.
  To label the GP/NLSE alpha_ring result CANON-derived, the canon must accept
  that the resolved SST core envelope is described by this one-modulus isotropic
  complex order parameter in the long-wavelength core limit.

Files exported:
  chi_v14B0_coefficient_gate.csv
  chi_v14B0_dimensionless_reduction.json
  chi_v14B0_alpha_proximity.json
  chi_v14B0_coefficient_gate.png
"""
    (out / "chi_v14B0_run_results_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

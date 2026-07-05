#!/usr/bin/env python3
"""v15B.0 consistency audit for the canonized single-modulus core lemma."""
from __future__ import annotations
from pathlib import Path
import csv


def audit_cases():
    cases = []
    # name, A, B, C, expected_ode_phase_coeff B/A, expected_ode_depletion C/A
    for name, A, B, C in [
        ("canon_single_modulus", 1.0, 1.0, 1.0),
        ("v10B0_quarter_potential", 1.0, 1.0, 0.5),
        ("phase_stiffness_mismatch", 1.0, 0.9, 1.0),
        ("depletion_stiffness_mismatch", 1.0, 1.0, 1.1),
    ]:
        cases.append({
            "case": name,
            "A": A,
            "B": B,
            "C": C,
            "B_over_A": B/A,
            "C_over_A": C/A,
            "is_unit_GP_NLSE": abs(B/A-1.0) < 1e-12 and abs(C/A-1.0) < 1e-12,
            "energy_depletion_prefactor": C/2.0,
        })
    return cases


def main():
    out = Path(__file__).resolve().parent / "exports"
    out.mkdir(exist_ok=True)
    rows = audit_cases()
    csv_path = out / "chi_v15B0_abc_consistency.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    summary = out / "chi_v15B0_run_results_summary.txt"
    lines = [
        "SST chi-phase package v15B.0 summary",
        "=======================================",
        "",
        "Status: CANON LEMMA / LOCAL CORE MODEL",
        "",
        "Canonized lemma:",
        "  E_perp[Psi] = kappa ∫ ( |grad Psi|^2 + (1/(2 xi^2))(1-|Psi|^2)^2 ) d^2x",
        "",
        "Polar reduction:",
        "  L_r = F'^2 r + n^2 F^2/r + (1/2)(F^2-1)^2 r",
        "",
        "Generic comparison:",
        "  L_r = A F'^2 r + B n^2 F^2/r + (C/2)(F^2-1)^2 r",
        "  canon single-modulus => A=B=C",
        "",
        "Unit vortex ODE:",
        "  F'' + F'/r - F/r^2 + F(1-F^2) = 0",
        "",
        "Audit cases:",
    ]
    for row in rows:
        lines.append(f"  {row['case']}: B/A={row['B_over_A']:.6g}, C/A={row['C_over_A']:.6g}, unit_GP_NLSE={row['is_unit_GP_NLSE']}, depletion_prefactor={row['energy_depletion_prefactor']:.6g}")
    lines += [
        "",
        "Conclusion:",
        "  The v10B.1/v12B.0 GP/NLSE equation is canon-derived from the accepted single-modulus lemma.",
        "  The v10B.0 quarter-potential convention is rejected for this unit ODE because C/A=1/2.",
        "  This package does not canonize alpha_ring=1.61 or alpha_ring=phi.",
    ]
    summary.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(summary.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()

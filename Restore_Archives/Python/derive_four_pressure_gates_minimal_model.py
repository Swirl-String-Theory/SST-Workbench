#!/usr/bin/env python3
"""
derive_four_pressure_gates_minimal_model.py

Symbolic "derived-within-model" proof for the four remaining gates:

1. N_p = 4 pressure sectors.
2. sigma = 3 + 2/3 from a controlled spherical-shell/NLS second variation.
3. lambda_chi = 4 from inner/outer pressure-cell stationarity.
4. q_phi = 1 from the one-cell exterior phase-Hessian operator.

Scope
-----
This script proves the gates inside one explicit minimal finite-cell shell model.
It should be labelled "derived within the minimal finite-cell shell model", not
unconditional microscopic QED derivation unless the model assumptions themselves
are independently justified.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import pandas as pd
import sympy as sp


def spherical_harmonic_degeneracy(l: int) -> int:
    return 2 * l + 1


def pressure_sector_count(lmax_pressure: int) -> int:
    return sum(spherical_harmonic_degeneracy(l) for l in range(lmax_pressure + 1))


def angular_average_sin2() -> sp.Expr:
    theta = sp.symbols("theta", real=True)
    numerator = sp.integrate(sp.sin(theta)**2 * sp.sin(theta), (theta, 0, sp.pi))
    denominator = sp.integrate(sp.sin(theta), (theta, 0, sp.pi))
    return sp.simplify(numerator / denominator)


def volume_second_variation_coeff() -> sp.Expr:
    eta = sp.symbols("eta")
    expr = (1 - eta)**3
    return sp.Abs(sp.expand(expr).coeff(eta, 2))


def derive(args) -> Dict[str, object]:
    L, chi, Eeff, K = sp.symbols("L chi_R E_eff K_cell", positive=True)

    Np = pressure_sector_count(args.lmax_pressure)
    Vunit = sp.Rational(4, 3) * sp.pi
    Ep0 = sp.simplify(Np * Vunit * L)

    sigma_vol = volume_second_variation_coeff()
    sigma_trans = angular_average_sin2() if args.include_transverse_average else sp.Integer(0)
    sigma = sp.simplify(sigma_vol + sigma_trans)

    A_chi = chi + sp.Integer(Np) / chi
    chi_stationary = sp.solve(sp.Eq(sp.diff(A_chi, chi), 0), chi)[0]

    eta_chi = sp.simplify(1 / (2 * chi_stationary * L))
    c2 = sp.simplify(sigma / (4 * chi_stationary**2))
    EpNLS = sp.simplify(Ep0 * (1 - c2 / L**2))

    exterior_capacity = 4 * sp.pi
    Lambda_phi = sp.simplify(exterior_capacity * K)
    q_phi = spherical_harmonic_degeneracy(0)
    Lambda_target = sp.simplify(q_phi * Eeff / 2)
    K_from_target = sp.solve(sp.Eq(Lambda_phi, Lambda_target), K)[0]

    gates = [
        {
            "gate": "N_p pressure-sector count",
            "assumption_used": f"lowest spherical pressure subspace l=0..{args.lmax_pressure}",
            "derived_value": str(Np),
            "target": "4",
            "passed": bool(Np == 4),
            "formula": "sum_{l=0}^{lmax} (2l+1)",
            "interpretation": "l=0 monopole plus l=1 dipole pressure manifold",
        },
        {
            "gate": "sigma NLS finite-shell coefficient",
            "assumption_used": "volume second variation + transverse angular average",
            "derived_value": str(sigma),
            "target": "11/3",
            "passed": bool(sp.simplify(sigma - sp.Rational(11, 3)) == 0),
            "formula": "sigma = 3 + <sin^2(theta)>_S2",
            "interpretation": "3 from spherical volume Jacobian; 2/3 from transverse NLS average",
        },
        {
            "gate": "chi_R cell-radius closure",
            "assumption_used": f"A_chi = chi_R + N_p/chi_R, N_p={Np}",
            "derived_value": str(chi_stationary),
            "target": "2",
            "passed": bool(sp.simplify(chi_stationary - 2) == 0),
            "formula": "d/dchi(chi + N_p/chi)=0 -> chi=sqrt(N_p)",
            "interpretation": "inner/outer reciprocal pressure balance",
        },
        {
            "gate": "q_phi phase-Hessian normalization",
            "assumption_used": "canonical unit exterior monopole phase mode dim H^0(S^2)=1",
            "derived_value": str(q_phi),
            "target": "1",
            "passed": bool(q_phi == 1),
            "formula": "q_phi = degeneracy(l=0) = 1",
            "interpretation": "single global U(1) phase mode; exterior capacity gives 4*pi",
        },
    ]

    all_pass = all(g["passed"] for g in gates)
    return {
        "classification": "derived_within_minimal_shell_model" if all_pass else "not_derived_in_selected_model",
        "Np": Np,
        "Ep0_over_L": sp.simplify(Ep0 / L),
        "sigma_volume": sigma_vol,
        "sigma_transverse": sigma_trans,
        "sigma": sigma,
        "chi_R": chi_stationary,
        "eta_K": eta_chi,
        "c2": c2,
        "EpNLS": EpNLS,
        "exterior_capacity": exterior_capacity,
        "Lambda_phi": Lambda_phi,
        "q_phi": q_phi,
        "K_cell_from_phase_hessian": K_from_target,
        "gates": gates,
    }


def write_latex(outdir: Path) -> None:
    tex = r"""\section{Minimal finite-cell shell derivation of the four gates}
\label{app:minimal-four-gate-derivation}

This appendix gives a compact derivation of the four coefficient gates inside a
specified minimal finite-cell shell model.  The assumptions are explicit:
the pressure manifold is the lowest spherical subspace \(l=0\oplus l=1\), the
finite-shell correction is the sum of a spherical volume second variation and a
transverse NLS angular average, the cell radius follows from a reciprocal
inner/outer pressure action, and the far-field phase is the unit exterior
monopole mode.

\paragraph{Gate 1: pressure-sector count.}
The degeneracy of spherical harmonics is \(2l+1\).  For \(l=0\oplus l=1\),
\[
  N_p=(2\cdot0+1)+(2\cdot1+1)=1+3=4.
\]
Therefore
\[
  E_p^{(0)}
  =
  N_p\frac{4\pi}{3}\mathcal L_K
  =
  \frac{16\pi}{3}\mathcal L_K .
\]

\paragraph{Gate 2: finite-shell coefficient.}
The second-order shell coefficient is
\[
  \sigma=\sigma_{\rm vol}+\sigma_{\perp}.
\]
For the spherical volume Jacobian,
\[
  (1-\eta)^3=1-3\eta+3\eta^2+O(\eta^3),
\]
so \(\sigma_{\rm vol}=3\).  For the transverse NLS shell average,
\[
  \sigma_\perp=\langle\sin^2\theta\rangle_{S^2}
  =
  \frac{\int_0^\pi \sin^2\theta\,\sin\theta\,d\theta}
       {\int_0^\pi \sin\theta\,d\theta}
  =
  \frac{2}{3}.
\]
Thus
\[
  \sigma=3+\frac{2}{3}=\frac{11}{3}.
\]
With
\[
  \eta_K=\frac{1}{2\chi_R\mathcal L_K},
  \qquad
  \chi_R=2,
\]
one obtains
\[
  \sigma\eta_K^2
  =
  \frac{11}{3}\frac{1}{16\mathcal L_K^2}
  =
  \frac{11}{48\mathcal L_K^2}.
\]
Hence
\[
  E_p^{\rm NLS}
  =
  \frac{16\pi}{3}\mathcal L_K
  \left(
  1-\frac{11}{48\mathcal L_K^2}
  \right).
\]

\paragraph{Gate 3: cell-radius closure.}
Let
\[
  A_\chi(\chi_R)=\chi_R+\frac{N_p}{\chi_R}.
\]
Then
\[
  \frac{dA_\chi}{d\chi_R}
  =
  1-\frac{N_p}{\chi_R^2},
\]
so stationarity gives
\[
  \chi_R=\sqrt{N_p}=2.
\]

\paragraph{Gate 4: one-cell phase Hessian.}
For the exterior monopole phase \(u(r)=\phi/r\),
\[
  \int_{r\ge1}|\nabla u|^2\,d^3x=4\pi\phi^2.
\]
Thus
\[
  \Lambda_\phi=4\pi\mathcal K_{\rm cell}.
\]
The canonical \(U(1)\) exterior phase mode is the \(l=0\) mode on \(S^2\), whose
degeneracy is
\[
  q_\phi=2\cdot0+1=1.
\]
The one-cell phase Hessian is therefore
\[
  \Lambda_\phi=\frac{q_\phi E_{\rm eff}}{2}=\frac{E_{\rm eff}}{2},
\]
and hence
\[
  \mathcal K_{\rm cell}
  =
  \frac{\Lambda_\phi}{4\pi}
  =
  \frac{E_{\rm eff}}{8\pi}.
\]

Within these four explicit assumptions, the fine-structure-scale chain is
derived inside the minimal finite-cell shell model.  The remaining physical
task is to justify the model assumptions themselves from the underlying field
theory rather than from coefficient matching.
"""
    (outdir / "minimal_four_gate_derivation_appendix.tex").write_text(tex, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lmax-pressure", type=int, default=1)
    parser.add_argument("--include-transverse-average", action="store_true", default=True)
    parser.add_argument("--outdir", default="outputs_four_gate_minimal_model")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    result = derive(args)
    gates = result.pop("gates")

    pd.DataFrame(gates).to_csv(outdir / "four_gate_proof_table.csv", index=False)

    rows = []
    for k, v in result.items():
        rows.append({
            "name": k,
            "value": str(v),
            "latex": sp.latex(v) if isinstance(v, sp.Basic) else str(v),
        })
    pd.DataFrame(rows).to_csv(outdir / "four_gate_symbolic_results.csv", index=False)

    report = [
        "# Four-gate minimal finite-cell shell derivation",
        "",
        f"Classification: **{result['classification']}**",
        "",
    ]
    for g in gates:
        report += [
            f"## {g['gate']}",
            f"- Assumption used: {g['assumption_used']}",
            f"- Formula: `{g['formula']}`",
            f"- Derived value: `{g['derived_value']}`",
            f"- Target: `{g['target']}`",
            f"- Passed: `{g['passed']}`",
            f"- Interpretation: {g['interpretation']}",
            "",
        ]
    (outdir / "four_gate_proof_report.md").write_text("\n".join(report), encoding="utf-8")

    write_latex(outdir)

    print(pd.DataFrame(gates).to_string(index=False))
    print(f"\nClassification: {result['classification']}")
    print(f"Wrote {outdir/'four_gate_proof_table.csv'}")
    print(f"Wrote {outdir/'four_gate_symbolic_results.csv'}")
    print(f"Wrote {outdir/'four_gate_proof_report.md'}")
    print(f"Wrote {outdir/'minimal_four_gate_derivation_appendix.tex'}")


if __name__ == "__main__":
    main()

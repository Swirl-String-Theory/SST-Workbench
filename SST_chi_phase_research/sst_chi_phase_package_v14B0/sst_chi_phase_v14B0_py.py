"""
sst_chi_phase_v14B0_py.py

Track B v14B.0: internal A=B=C gate for the GP/NLSE core-envelope reduction.

This module does not assert that SST has already locked the single-isotropic-core
modulus as a canon axiom. It verifies the conditional theorem:

    single isotropic complex core-envelope stiffness
        => A_grad = B_phase = C_depletion
        => GP/NLSE unit vortex ODE used in v10B.1-v12B.0.

Author: generated for SST/CANON audit workflow.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import math


@dataclass(frozen=True)
class CoefficientCase:
    name: str
    A_grad: float
    B_phase: float
    C_depletion: float
    n: int = 1
    note: str = ""


@dataclass(frozen=True)
class GateResult:
    name: str
    A_grad: float
    B_phase: float
    C_depletion: float
    n: int
    B_over_A: float
    C_over_A: float
    phase_coeff: float
    depletion_coeff: float
    energy_potential_prefactor: float
    ode_matches_unit_gp: bool
    abc_equal: bool
    note: str


def euler_lagrange_reduced_coefficients(A_grad: float, B_phase: float, C_depletion: float, n: int = 1) -> Dict[str, float]:
    """Return coefficients in

        F'' + F'/r - phase_coeff * F/r^2 + depletion_coeff * F(1-F^2) = 0.

    For the radial Lagrangian density

        L_r = A F'^2 r + B n^2 F^2/r + (C/2)(F^2-1)^2 r.

    Variation gives phase_coeff=(B/A)n^2 and depletion_coeff=C/A.
    """
    if A_grad <= 0:
        raise ValueError("A_grad must be positive")
    return {
        "B_over_A": B_phase / A_grad,
        "C_over_A": C_depletion / A_grad,
        "phase_coeff": (B_phase / A_grad) * (n ** 2),
        "depletion_coeff": C_depletion / A_grad,
        "energy_potential_prefactor": 0.5 * C_depletion,
    }


def analyze_case(case: CoefficientCase, tol: float = 1e-12) -> GateResult:
    coeff = euler_lagrange_reduced_coefficients(case.A_grad, case.B_phase, case.C_depletion, case.n)
    abc_equal = (
        abs(case.A_grad - case.B_phase) <= tol * max(1.0, abs(case.A_grad), abs(case.B_phase))
        and abs(case.A_grad - case.C_depletion) <= tol * max(1.0, abs(case.A_grad), abs(case.C_depletion))
    )
    ode_matches = (
        case.n == 1
        and abs(coeff["phase_coeff"] - 1.0) <= 1e-10
        and abs(coeff["depletion_coeff"] - 1.0) <= 1e-10
    )
    return GateResult(
        name=case.name,
        A_grad=case.A_grad,
        B_phase=case.B_phase,
        C_depletion=case.C_depletion,
        n=case.n,
        B_over_A=coeff["B_over_A"],
        C_over_A=coeff["C_over_A"],
        phase_coeff=coeff["phase_coeff"],
        depletion_coeff=coeff["depletion_coeff"],
        energy_potential_prefactor=coeff["energy_potential_prefactor"],
        ode_matches_unit_gp=ode_matches,
        abc_equal=abc_equal,
        note=case.note,
    )


def canonical_cases() -> List[CoefficientCase]:
    return [
        CoefficientCase(
            name="single_isotropic_core_modulus",
            A_grad=1.0,
            B_phase=1.0,
            C_depletion=1.0,
            n=1,
            note="PASS: single isotropic envelope stiffness; gives v10B.1 ODE and energy prefactor 1/2.",
        ),
        CoefficientCase(
            name="v10B0_old_potential_prefactor_quarter",
            A_grad=1.0,
            B_phase=1.0,
            C_depletion=0.5,
            n=1,
            note="FAIL: energy has (F^2-1)^2 r / 4, so C/A=1/2; inconsistent with solved unit GP ODE.",
        ),
        CoefficientCase(
            name="anisotropic_phase_stiffness",
            A_grad=1.0,
            B_phase=1.08,
            C_depletion=1.0,
            n=1,
            note="FAIL: phase stiffness differs; vortex winding term coefficient changes.",
        ),
        CoefficientCase(
            name="anisotropic_depletion_stiffness",
            A_grad=1.0,
            B_phase=1.0,
            C_depletion=0.92,
            n=1,
            note="FAIL: depletion stiffness differs; healing-tail and ring constant change.",
        ),
        CoefficientCase(
            name="higher_winding_same_modulus",
            A_grad=1.0,
            B_phase=1.0,
            C_depletion=1.0,
            n=2,
            note="Not the unit electron-sector vortex: A=B=C but n=2 gives phase coefficient 4.",
        ),
    ]


def dimensionless_reduction_table(kappa: float = 1.0, xi: float = 1.0) -> Dict[str, float]:
    """Coefficients after reducing

        E = kappa ∫ [ |∇Ψ|² + (1/(2 ξ²))(1-|Ψ|²)² ] d²x,
        Ψ = F(ρ) exp(i n θ), x=ρ/ξ.

    Up to a common prefactor 2π kappa, the dimensionless radial coefficients are
        A=B=C=1.
    """
    if kappa <= 0 or xi <= 0:
        raise ValueError("kappa and xi must be positive")
    # Physical radial energy before x=rho/xi:
    # kappa [F_rho^2 + n^2 F^2/rho^2 + (1/(2xi^2))(F^2-1)^2] rho d rho.
    # Substitute rho=xi*x, d rho=xi dx, F_rho=(1/xi)F_x.
    # Common factor kappa; all three dimensionless coefficients equal 1.
    return {
        "kappa": kappa,
        "xi": xi,
        "A_grad_dimensionless": 1.0,
        "B_phase_dimensionless": 1.0,
        "C_depletion_dimensionless": 1.0,
        "potential_prefactor_dimensionless": 0.5,
    }


def proximity_metrics(alpha_gp_inf: float = 1.619350923, legacy_nls: float = 1.61) -> Dict[str, float]:
    phi = (1 + math.sqrt(5)) / 2
    return {
        "alpha_gp_inf": alpha_gp_inf,
        "legacy_nls_alpha": legacy_nls,
        "delta_to_legacy_nls": alpha_gp_inf - legacy_nls,
        "golden_ratio_phi": phi,
        "delta_to_phi": alpha_gp_inf - phi,
    }

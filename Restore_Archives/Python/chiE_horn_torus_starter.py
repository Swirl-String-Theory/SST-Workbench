#!/usr/bin/env python3
"""
SST research-track starter: horn-torus loop energy factor chi_E.

Purpose
-------
Compute the dimensionless closed-loop energy factor without using m_e, hbar,
alpha, r_c, or lambda_C as inputs.

Two normalizations are reported:
    Xi_E  = E_loop / (rho_sat * Gamma0^2 * a0)
    chi_E = E_loop / (rho_sat * v0^2 * a0^3) = 4*pi^2*Xi_E
where v0 = Gamma0/(2*pi*a0).

The parameter-counting relation in the SST research-track audit uses chi_E.
The canon-calibrated target would be chi_E = 2*pi, equivalently Xi_E=1/(2*pi).

This file is deliberately a diagnostic, not a proof. The regularized filament
kernel and the thin-ring formula are model choices; if chi_E=2*pi requires tuning
lambda=R/a0, a core constant, or the regularization, the result is calibrated.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class FluidPrimitiveParams:
    rho_sat: float      # kg m^-3
    Gamma0: float       # m^2 s^-1
    P_vac: float        # Pa


def cavity_radius(params: FluidPrimitiveParams) -> float:
    """a0 = Gamma0/(2*pi) * sqrt(rho_sat/(2 P_vac))."""
    if params.rho_sat <= 0 or params.Gamma0 <= 0 or params.P_vac <= 0:
        raise ValueError("rho_sat, Gamma0 and P_vac must be positive")
    return params.Gamma0 / (2.0 * math.pi) * math.sqrt(params.rho_sat / (2.0 * params.P_vac))


def boundary_speed(Gamma0: float, a0: float) -> float:
    """v0 = Gamma0/(2*pi*a0)."""
    if Gamma0 <= 0 or a0 <= 0:
        raise ValueError("Gamma0 and a0 must be positive")
    return Gamma0 / (2.0 * math.pi * a0)


def hollow_core_line_energy(a: float, R_outer: float, params: FluidPrimitiveParams) -> float:
    """Straight hollow-core vortex energy per unit length.

    E'(a) = rho Gamma^2/(4*pi) ln(R/a) + P_vac*pi*a^2.
    """
    if not (0.0 < a < R_outer):
        raise ValueError("Require 0 < a < R_outer")
    return (
        params.rho_sat * params.Gamma0**2 / (4.0 * math.pi) * math.log(R_outer / a)
        + params.P_vac * math.pi * a * a
    )


def hollow_core_second_derivative_at_min(params: FluidPrimitiveParams) -> float:
    """d^2E'/da^2 at the variational hollow-core minimum.

    Using equilibrium, this is 4*pi*P_vac. Units: J m^-3 = Pa.
    """
    return 4.0 * math.pi * params.P_vac


def xi_E_thin_ring(lambda_R: float, C_core: float = 1.75, include_cavity: bool = True) -> float:
    """Thin-ring asymptotic energy in circulation normalization.

    Xi_E = E/(rho Gamma^2 a0) ~= 0.5*lambda*(ln(8 lambda)-C_core).
    Optional cavity work adds lambda/4 using the hollow-core equilibrium P_vac.

    Valid only for lambda=R/a0 >> 1; using it near lambda=O(1) is diagnostic.
    """
    if lambda_R <= 0:
        raise ValueError("lambda_R must be positive")
    xi = 0.5 * lambda_R * (math.log(8.0 * lambda_R) - C_core)
    if include_cavity:
        xi += 0.25 * lambda_R
    return xi


def xi_E_regularized_circle(
    lambda_R: float,
    n: int = 16384,
    eps: float = 1.0,
    include_cavity: bool = True,
) -> float:
    """Regularized circular-filament double-integral diagnostic.

    For x(phi)=R(cos phi, sin phi,0), use
        E = rho Gamma^2/(8*pi) double_int dl.dl'/sqrt(|x-x'|^2+(eps*a0)^2).

    The dimensionless result is
        Xi_E = lambda^2/4 int_0^{2pi} cos(theta)
               / sqrt(4 lambda^2 sin^2(theta/2)+eps^2) dtheta.

    Optional cavity work adds lambda/4 using the hollow-core equilibrium P_vac.
    """
    if lambda_R <= 0 or eps <= 0 or n < 16:
        raise ValueError("Require lambda_R>0, eps>0, n>=16")

    # Midpoint rule avoids sampling theta=0 specially; integrand is regular for eps>0.
    h = 2.0 * math.pi / n
    total = 0.0
    for k in range(n):
        theta = (k + 0.5) * h
        denom = math.sqrt(4.0 * lambda_R * lambda_R * math.sin(theta / 2.0) ** 2 + eps * eps)
        total += math.cos(theta) / denom
    integral = h * total
    xi = (lambda_R * lambda_R / 4.0) * integral
    if include_cavity:
        xi += 0.25 * lambda_R
    return xi


def chi_from_xi(xi: float) -> float:
    """chi_E = E/(rho v0^2 a0^3) = 4*pi^2*Xi_E."""
    return 4.0 * math.pi * math.pi * xi


def find_lambda_for_target(
    target_chi: float = 2.0 * math.pi,
    lo: float = 1.0,
    hi: float = 50.0,
    model: str = "regularized",
    n: int = 16384,
    eps: float = 1.0,
    C_core: float = 1.75,
) -> Optional[float]:
    """Bisection root for chi_E(lambda)=target, if bracketed."""
    def f(lam: float) -> float:
        if model == "regularized":
            return chi_from_xi(xi_E_regularized_circle(lam, n=n, eps=eps)) - target_chi
        if model == "thin":
            return chi_from_xi(xi_E_thin_ring(lam, C_core=C_core)) - target_chi
        raise ValueError("model must be 'regularized' or 'thin'")

    flo, fhi = f(lo), f(hi)
    if flo == 0.0:
        return lo
    if fhi == 0.0:
        return hi
    if flo * fhi > 0.0:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0.0:
            hi = mid
            fhi = fm
        else:
            lo = mid
            flo = fm
    return 0.5 * (lo + hi)


def table(lambdas: Iterable[float], n: int, eps: float, C_core: float) -> str:
    lines = [
        "lambda    Xi_reg       chi_reg      Xi_thin      chi_thin",
        "-----------------------------------------------------------",
    ]
    for lam in lambdas:
        xi_r = xi_E_regularized_circle(lam, n=n, eps=eps)
        xi_t = xi_E_thin_ring(lam, C_core=C_core)
        lines.append(f"{lam:6.3f}  {xi_r:10.6g}  {chi_from_xi(xi_r):10.6g}  {xi_t:10.6g}  {chi_from_xi(xi_t):10.6g}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=16384, help="quadrature panels")
    parser.add_argument("--eps", type=float, default=1.0, help="regularization radius / a0")
    parser.add_argument("--C-core", type=float, default=1.75, help="thin-ring core constant")
    parser.add_argument("--lambda-min", type=float, default=0.2)
    parser.add_argument("--lambda-max", type=float, default=8.0)
    parser.add_argument("--lambda-count", type=int, default=14)
    args = parser.parse_args()

    target = 2.0 * math.pi
    print("SST horn-torus chi_E diagnostic")
    print("target chi_E = 2*pi =", target)
    print("target Xi_E = 1/(2*pi) =", 1.0 / (2.0 * math.pi))
    print()

    # Include lambda=1 explicitly because this is the non-self-intersecting horn-torus threshold.
    lambdas = [args.lambda_min + i * (args.lambda_max - args.lambda_min) / max(1, args.lambda_count - 1) for i in range(args.lambda_count)]
    if 1.0 not in lambdas:
        lambdas.append(1.0)
    lambdas = sorted(set(round(x, 12) for x in lambdas))
    print(table(lambdas, n=args.n, eps=args.eps, C_core=args.C_core))
    print()

    for model in ["regularized", "thin"]:
        root_ge_1 = find_lambda_for_target(target, lo=1.0, hi=args.lambda_max, model=model, n=args.n, eps=args.eps, C_core=args.C_core)
        root_loose = find_lambda_for_target(target, lo=0.05, hi=args.lambda_max, model=model, n=args.n, eps=args.eps, C_core=args.C_core)
        print(f"{model}: root with lambda>=1 bracket = {root_ge_1}")
        print(f"{model}: root with lambda>=0.05 bracket = {root_loose}")
    print()
    print("Interpretation guard:")
    print("  If chi_E=2*pi occurs only for lambda<1, a tuned C_core, or a tuned eps,")
    print("  it is not a horn-torus derivation. It is a calibrated model choice.")


if __name__ == "__main__":
    main()

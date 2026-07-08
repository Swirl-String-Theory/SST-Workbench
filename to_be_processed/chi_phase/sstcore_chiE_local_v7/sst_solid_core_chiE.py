from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

PI = math.pi
TARGET_CHI_E = 2.0 * PI
TARGET_XI_E = 1.0 / (2.0 * PI)


@dataclass(frozen=True)
class SolidCoreParams:
    """Solid constant-density Rankine-core ring parameters.

    This is a primitive-safe, dimensionless Step-2 diagnostic.  It does not use
    m_e, hbar, alpha_EM, r_c, or lambda_C.  The default core constant is the
    classic thin-ring value for a solid core with constant volume:

        alpha_E = 7/4.

    The formulas are asymptotic for R/a0 >> 1.  Evaluating them at lambda=1 is
    deliberately labelled as a horn-limit extrapolation, not a theorem.
    """

    lambda_: float = 1.0        # R/a0, dimensionless; embedded torus guard lambda>=1
    alpha_E: float = 1.75       # energy constant; solid core + constant volume = 7/4
    beta_V: float = 0.25        # speed constant; solid core + constant volume = 1/4
    rho_sat: float = 1.0        # kg m^-3, only for dimensional E_loop reporting
    Gamma0: float = 1.0         # m^2 s^-1, only for dimensional E_loop reporting
    a0: float = 1.0             # m, only for dimensional E_loop reporting

    @property
    def R(self) -> float:
        return self.lambda_ * self.a0

    @property
    def v0(self) -> float:
        return self.Gamma0 / (2.0 * PI * self.a0)


@dataclass(frozen=True)
class SolidCoreResult:
    lambda_: float
    alpha_E: float
    beta_V: float
    R: float
    v0: float

    Xi_internal_rankine: float
    Xi_external_asymptotic: float
    Xi_total: float

    chi_internal_rankine: float
    chi_external_asymptotic: float
    chi_E: float
    target_residual: float

    alpha_required_for_2pi: float
    beta_speed_factor: float
    speed_factor_positive: bool
    E_loop: float

    target_chi_E: float = TARGET_CHI_E
    target_xi_E: float = TARGET_XI_E
    model: str = "solid_core_constant_density_rankine_thin_ring"
    status: str = "RESEARCH-TRACK / ASYMPTOTIC CHECK / NOT CANONIZED"


def require_positive(name: str, value: float) -> None:
    if not (value > 0.0) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite and positive, got {value!r}")


def require_lambda(lambda_: float) -> None:
    require_positive("lambda_", lambda_)
    if lambda_ < 1.0:
        raise ValueError("embedded torus requires lambda_=R/a0 >= 1")


def chi_from_xi(xi: float) -> float:
    return 4.0 * PI * PI * xi


def xi_internal_rankine(lambda_: float) -> float:
    """Internal kinetic energy of a constant-density Rankine tube.

    Local profile in cross-section:
        v_theta(s)=Gamma0*s/(2*pi*a0^2), 0<=s<=a0.

    Integrated over a toroidal tube gives
        E_int = rho_sat Gamma0^2 R / 8,
    hence
        Xi_int = E_int/(rho_sat Gamma0^2 a0) = lambda/8.
    """
    require_lambda(lambda_)
    return 0.125 * lambda_


def xi_total_solid_thin_ring(lambda_: float, alpha_E: float = 1.75) -> float:
    """Thin-ring asymptotic total kinetic energy for solid core.

    E ~= 1/2 rho Gamma^2 R [log(8R/a)-alpha_E]
    Xi = E/(rho Gamma^2 a0) = 1/2 lambda [log(8 lambda)-alpha_E].

    Default alpha_E=7/4 corresponds to solid core + constant volume.
    """
    require_lambda(lambda_)
    if not math.isfinite(alpha_E):
        raise ValueError("alpha_E must be finite")
    return 0.5 * lambda_ * (math.log(8.0 * lambda_) - alpha_E)


def xi_external_solid_asymptotic(lambda_: float, alpha_E: float = 1.75) -> float:
    """External asymptotic contribution inferred by subtracting Rankine core energy."""
    return xi_total_solid_thin_ring(lambda_, alpha_E) - xi_internal_rankine(lambda_)


def alpha_required_for_target(lambda_: float, target_chi_E: float = TARGET_CHI_E) -> float:
    """Energy constant alpha_E required to force chi_E=target at fixed lambda.

    From target_Xi = 1/2 lambda [log(8 lambda)-alpha_E].
    """
    require_lambda(lambda_)
    target_xi = target_chi_E / (4.0 * PI * PI)
    return math.log(8.0 * lambda_) - 2.0 * target_xi / lambda_


def speed_factor(lambda_: float, beta_V: float = 0.25) -> float:
    """Thin-ring translational speed bracket log(8lambda)-beta_V."""
    require_lambda(lambda_)
    if not math.isfinite(beta_V):
        raise ValueError("beta_V must be finite")
    return math.log(8.0 * lambda_) - beta_V


def evaluate_solid_core(params: SolidCoreParams) -> SolidCoreResult:
    require_lambda(params.lambda_)
    require_positive("rho_sat", params.rho_sat)
    require_positive("Gamma0", params.Gamma0)
    require_positive("a0", params.a0)
    if not math.isfinite(params.alpha_E):
        raise ValueError("alpha_E must be finite")
    if not math.isfinite(params.beta_V):
        raise ValueError("beta_V must be finite")

    xi_int = xi_internal_rankine(params.lambda_)
    xi_total = xi_total_solid_thin_ring(params.lambda_, params.alpha_E)
    xi_ext = xi_total - xi_int

    chi_int = chi_from_xi(xi_int)
    chi_ext = chi_from_xi(xi_ext)
    chi_total = chi_from_xi(xi_total)
    sf = speed_factor(params.lambda_, params.beta_V)
    E_loop = xi_total * params.rho_sat * params.Gamma0 * params.Gamma0 * params.a0

    return SolidCoreResult(
        lambda_=float(params.lambda_),
        alpha_E=float(params.alpha_E),
        beta_V=float(params.beta_V),
        R=float(params.R),
        v0=float(params.v0),
        Xi_internal_rankine=float(xi_int),
        Xi_external_asymptotic=float(xi_ext),
        Xi_total=float(xi_total),
        chi_internal_rankine=float(chi_int),
        chi_external_asymptotic=float(chi_ext),
        chi_E=float(chi_total),
        target_residual=float((chi_total - TARGET_CHI_E) / TARGET_CHI_E),
        alpha_required_for_2pi=float(alpha_required_for_target(params.lambda_)),
        beta_speed_factor=float(sf),
        speed_factor_positive=bool(sf > 0.0),
        E_loop=float(E_loop),
    )


def scan_lambda(
    lambda_min: float,
    lambda_max: float,
    lambda_count: int,
    base: SolidCoreParams,
) -> List[SolidCoreResult]:
    require_lambda(lambda_min)
    require_lambda(lambda_max)
    if lambda_max < lambda_min:
        raise ValueError("lambda_max must be >= lambda_min")
    if lambda_count < 2:
        raise ValueError("lambda_count must be >= 2")
    return [
        evaluate_solid_core(SolidCoreParams(
            lambda_=float(lam),
            alpha_E=base.alpha_E,
            beta_V=base.beta_V,
            rho_sat=base.rho_sat,
            Gamma0=base.Gamma0,
            a0=base.a0,
        ))
        for lam in np.linspace(lambda_min, lambda_max, lambda_count)
    ]


def scan_alpha(
    alpha_min: float,
    alpha_max: float,
    alpha_count: int,
    base: SolidCoreParams,
) -> List[SolidCoreResult]:
    if alpha_count < 2:
        raise ValueError("alpha_count must be >= 2")
    if alpha_max < alpha_min:
        raise ValueError("alpha_max must be >= alpha_min")
    return [
        evaluate_solid_core(SolidCoreParams(
            lambda_=base.lambda_,
            alpha_E=float(alpha),
            beta_V=base.beta_V,
            rho_sat=base.rho_sat,
            Gamma0=base.Gamma0,
            a0=base.a0,
        ))
        for alpha in np.linspace(alpha_min, alpha_max, alpha_count)
    ]


def result_to_dict(result: SolidCoreResult) -> Dict[str, Any]:
    return asdict(result)


def write_csv(path: str | Path, rows: Iterable[SolidCoreResult]) -> None:
    rows_list = [result_to_dict(r) for r in rows]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows_list:
        return
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_list[0].keys()))
        writer.writeheader()
        writer.writerows(rows_list)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

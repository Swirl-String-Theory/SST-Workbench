from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

PI = math.pi
TARGET_CHI_E = 2.0 * PI
TARGET_XI_E = 1.0 / (2.0 * PI)


@dataclass(frozen=True)
class HornTorusParams:
    """Dimensionless horn-torus energy parameters.

    The solver is intentionally primitive-only.  The dimensionless loop geometry is
    R/a0 = lambda_.  No electron-normalized constants are used by this module.
    """

    lambda_: float = 1.0
    epsilon: float = 1.0
    quadrature_n: int = 32768
    core_constant: float = 1.75


@dataclass(frozen=True)
class HornTorusResult:
    lambda_: float
    epsilon: float
    quadrature_n: int
    kernel: str
    xi_filament: float
    xi_cavitation: float
    xi_total_hollow: float
    chi_K: float
    chi_cavitation: float
    chi_E_hollow: float
    target_chi_E: float
    target_xi_E: float
    residual_kinetic_to_2pi: float
    residual_total_to_2pi: float
    status: str


@dataclass(frozen=True)
class PrimitiveScales:
    """Optional dimensional primitive scales for reporting only."""

    rho_sat: float
    Gamma0: float
    P_vac: float
    mu_vac: Optional[float] = None

    @property
    def a0(self) -> float:
        return self.Gamma0 / (2.0 * PI) * math.sqrt(self.rho_sat / (2.0 * self.P_vac))

    @property
    def v0(self) -> float:
        return self.Gamma0 / (2.0 * PI * self.a0)

    @property
    def c_T(self) -> Optional[float]:
        if self.mu_vac is None:
            return None
        return math.sqrt(self.mu_vac / self.rho_sat)

    @property
    def alpha_sst_0(self) -> Optional[float]:
        c_T = self.c_T
        if c_T is None:
            return None
        return 2.0 * self.v0 / c_T


def require_positive(name: str, value: float) -> None:
    if not (value > 0.0) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite and positive, got {value!r}")


def require_lambda(lambda_: float, *, allow_horn: bool = True) -> None:
    require_positive("lambda_", lambda_)
    if allow_horn:
        if lambda_ < 1.0:
            raise ValueError("embedded hollow torus requires lambda_ = R/a0 >= 1")
    else:
        if lambda_ <= 1.0:
            raise ValueError("smooth torus limit requires lambda_ > 1; horn is lambda_->1+")


def v0_from_gamma_a0(Gamma0: float, a0: float) -> float:
    require_positive("Gamma0", Gamma0)
    require_positive("a0", a0)
    return Gamma0 / (2.0 * PI * a0)


def p_vac_from_variational_a0(rho_sat: float, Gamma0: float, a0: float) -> float:
    require_positive("rho_sat", rho_sat)
    require_positive("Gamma0", Gamma0)
    require_positive("a0", a0)
    return rho_sat * Gamma0 * Gamma0 / (8.0 * PI * PI * a0 * a0)


def xi_cavitation(lambda_: float) -> float:
    """Cavitation work in Xi normalization E/(rho Gamma^2 a0)."""
    require_lambda(lambda_)
    return 0.25 * lambda_


def chi_from_xi(xi: float) -> float:
    return 4.0 * PI * PI * xi


def xi_thin_ring(lambda_: float, core_constant: float = 1.75) -> float:
    """Thin-ring diagnostic, not valid as a horn proof for lambda_=O(1)."""
    require_lambda(lambda_)
    if not math.isfinite(core_constant):
        raise ValueError("core_constant must be finite")
    return 0.5 * lambda_ * (math.log(8.0 * lambda_) - core_constant)


def xi_regularized_circular_filament(
    lambda_: float,
    epsilon: float = 1.0,
    quadrature_n: int = 32768,
    cpp_mod: Any = None,
) -> float:
    """Dimensionless softened Neumann energy of a circular vortex loop.

    Returns Xi_filament = E_filament/(rho_sat Gamma0^2 a0).  The softening
    length is epsilon*a0.  If cpp_mod exposes horn_xi_regularized_filament,
    that compiled implementation is used.
    """
    require_lambda(lambda_)
    require_positive("epsilon", epsilon)
    if quadrature_n < 128:
        raise ValueError("quadrature_n must be >= 128")
    if cpp_mod is not None and hasattr(cpp_mod, "horn_xi_regularized_filament"):
        return float(cpp_mod.horn_xi_regularized_filament(float(lambda_), float(epsilon), int(quadrature_n)))

    theta = (np.arange(quadrature_n, dtype=np.float64) + 0.5) * (2.0 * PI / quadrature_n)
    denom = np.sqrt(4.0 * lambda_ * lambda_ * np.sin(0.5 * theta) ** 2 + epsilon * epsilon)
    integral = float(np.sum(np.cos(theta) / denom) * (2.0 * PI / quadrature_n))
    return 0.25 * lambda_ * lambda_ * integral


def evaluate_horn_torus(
    params: HornTorusParams,
    kernel: str = "regularized",
    cpp_mod: Any = None,
) -> HornTorusResult:
    """Evaluate kinetic-only and hollow-total horn-torus energy factors."""
    require_lambda(params.lambda_)
    kernel_l = kernel.lower().strip()
    if kernel_l in {"regularized", "softened", "neumann"}:
        xi_fil = xi_regularized_circular_filament(
            params.lambda_, params.epsilon, params.quadrature_n, cpp_mod=cpp_mod
        )
        kernel_name = "regularized"
    elif kernel_l in {"thin", "thin_ring", "asymptotic"}:
        xi_fil = xi_thin_ring(params.lambda_, params.core_constant)
        kernel_name = "thin_ring_asymptotic"
    else:
        raise ValueError(f"Unknown kernel {kernel!r}")

    xi_cav = xi_cavitation(params.lambda_)
    xi_total = xi_fil + xi_cav
    chi_K = chi_from_xi(xi_fil)
    chi_cav = chi_from_xi(xi_cav)
    chi_E = chi_from_xi(xi_total)

    return HornTorusResult(
        lambda_=float(params.lambda_),
        epsilon=float(params.epsilon),
        quadrature_n=int(params.quadrature_n),
        kernel=kernel_name,
        xi_filament=float(xi_fil),
        xi_cavitation=float(xi_cav),
        xi_total_hollow=float(xi_total),
        chi_K=float(chi_K),
        chi_cavitation=float(chi_cav),
        chi_E_hollow=float(chi_E),
        target_chi_E=TARGET_CHI_E,
        target_xi_E=TARGET_XI_E,
        residual_kinetic_to_2pi=float((chi_K - TARGET_CHI_E) / TARGET_CHI_E),
        residual_total_to_2pi=float((chi_E - TARGET_CHI_E) / TARGET_CHI_E),
        status=(
            "RESEARCH-TRACK diagnostic: regularized/thin kernel is not a proof of "
            "the resolved hollow-core Dirichlet problem."
        ),
    )


def scan_lambda(
    lambda_min: float,
    lambda_max: float,
    lambda_count: int,
    base: HornTorusParams,
    kernel: str = "regularized",
    cpp_mod: Any = None,
) -> List[HornTorusResult]:
    require_lambda(lambda_min)
    require_lambda(lambda_max)
    if lambda_max < lambda_min:
        raise ValueError("lambda_max must be >= lambda_min")
    if lambda_count < 2:
        raise ValueError("lambda_count must be >= 2")
    values = np.linspace(lambda_min, lambda_max, lambda_count)
    rows: List[HornTorusResult] = []
    for lam in values:
        p = HornTorusParams(
            lambda_=float(lam),
            epsilon=base.epsilon,
            quadrature_n=base.quadrature_n,
            core_constant=base.core_constant,
        )
        rows.append(evaluate_horn_torus(p, kernel=kernel, cpp_mod=cpp_mod))
    return rows


def result_to_dict(result: HornTorusResult) -> Dict[str, Any]:
    return asdict(result)


def write_csv(path: str | Path, rows: Iterable[HornTorusResult]) -> None:
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


def circular_loop_points(lambda_: float = 1.0, n: int = 512) -> np.ndarray:
    """Return a dimensionless circular centerline with radius lambda_ in a0 units."""
    require_lambda(lambda_)
    if n < 8:
        raise ValueError("n must be >= 8")
    t = np.linspace(0.0, 2.0 * PI, n, endpoint=False)
    return np.column_stack([lambda_ * np.cos(t), lambda_ * np.sin(t), np.zeros_like(t)])


def general_polyline_xi_filament(points_dim_a0: np.ndarray, epsilon: float = 1.0, cpp_mod: Any = None) -> float:
    """Regularized Neumann energy for any closed dimensionless polyline.

    `points_dim_a0` must be in units of a0, and the return value is Xi_filament.
    """
    from sst_trefoil_biot_py import bs_energy_dimensionless

    return float(bs_energy_dimensionless(points_dim_a0, epsilon, mode="regularized", cpp_mod=cpp_mod))

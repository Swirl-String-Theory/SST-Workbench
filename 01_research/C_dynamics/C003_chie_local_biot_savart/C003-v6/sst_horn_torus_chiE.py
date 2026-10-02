from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

PI = math.pi
TARGET_CHI_E = 2.0 * PI
TARGET_XI_E = 1.0 / (2.0 * PI)


class HornTorusKernel(str, Enum):
    """Python-side mirror of the C++ enum class HornTorusKernel."""

    THIN_RING_ASYMPTOTIC = "thin_ring_asymptotic"
    REGULARIZED_CIRCULAR_FILAMENT = "regularized_circular_filament"

    @classmethod
    def from_any(cls, value: str | "HornTorusKernel") -> "HornTorusKernel":
        if isinstance(value, cls):
            return value
        v = str(value).lower().strip()
        if v in {"thin", "thin_ring", "thin_ring_asymptotic", "asymptotic"}:
            return cls.THIN_RING_ASYMPTOTIC
        if v in {"regularized", "regularised", "softened", "neumann", "regularized_circular_filament"}:
            return cls.REGULARIZED_CIRCULAR_FILAMENT
        raise ValueError(f"Unknown horn-torus kernel {value!r}")


class EnergyMassMode(str, Enum):
    """Mass-energy interpretation switch for the horn-torus diagnostic.

    KINETIC_ONLY:
        Inertial mass counts only the exterior kinetic Dirichlet energy.

    KINETIC_PLUS_CAVITY:
        Inertial mass counts exterior kinetic energy plus positive cavitation work.
        This is the v4 default and the strict hollow-core total.

    VACUUM_SUBTRACTED:
        Compute the hollow total but explicitly subtract P_vac V_cav again.  Numerically
        this equals kinetic-only, but it records the subtraction as Xi_renormalization.

    TARGET_RENORMALIZED:
        Add exactly the renormalization required to force chi_E=2*pi.  This is not a
        derivation; it is a diagnostic that reports how large the calibrated subtraction
        would need to be.
    """

    KINETIC_ONLY = "kinetic_only"
    KINETIC_PLUS_CAVITY = "kinetic_plus_cavity"
    VACUUM_SUBTRACTED = "vacuum_subtracted"
    TARGET_RENORMALIZED = "target_renormalized"

    @classmethod
    def from_any(cls, value: str | "EnergyMassMode") -> "EnergyMassMode":
        if isinstance(value, cls):
            return value
        v = str(value).lower().strip().replace("-", "_")
        aliases = {
            "kinetic": cls.KINETIC_ONLY,
            "kinetic_only": cls.KINETIC_ONLY,
            "k": cls.KINETIC_ONLY,
            "hollow": cls.KINETIC_PLUS_CAVITY,
            "total": cls.KINETIC_PLUS_CAVITY,
            "kinetic_plus_cavity": cls.KINETIC_PLUS_CAVITY,
            "kinetic+cavity": cls.KINETIC_PLUS_CAVITY,
            "cavity": cls.KINETIC_PLUS_CAVITY,
            "vacuum_subtracted": cls.VACUUM_SUBTRACTED,
            "vacuum_subtraction": cls.VACUUM_SUBTRACTED,
            "excess_relative_to_vacuum": cls.VACUUM_SUBTRACTED,
            "excess": cls.VACUUM_SUBTRACTED,
            "target": cls.TARGET_RENORMALIZED,
            "target_renormalized": cls.TARGET_RENORMALIZED,
            "force_2pi": cls.TARGET_RENORMALIZED,
            "calibrated_2pi": cls.TARGET_RENORMALIZED,
        }
        if v in aliases:
            return aliases[v]
        raise ValueError(f"Unknown energy mass mode {value!r}")


@dataclass(frozen=True)
class HornTorusParams:
    """Primitive-safe horn-torus energy parameters.

    The dimensional fields are used only for reporting dimensional E_loop.  The
    dimensionless loop geometry is lambda_=R/a0.  Electron-normalized constants are
    not required by this module.
    """

    rho_sat: float = 1.0       # kg m^-3
    Gamma0: float = 1.0        # m^2 s^-1
    a0: float = 1.0            # m
    lambda_: float = 1.0       # R/a0. Named lambda_ because lambda is reserved.
    epsilon: float = 1.0       # a_soft/a0
    quadrature_n: int = 32768
    core_constant: float = 1.75
    mass_mode: str = EnergyMassMode.KINETIC_PLUS_CAVITY.value

    @property
    def R(self) -> float:
        return self.lambda_ * self.a0

    @property
    def v0(self) -> float:
        return v0_from_gamma_a0(self.Gamma0, self.a0)

    @property
    def energy_mass_mode(self) -> EnergyMassMode:
        return EnergyMassMode.from_any(self.mass_mode)


@dataclass(frozen=True)
class HornTorusResult:
    lambda_: float
    epsilon: float
    R: float
    v0: float

    Xi_filament: float
    Xi_cavitation: float
    Xi_renormalization: float
    Xi_total: float          # strict hollow total = Xi_filament + Xi_cavitation
    Xi_mass: float           # selected mass-energy value after mode/subtraction

    chi_K: float
    chi_cavitation: float
    chi_renormalization: float
    chi_E_hollow_total: float
    chi_E: float             # selected mass-energy chi_E
    E_loop: float            # selected mass-energy E_loop
    target_residual: float   # (selected chi_E - 2*pi)/(2*pi)

    mass_mode: str
    kernel: str
    quadrature_n: int
    target_chi_E: float = TARGET_CHI_E
    target_xi_E: float = TARGET_XI_E
    status: str = "RESEARCH-TRACK / FALSIFICATION TEST / NOT CANONIZED"

    # Backward-compatible aliases used by the v3/v4 runner/tests.
    @property
    def xi_filament(self) -> float:
        return self.Xi_filament

    @property
    def xi_cavitation(self) -> float:
        return self.Xi_cavitation

    @property
    def xi_total_hollow(self) -> float:
        return self.Xi_total

    @property
    def chi_E_hollow(self) -> float:
        return self.chi_E_hollow_total

    @property
    def residual_kinetic_to_2pi(self) -> float:
        return (self.chi_K - TARGET_CHI_E) / TARGET_CHI_E

    @property
    def residual_total_to_2pi(self) -> float:
        return (self.chi_E_hollow_total - TARGET_CHI_E) / TARGET_CHI_E

    @property
    def residual_mass_to_2pi(self) -> float:
        return self.target_residual


@dataclass(frozen=True)
class PrimitiveScales:
    """Optional primitive scales for deriving a0 and reporting c_T/alpha_sst_0."""

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


# ---------------------------------------------------------------------------
# Validation and primitive identities
# ---------------------------------------------------------------------------

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
    """Cavitation work in Xi normalization E/(rho_sat Gamma0^2 a0)."""
    require_lambda(lambda_)
    return 0.25 * lambda_


def chi_from_xi(xi: float) -> float:
    """chi_E = E/(rho_sat v0^2 a0^3) = 4*pi^2*Xi_E."""
    return 4.0 * PI * PI * xi


def mass_xi_components(xi_filament: float, xi_cavitation_value: float, mode: str | EnergyMassMode) -> tuple[float, float]:
    """Return (Xi_renormalization, Xi_mass) for the selected mass-energy mode."""
    m = EnergyMassMode.from_any(mode)
    xi_hollow = xi_filament + xi_cavitation_value
    if m == EnergyMassMode.KINETIC_ONLY:
        return 0.0, xi_filament
    if m == EnergyMassMode.KINETIC_PLUS_CAVITY:
        return 0.0, xi_hollow
    if m == EnergyMassMode.VACUUM_SUBTRACTED:
        return -xi_cavitation_value, xi_filament
    if m == EnergyMassMode.TARGET_RENORMALIZED:
        return TARGET_XI_E - xi_hollow, TARGET_XI_E
    raise ValueError(f"Unsupported mass mode {mode!r}")


# ---------------------------------------------------------------------------
# Analytic/diagnostic kernels
# ---------------------------------------------------------------------------

def xi_thin_ring(lambda_: float, core_constant: float = 1.75) -> float:
    """Thin-ring diagnostic, not a horn proof for lambda_=O(1)."""
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
    length is epsilon*a0.  If cpp_mod exposes the compiled kernel, it is used.
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


def _cpp_kernel(cpp_mod: Any, kernel: HornTorusKernel):
    if cpp_mod is None or not hasattr(cpp_mod, "HornTorusKernel"):
        return None
    if kernel == HornTorusKernel.THIN_RING_ASYMPTOTIC:
        return cpp_mod.HornTorusKernel.THIN_RING_ASYMPTOTIC
    return cpp_mod.HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT


def _cpp_mass_mode(cpp_mod: Any, mode: EnergyMassMode):
    if cpp_mod is None or not hasattr(cpp_mod, "EnergyMassMode"):
        return None
    if mode == EnergyMassMode.KINETIC_ONLY:
        return cpp_mod.EnergyMassMode.KINETIC_ONLY
    if mode == EnergyMassMode.KINETIC_PLUS_CAVITY:
        return cpp_mod.EnergyMassMode.KINETIC_PLUS_CAVITY
    if mode == EnergyMassMode.VACUUM_SUBTRACTED:
        return cpp_mod.EnergyMassMode.VACUUM_SUBTRACTED
    return cpp_mod.EnergyMassMode.TARGET_RENORMALIZED


def _cpp_params(cpp_mod: Any, params: HornTorusParams):
    p = cpp_mod.HornTorusParams()
    p.rho_sat = float(params.rho_sat)
    p.Gamma0 = float(params.Gamma0)
    p.a0 = float(params.a0)
    p.lambda_ = float(params.lambda_)
    p.epsilon = float(params.epsilon)
    p.quadrature_n = int(params.quadrature_n)
    p.core_constant = float(params.core_constant)
    if hasattr(p, "mass_mode"):
        p.mass_mode = _cpp_mass_mode(cpp_mod, params.energy_mass_mode)
    return p


def _result_from_cpp(r: Any, kernel: HornTorusKernel, quadrature_n: int) -> HornTorusResult:
    xi_total = float(r.Xi_total)
    xi_mass = float(getattr(r, "Xi_mass", xi_total))
    chi_e_hollow = float(getattr(r, "chi_E_hollow_total", chi_from_xi(xi_total)))
    return HornTorusResult(
        lambda_=float(r.lambda_),
        epsilon=float(r.epsilon),
        R=float(r.R),
        v0=float(r.v0),
        Xi_filament=float(r.Xi_filament),
        Xi_cavitation=float(r.Xi_cavitation),
        Xi_renormalization=float(getattr(r, "Xi_renormalization", 0.0)),
        Xi_total=xi_total,
        Xi_mass=xi_mass,
        chi_K=float(r.chi_K),
        chi_cavitation=float(r.chi_cavitation),
        chi_renormalization=float(getattr(r, "chi_renormalization", 0.0)),
        chi_E_hollow_total=chi_e_hollow,
        chi_E=float(r.chi_E),
        E_loop=float(r.E_loop),
        target_residual=float(r.target_residual),
        mass_mode=str(getattr(r, "mass_mode", EnergyMassMode.KINETIC_PLUS_CAVITY.value)),
        kernel=kernel.value,
        quadrature_n=int(quadrature_n),
    )


def evaluate_horn_torus(
    params: HornTorusParams,
    kernel: str | HornTorusKernel = HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT,
    mass_mode: str | EnergyMassMode | None = None,
    cpp_mod: Any = None,
) -> HornTorusResult:
    """Evaluate kinetic-only, hollow-total, and selected mass-mode energy factors."""
    require_positive("rho_sat", params.rho_sat)
    require_positive("Gamma0", params.Gamma0)
    require_positive("a0", params.a0)
    require_lambda(params.lambda_)
    require_positive("epsilon", params.epsilon)
    if params.quadrature_n < 128:
        raise ValueError("quadrature_n must be >= 128")
    kernel_e = HornTorusKernel.from_any(kernel)
    mode_e = EnergyMassMode.from_any(params.mass_mode if mass_mode is None else mass_mode)

    params2 = HornTorusParams(
        rho_sat=params.rho_sat,
        Gamma0=params.Gamma0,
        a0=params.a0,
        lambda_=params.lambda_,
        epsilon=params.epsilon,
        quadrature_n=params.quadrature_n,
        core_constant=params.core_constant,
        mass_mode=mode_e.value,
    )

    cpp_kernel = _cpp_kernel(cpp_mod, kernel_e)
    if cpp_kernel is not None and hasattr(cpp_mod, "horn_torus_energy") and hasattr(cpp_mod, "EnergyMassMode"):
        return _result_from_cpp(
            cpp_mod.horn_torus_energy(_cpp_params(cpp_mod, params2), cpp_kernel),
            kernel_e,
            params.quadrature_n,
        )

    if kernel_e == HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT:
        xi_fil = xi_regularized_circular_filament(
            params.lambda_, params.epsilon, params.quadrature_n, cpp_mod=cpp_mod
        )
    else:
        xi_fil = xi_thin_ring(params.lambda_, params.core_constant)

    xi_cav = xi_cavitation(params.lambda_)
    xi_ren, xi_mass = mass_xi_components(xi_fil, xi_cav, mode_e)
    xi_total = xi_fil + xi_cav
    chi_K = chi_from_xi(xi_fil)
    chi_cav = chi_from_xi(xi_cav)
    chi_ren = chi_from_xi(xi_ren)
    chi_hollow = chi_from_xi(xi_total)
    chi_E = chi_from_xi(xi_mass)
    E_loop = xi_mass * params.rho_sat * params.Gamma0 * params.Gamma0 * params.a0

    return HornTorusResult(
        lambda_=float(params.lambda_),
        epsilon=float(params.epsilon),
        R=float(params.R),
        v0=float(params.v0),
        Xi_filament=float(xi_fil),
        Xi_cavitation=float(xi_cav),
        Xi_renormalization=float(xi_ren),
        Xi_total=float(xi_total),
        Xi_mass=float(xi_mass),
        chi_K=float(chi_K),
        chi_cavitation=float(chi_cav),
        chi_renormalization=float(chi_ren),
        chi_E_hollow_total=float(chi_hollow),
        chi_E=float(chi_E),
        E_loop=float(E_loop),
        target_residual=float((chi_E - TARGET_CHI_E) / TARGET_CHI_E),
        mass_mode=mode_e.value,
        kernel=kernel_e.value,
        quadrature_n=int(params.quadrature_n),
    )


def scan_lambda(
    lambda_min: float,
    lambda_max: float,
    lambda_count: int,
    base: HornTorusParams,
    kernel: str | HornTorusKernel = HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT,
    mass_mode: str | EnergyMassMode | None = None,
    cpp_mod: Any = None,
) -> List[HornTorusResult]:
    """Scan lambda with the hard embedded-torus guard lambda_min>=1."""
    require_lambda(lambda_min)
    require_lambda(lambda_max)
    if lambda_max < lambda_min:
        raise ValueError("lambda_max must be >= lambda_min")
    if lambda_count < 2:
        raise ValueError("lambda_count must be >= 2")
    kernel_e = HornTorusKernel.from_any(kernel)
    mode_e = EnergyMassMode.from_any(base.mass_mode if mass_mode is None else mass_mode)

    values = np.linspace(lambda_min, lambda_max, lambda_count)
    return [
        evaluate_horn_torus(
            HornTorusParams(
                rho_sat=base.rho_sat,
                Gamma0=base.Gamma0,
                a0=base.a0,
                lambda_=float(lam),
                epsilon=base.epsilon,
                quadrature_n=base.quadrature_n,
                core_constant=base.core_constant,
                mass_mode=mode_e.value,
            ),
            kernel=kernel_e,
            cpp_mod=cpp_mod,
        )
        for lam in values
    ]


def minimize_lambda(
    lambda_min: float,
    lambda_max: float,
    base: HornTorusParams,
    kernel: str | HornTorusKernel = HornTorusKernel.REGULARIZED_CIRCULAR_FILAMENT,
    mass_mode: str | EnergyMassMode | None = None,
    cpp_mod: Any = None,
    iterations: int = 80,
) -> HornTorusResult:
    """Golden-section minimizer for the selected chi_E over lambda>=1."""
    require_lambda(lambda_min)
    require_lambda(lambda_max)
    if lambda_max < lambda_min:
        raise ValueError("lambda_max must be >= lambda_min")
    if iterations < 8:
        raise ValueError("iterations must be >= 8")
    kernel_e = HornTorusKernel.from_any(kernel)
    mode_e = EnergyMassMode.from_any(base.mass_mode if mass_mode is None else mass_mode)

    cpp_kernel = _cpp_kernel(cpp_mod, kernel_e)
    if cpp_kernel is not None and hasattr(cpp_mod, "minimize_lambda") and hasattr(cpp_mod, "EnergyMassMode"):
        raw = cpp_mod.minimize_lambda(float(lambda_min), float(lambda_max), _cpp_params(cpp_mod, HornTorusParams(**{**asdict(base), "mass_mode": mode_e.value})), cpp_kernel, int(iterations))
        return _result_from_cpp(raw, kernel_e, base.quadrature_n)

    gr = (math.sqrt(5.0) - 1.0) / 2.0
    lo, hi = float(lambda_min), float(lambda_max)
    c = hi - gr * (hi - lo)
    d = lo + gr * (hi - lo)

    def f(lam: float) -> float:
        return evaluate_horn_torus(
            HornTorusParams(
                rho_sat=base.rho_sat,
                Gamma0=base.Gamma0,
                a0=base.a0,
                lambda_=lam,
                epsilon=base.epsilon,
                quadrature_n=base.quadrature_n,
                core_constant=base.core_constant,
                mass_mode=mode_e.value,
            ),
            kernel=kernel_e,
            cpp_mod=cpp_mod,
        ).chi_E

    fc, fd = f(c), f(d)
    for _ in range(iterations):
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - gr * (hi - lo)
            fc = f(c)
        else:
            lo, c, fc = c, d, fd
            d = lo + gr * (hi - lo)
            fd = f(d)
    lam = 0.5 * (lo + hi)
    return evaluate_horn_torus(
        HornTorusParams(
            rho_sat=base.rho_sat,
            Gamma0=base.Gamma0,
            a0=base.a0,
            lambda_=lam,
            epsilon=base.epsilon,
            quadrature_n=base.quadrature_n,
            core_constant=base.core_constant,
            mass_mode=mode_e.value,
        ),
        kernel=kernel_e,
        cpp_mod=cpp_mod,
    )


# ---------------------------------------------------------------------------
# General polygon kernel
# ---------------------------------------------------------------------------

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


def general_polyline_xi_filament(
    points: np.ndarray,
    epsilon: float = 1.0,
    a0: float = 1.0,
    cpp_mod: Any = None,
) -> float:
    """Regularized Neumann energy for any closed polyline.

    If `points` are dimensionless in a0-units, use a0=1.  If points are in
    physical units, set a0 to the physical core radius; the return value is still
    Xi_filament = E_filament/(rho_sat Gamma0^2 a0).
    """
    require_positive("epsilon", epsilon)
    require_positive("a0", a0)
    p = np.asarray(points, dtype=np.float64)
    if cpp_mod is not None:
        if hasattr(cpp_mod, "regularized_neumann_energy_dimensionless_scaled"):
            return float(cpp_mod.regularized_neumann_energy_dimensionless_scaled(p, float(a0), float(epsilon)))
        if hasattr(cpp_mod, "regularized_neumann_energy_dimensionless") and a0 == 1.0:
            return float(cpp_mod.regularized_neumann_energy_dimensionless(p, float(epsilon)))
    from sst_trefoil_biot_py import bs_energy_dimensionless

    return float(bs_energy_dimensionless(p, epsilon * a0, mode="regularized", cpp_mod=None) / a0)

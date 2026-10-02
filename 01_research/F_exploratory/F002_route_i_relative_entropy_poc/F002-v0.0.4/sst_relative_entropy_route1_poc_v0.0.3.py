#!/usr/bin/env python3
"""
SST Route-I / quantum-relative-entropy numerical proof-of-concept v0.0.3.

This script audits, in a controlled 1D horizon model, the chain

    coherent pulse -> T_UU -> S_rel -> delta A

used by Dorau & Much (PRL 136, 091602, 2026), and compares the
energy-flux/entropy route with a linearized Raychaudhuri focusing route.

Version 0.0.3 closes the v0.0.2 affine-scale and local modular/KMS gate
inside the homogeneous quadratic transverse-torsion sector.  The closure is

    Phi_T    = sqrt(Z_T) A,
    varphi_T = sqrt(Z_T / hbar) A,
    L_*      = 1 / |d_n ln S_clock| = c_T^2 / a_clock,
    phi_hat  = L_* sqrt(Z_T / hbar) A,

and, after canonical quantization in the effective metric with causal speed
c_T, the right-wedge vacuum is KMS under the boost/modular flow.  In Rindler
coordinates the modular action is U -> exp(-2*pi*s) U and

    beta_tau = 2*pi*L_*/c_T,
    T_KMS    = hbar*a_clock/(2*pi*c_T*k_B).

Important: this is a conditional effective-sector theorem.  It does not
derive K_T or c_T from the full nonlinear SST substrate, prove universal
monometricity, derive the Bekenstein-Hawking area coefficient, or establish
Einstein dynamics empirically.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception:  # plotting is optional
    plt = None

PI = math.pi
C_LIGHT = 299_792_458.0  # m s^-1, exact
RHO_F = 7.0e-7  # kg m^-3, SST canonical effective fluid density
HBAR = 1.054_571_817e-34  # J s, h/(2*pi) to the stated precision
K_B = 1.380_649e-23  # J K^-1, exact
R_C = 1.40897017e-15  # m, SST canonical core radius
VERSION = "0.0.3"


@dataclass(frozen=True)
class PulseParameters:
    amplitude: float = 0.01
    center: float = -2.0
    half_width: float = 0.75
    carrier: float = 2.5 * PI


@dataclass(frozen=True)
class TorsionNormalizationResult:
    length_scale_m: float
    rho_f_kg_m3: float
    k_t_pa: float
    c_t_m_s: float
    z_t_kg_m2_s: float
    canonical_factor_sqrt_z: float
    quantum_factor_m_minus_2: float
    dimensionless_factor_m_minus_1: float
    pulse_coefficient_displacement_m: float
    pulse_peak_displacement_m: float
    max_linear_strain: float
    action_slice_original: float
    action_slice_canonical: float
    physical_energy_original_j: float
    physical_energy_canonical_j: float
    symplectic_original: float
    symplectic_canonical: float
    relerr_action: float
    relerr_energy: float
    relerr_symplectic: float
    relerr_dimensionless_roundtrip: float


@dataclass(frozen=True)
class RindlerKMSResult:
    clock_log_gradient_m_inv: float
    length_scale_m: float
    proper_acceleration_m_s2: float
    beta_proper_time_s: float
    unruh_temperature_k: float
    metric_relerr_g_eta_eta: float
    metric_abs_g_eta_xi: float
    metric_relerr_g_xi_xi: float
    acceleration_relerr: float
    clock_gradient_relerr: float
    affine_dilation_relerr: float
    kms_complex_relerr: float
    detailed_balance_relerr: float
    temperature_identity_relerr: float


@dataclass(frozen=True)
class AuditResult:
    n: int
    s_rel_flux: float
    s_rel_modular_plus: float
    s_rel_modular_minus: float
    delta_a_entropy: float
    delta_a_weighted_ricci: float
    delta_a_linear_ode: float
    delta_a_nonlinear_ode: float
    relerr_modular_plus: float
    relerr_modular_minus: float
    relerr_entropy_vs_ricci: float
    relerr_linear_ode_vs_ricci: float
    nonlinear_fractional_correction: float


def trapz(y: np.ndarray, x: np.ndarray) -> float:
    """NumPy-version-independent trapezoidal integration."""
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def safe_relerr(value: float, reference: float) -> float:
    scale = max(abs(reference), np.finfo(float).tiny)
    return abs(value - reference) / scale


def compact_pulse(u: np.ndarray, p: PulseParameters) -> np.ndarray:
    """C-infinity compact bump with an internal carrier oscillation."""
    z = (u - p.center) / p.half_width
    out = np.zeros_like(u, dtype=float)
    inside = np.abs(z) < 1.0
    zi = z[inside]
    bump = np.exp(-1.0 / (1.0 - zi * zi))
    out[inside] = p.amplitude * bump * np.cos(p.carrier * zi)
    return out


def compact_pulse_du(u: np.ndarray, p: PulseParameters) -> np.ndarray:
    """Analytic derivative d phi / dU of compact_pulse."""
    z = (u - p.center) / p.half_width
    out = np.zeros_like(u, dtype=float)
    inside = np.abs(z) < 1.0
    zi = z[inside]
    one_minus = 1.0 - zi * zi
    bump = np.exp(-1.0 / one_minus)
    dbump_dz = bump * (-2.0 * zi / (one_minus * one_minus))
    dcarrier_dz = -p.carrier * np.sin(p.carrier * zi)
    out[inside] = (
        p.amplitude
        / p.half_width
        * (dbump_dz * np.cos(p.carrier * zi) + bump * dcarrier_dz)
    )
    return out


def symplectic_form(
    u: np.ndarray,
    f: np.ndarray,
    df_du: np.ndarray,
    g: np.ndarray,
    dg_du: np.ndarray,
    cross_section_area: float,
) -> float:
    """sigma(f,g)=A_perp int (f g' - g f') dU."""
    return cross_section_area * trapz(f * dg_du - g * df_du, u)


def modular_half_derivative(
    u: np.ndarray,
    p: PulseParameters,
    cross_section_area: float,
    finite_difference_step: float,
    dilation_sign: float,
) -> float:
    """
    Compute (1/2) d/dt sigma(phi^t,phi)|_0 by a central difference.

    phi^t(U)=phi(exp(dilation_sign*2*pi*t) U).
    The sign is exposed because horizon orientation/pullback conventions
    determine whether this expression equals +S_rel or -S_rel.
    """
    phi = compact_pulse(u, p)
    dphi = compact_pulse_du(u, p)

    def sigma_at(t: float) -> float:
        scale = math.exp(dilation_sign * 2.0 * PI * t)
        phi_t = compact_pulse(scale * u, p)
        dphi_t = scale * compact_pulse_du(scale * u, p)
        return symplectic_form(
            u, phi_t, dphi_t, phi, dphi, cross_section_area
        )

    h = finite_difference_step
    derivative = (sigma_at(h) - sigma_at(-h)) / (2.0 * h)
    return 0.5 * derivative


def cumulative_integral_to_zero(u: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Return I(U_i)=int_{U_i}^{0} values(s) ds on an ascending grid."""
    result = np.zeros_like(values)
    # Integrate from the right endpoint toward negative U.
    for i in range(len(u) - 2, -1, -1):
        du = u[i + 1] - u[i]
        result[i] = result[i + 1] + 0.5 * du * (values[i] + values[i + 1])
    return result


def rk4_backward_from_zero(
    u: np.ndarray, source: Callable[[float], float]
) -> np.ndarray:
    """
    Solve dtheta/dU = -theta^2/2 - source(U), theta(0)=0,
    backward along an ascending U grid ending at U=0.
    """
    theta = np.zeros_like(u)

    def rhs(x: float, y: float) -> float:
        return -0.5 * y * y - source(x)

    for i in range(len(u) - 1, 0, -1):
        x0 = float(u[i])
        y0 = float(theta[i])
        h = float(u[i - 1] - u[i])  # negative
        k1 = rhs(x0, y0)
        k2 = rhs(x0 + 0.5 * h, y0 + 0.5 * h * k1)
        k3 = rhs(x0 + 0.5 * h, y0 + 0.5 * h * k2)
        k4 = rhs(x0 + h, y0 + h * k3)
        theta[i - 1] = y0 + h * (k1 + 2*k2 + 2*k3 + k4) / 6.0
    return theta


def run_audit(
    n: int,
    p: PulseParameters,
    alpha: float,
    cross_section_area: float,
    u_min: float,
    finite_difference_step: float,
) -> tuple[AuditResult, dict[str, np.ndarray]]:
    if n < 101:
        raise ValueError("n must be >= 101")
    if u_min >= p.center - p.half_width:
        raise ValueError("u_min must lie left of the pulse support")
    if p.center + p.half_width >= 0.0:
        raise ValueError("pulse support must remain strictly in U<0")

    u = np.linspace(u_min, 0.0, n)
    phi = compact_pulse(u, p)
    dphi = compact_pulse_du(u, p)
    t_uu = dphi * dphi

    weighted_flux = -cross_section_area * trapz(u * t_uu, u)
    s_rel_flux = 2.0 * PI * weighted_flux

    s_mod_plus = modular_half_derivative(
        u, p, cross_section_area, finite_difference_step, +1.0
    )
    s_mod_minus = modular_half_derivative(
        u, p, cross_section_area, finite_difference_step, -1.0
    )

    r_uu = alpha * t_uu
    delta_a_entropy = alpha * s_rel_flux / (2.0 * PI)
    delta_a_weighted_ricci = -cross_section_area * trapz(u * r_uu, u)

    theta_linear = cumulative_integral_to_zero(u, r_uu)
    delta_a_linear_ode = cross_section_area * trapz(theta_linear, u)

    # Evaluate the source analytically so RK4 is not tied to grid interpolation.
    def r_source(x: float) -> float:
        arr = np.asarray([x], dtype=float)
        return alpha * float(compact_pulse_du(arr, p)[0] ** 2)

    theta_nonlinear = rk4_backward_from_zero(u, r_source)
    delta_a_nonlinear_ode = cross_section_area * trapz(theta_nonlinear, u)

    result = AuditResult(
        n=n,
        s_rel_flux=s_rel_flux,
        s_rel_modular_plus=s_mod_plus,
        s_rel_modular_minus=s_mod_minus,
        delta_a_entropy=delta_a_entropy,
        delta_a_weighted_ricci=delta_a_weighted_ricci,
        delta_a_linear_ode=delta_a_linear_ode,
        delta_a_nonlinear_ode=delta_a_nonlinear_ode,
        relerr_modular_plus=safe_relerr(s_mod_plus, s_rel_flux),
        relerr_modular_minus=safe_relerr(s_mod_minus, s_rel_flux),
        relerr_entropy_vs_ricci=safe_relerr(
            delta_a_entropy, delta_a_weighted_ricci
        ),
        relerr_linear_ode_vs_ricci=safe_relerr(
            delta_a_linear_ode, delta_a_weighted_ricci
        ),
        nonlinear_fractional_correction=(
            (delta_a_nonlinear_ode - delta_a_linear_ode)
            / max(abs(delta_a_linear_ode), np.finfo(float).tiny)
        ),
    )

    arrays = {
        "u": u,
        "phi": phi,
        "dphi_du": dphi,
        "t_uu": t_uu,
        "r_uu": r_uu,
        "theta_linear": theta_linear,
        "theta_nonlinear": theta_nonlinear,
    }
    return result, arrays



def run_torsion_normalization_audit(
    p: PulseParameters,
    rho_f: float,
    k_t: float,
    length_scale_m: float,
    cross_section_area_hat: float,
    n: int = 4001,
) -> tuple[TorsionNormalizationResult, dict[str, np.ndarray]]:
    """
    Verify the canonical field redefinition implied by the SST torsion action.

    Starting point (one transverse polarization, x^0=c_T t):

        S = 1/2 int d x^0 d^3x Z_T[(d_0 A)^2-(grad A)^2],
        Z_T = sqrt(rho_f K_T) = rho_f c_T.

    Therefore Phi_T=sqrt(Z_T)A gives a canonical quadratic action.  Dividing
    by sqrt(hbar) gives the quantum-normalized field varphi_T, and using
    u=x/L_* gives the dimensionless numerical field phi_hat=L_* varphi_T.
    """
    if rho_f <= 0.0 or k_t <= 0.0 or length_scale_m <= 0.0:
        raise ValueError("rho_f, k_t and length_scale_m must be positive")
    if cross_section_area_hat <= 0.0:
        raise ValueError("cross_section_area_hat must be positive")

    c_t = math.sqrt(k_t / rho_f)
    z_t = math.sqrt(rho_f * k_t)
    canonical_factor = math.sqrt(z_t)
    quantum_factor = math.sqrt(z_t / HBAR)
    dimensionless_factor = length_scale_m * quantum_factor

    # A compact standing-wave slice avoids the null-wave cancellation of the
    # Lagrangian density while preserving the same field normalization.
    q = np.linspace(-1.25, 1.25, n)
    profile_params = PulseParameters(
        amplitude=p.amplitude,
        center=0.0,
        half_width=1.0,
        carrier=p.carrier,
    )
    profile = compact_pulse(q, profile_params)
    dprofile_dq = compact_pulse_du(q, profile_params)
    phase = 0.37
    omega_hat = 1.7

    # phi_hat is dimensionless.  A has units of displacement [m].
    phi_hat = profile * math.cos(phase)
    d0_phi_hat = -omega_hat * profile * math.sin(phase)
    dxhat_phi_hat = dprofile_dq * math.cos(phase)

    a_field = phi_hat / dimensionless_factor
    d0_a = d0_phi_hat / (length_scale_m * dimensionless_factor)
    dx_a = dxhat_phi_hat / (length_scale_m * dimensionless_factor)

    phi_canonical = canonical_factor * a_field
    d0_phi_canonical = canonical_factor * d0_a
    dx_phi_canonical = canonical_factor * dx_a

    # Physical coordinate and area.  The input area is dimensionless in L_*^2.
    x = length_scale_m * q
    area_physical = cross_section_area_hat * length_scale_m**2

    action_slice_original = area_physical * trapz(
        0.5 * z_t * (d0_a**2 - dx_a**2), x
    )
    action_slice_canonical = area_physical * trapz(
        0.5 * (d0_phi_canonical**2 - dx_phi_canonical**2), x
    )

    dt_a = c_t * d0_a
    energy_original = area_physical * trapz(
        0.5 * (rho_f * dt_a**2 + k_t * dx_a**2), x
    )
    energy_canonical = c_t * area_physical * trapz(
        0.5 * (d0_phi_canonical**2 + dx_phi_canonical**2), x
    )

    # Canonical two-form preservation under Phi_T=sqrt(Z_T)A.
    f = compact_pulse(
        q,
        PulseParameters(amplitude=0.7 * p.amplitude, center=-0.15,
                        half_width=0.85, carrier=1.3 * p.carrier),
    )
    g = compact_pulse(
        q,
        PulseParameters(amplitude=0.5 * p.amplitude, center=0.18,
                        half_width=0.78, carrier=0.8 * p.carrier),
    )
    delta1_a = f / dimensionless_factor
    delta2_a = g / dimensionless_factor
    delta1_d0a = g / (length_scale_m * dimensionless_factor)
    delta2_d0a = -f / (length_scale_m * dimensionless_factor)
    symplectic_original = area_physical * trapz(
        z_t * (delta1_d0a * delta2_a - delta2_d0a * delta1_a), x
    )
    delta1_phi = canonical_factor * delta1_a
    delta2_phi = canonical_factor * delta2_a
    delta1_d0phi = canonical_factor * delta1_d0a
    delta2_d0phi = canonical_factor * delta2_d0a
    symplectic_canonical = area_physical * trapz(
        delta1_d0phi * delta2_phi - delta2_d0phi * delta1_phi, x
    )

    reconstructed_phi_hat = (
        length_scale_m * math.sqrt(z_t / HBAR) * a_field
    )
    roundtrip_scale = max(float(np.max(np.abs(phi_hat))), np.finfo(float).tiny)
    roundtrip_error = float(
        np.max(np.abs(reconstructed_phi_hat - phi_hat)) / roundtrip_scale
    )

    coefficient_displacement = p.amplitude / dimensionless_factor
    peak_displacement = float(np.max(np.abs(a_field)))
    max_strain = float(np.max(np.abs(dx_a)))

    result = TorsionNormalizationResult(
        length_scale_m=length_scale_m,
        rho_f_kg_m3=rho_f,
        k_t_pa=k_t,
        c_t_m_s=c_t,
        z_t_kg_m2_s=z_t,
        canonical_factor_sqrt_z=canonical_factor,
        quantum_factor_m_minus_2=quantum_factor,
        dimensionless_factor_m_minus_1=dimensionless_factor,
        pulse_coefficient_displacement_m=coefficient_displacement,
        pulse_peak_displacement_m=peak_displacement,
        max_linear_strain=max_strain,
        action_slice_original=action_slice_original,
        action_slice_canonical=action_slice_canonical,
        physical_energy_original_j=energy_original,
        physical_energy_canonical_j=energy_canonical,
        symplectic_original=symplectic_original,
        symplectic_canonical=symplectic_canonical,
        relerr_action=safe_relerr(action_slice_canonical, action_slice_original),
        relerr_energy=safe_relerr(energy_canonical, energy_original),
        relerr_symplectic=safe_relerr(
            symplectic_canonical, symplectic_original
        ),
        relerr_dimensionless_roundtrip=roundtrip_error,
    )
    arrays = {
        "q": q,
        "phi_hat": phi_hat,
        "a_field_m": a_field,
        "strain": dx_a,
    }
    return result, arrays


def normalization_scale_sweep(
    p: PulseParameters,
    rho_f: float,
    k_t: float,
    scales_m: Iterable[float],
) -> list[dict[str, float | bool | str]]:
    """Report how a fixed dimensionless pulse maps to physical displacement."""
    rows: list[dict[str, float | bool | str]] = []
    for scale in scales_m:
        result, _ = run_torsion_normalization_audit(
            p=p,
            rho_f=rho_f,
            k_t=k_t,
            length_scale_m=float(scale),
            cross_section_area_hat=1.0,
            n=2001,
        )
        rows.append(
            {
                "length_scale_m": result.length_scale_m,
                "dimensionless_factor_m_minus_1": result.dimensionless_factor_m_minus_1,
                "pulse_coefficient_displacement_m": result.pulse_coefficient_displacement_m,
                "pulse_peak_displacement_m": result.pulse_peak_displacement_m,
                "max_linear_strain": result.max_linear_strain,
                "linear_small_strain_gate_lt_0_1": result.max_linear_strain < 0.1,
                "interpretation": (
                    "linear displacement regime"
                    if result.max_linear_strain < 0.1
                    else "outside linear displacement regime for this fixed normalized amplitude"
                ),
            }
        )
    return rows



def massless_rindler_wightman(
    delta_tau: np.ndarray | complex,
    length_scale_m: float,
    c_t_m_s: float,
) -> np.ndarray:
    """
    Analytic Wightman function of the quantum-normalized massless field
    along the uniformly accelerated orbit xi=L_*.

        W(z) = -[16*pi^2 L_*^2 sinh^2(c_T z/(2 L_*))]^{-1}.

    The argument z is complex proper time.  Points at the poles are excluded.
    """
    z = np.asarray(delta_tau, dtype=np.complex128)
    argument = c_t_m_s * z / (2.0 * length_scale_m)
    return -1.0 / (
        16.0 * PI * PI * length_scale_m * length_scale_m
        * np.sinh(argument) ** 2
    )


def run_rindler_kms_audit(
    c_t_m_s: float,
    clock_log_gradient_m_inv: float,
) -> tuple[RindlerKMSResult, list[dict[str, float]]]:
    """
    Close the v0.0.2 local affine-scale and KMS gate in the free torsion sector.

    The coarse-grained Swirl-Clock is used as a local lapse S_clock.  In the
    Rindler linearization around the reference orbit,

        S_clock(xi) = xi/L_*,
        |d_xi ln S_clock|_{xi=L_*} = 1/L_*,
        a_clock = c_T^2/L_*.

    Canonical quantization of each independent transverse polarization gives
    a free massless field in the effective Minkowski metric.  The wedge vacuum
    then has boost modular flow, beta_eta=2*pi, and physical inverse temperature
    beta_tau=2*pi*L_*/c_T.
    """
    if c_t_m_s <= 0.0 or clock_log_gradient_m_inv <= 0.0:
        raise ValueError("c_T and the clock logarithmic gradient must be positive")

    length_scale = 1.0 / clock_log_gradient_m_inv
    acceleration = c_t_m_s * c_t_m_s / length_scale
    beta_tau = 2.0 * PI * length_scale / c_t_m_s
    temperature = HBAR / (K_B * beta_tau)

    # Rindler Jacobian audit: X0=xi*sinh(eta), X1=xi*cosh(eta).
    eta = np.linspace(-2.0, 2.0, 31)
    xi = length_scale * np.linspace(0.4, 2.4, 31)
    ee, xx = np.meshgrid(eta, xi, indexing="ij")
    dx0_deta = xx * np.cosh(ee)
    dx1_deta = xx * np.sinh(ee)
    dx0_dxi = np.sinh(ee)
    dx1_dxi = np.cosh(ee)
    g_eta_eta = -(dx0_deta**2) + dx1_deta**2
    g_eta_xi = -(dx0_deta * dx0_dxi) + dx1_deta * dx1_dxi
    g_xi_xi = -(dx0_dxi**2) + dx1_dxi**2
    metric_err_eta = float(np.max(np.abs(g_eta_eta + xx**2) / (xx**2)))
    metric_abs_cross = float(np.max(np.abs(g_eta_xi)) / length_scale)
    metric_err_xi = float(np.max(np.abs(g_xi_xi - 1.0)))

    # Constant-proper-acceleration orbit xi=L_*.
    tau = beta_tau * np.linspace(-0.31, 0.37, 41)
    rapidity = c_t_m_s * tau / length_scale
    acc0 = (c_t_m_s**2 / length_scale) * np.sinh(rapidity)
    acc1 = (c_t_m_s**2 / length_scale) * np.cosh(rapidity)
    acc_norm = np.sqrt(np.maximum(-(acc0**2) + acc1**2, 0.0))
    acceleration_err = float(
        np.max(np.abs(acc_norm - acceleration)) / acceleration
    )

    # The clock-lapse gradient fixes L_* and the same proper acceleration.
    gradient_step = 1.0e-5 * length_scale
    lapse_plus = (length_scale + gradient_step) / length_scale
    lapse_minus = (length_scale - gradient_step) / length_scale
    gradient_numeric = (
        math.log(lapse_plus) - math.log(lapse_minus)
    ) / (2.0 * gradient_step)
    clock_gradient_err = safe_relerr(
        gradient_numeric, clock_log_gradient_m_inv
    )

    # Boost/modular flow: U=X0-X1=-xi*exp(-eta), eta -> eta+2*pi*s.
    modular_s = np.linspace(-0.35, 0.35, 29)
    eta0 = 0.43
    xi0 = 1.17 * length_scale
    u0 = -xi0 * math.exp(-eta0)
    u_boost = -xi0 * np.exp(-(eta0 + 2.0 * PI * modular_s))
    u_expected = u0 * np.exp(-2.0 * PI * modular_s)
    affine_err = float(
        np.max(np.abs(u_boost - u_expected))
        / max(np.max(np.abs(u_expected)), np.finfo(float).tiny)
    )

    # Complex-time KMS identity W(z)=W(-z+i beta) inside the analytic strip.
    real_part = beta_tau * np.linspace(-0.61, 0.73, 23)
    imag_fractions = (0.17, 0.31, 0.43)
    kms_errors: list[float] = []
    for fraction in imag_fractions:
        z = real_part + 1j * fraction * beta_tau
        lhs = massless_rindler_wightman(z, length_scale, c_t_m_s)
        rhs = massless_rindler_wightman(
            -z + 1j * beta_tau, length_scale, c_t_m_s
        )
        scale = max(float(np.max(np.abs(lhs))), np.finfo(float).tiny)
        kms_errors.append(float(np.max(np.abs(lhs - rhs)) / scale))
    kms_err = max(kms_errors)

    # Bosonic detailed balance for an Unruh-DeWitt gap Omega.
    balance_rows: list[dict[str, float]] = []
    balance_errors: list[float] = []
    for beta_omega in (0.2, 0.7, 1.5, 3.0, 6.0):
        omega = beta_omega / beta_tau
        excitation = omega / (2.0 * PI * math.expm1(beta_omega))
        deexcitation = omega / (
            2.0 * PI * (-math.expm1(-beta_omega))
        )
        ratio = excitation / deexcitation
        expected = math.exp(-beta_omega)
        error = safe_relerr(ratio, expected)
        balance_errors.append(error)
        balance_rows.append(
            {
                "beta_omega": beta_omega,
                "omega_s_inv": omega,
                "excitation_rate_normalized": excitation,
                "deexcitation_rate_normalized": deexcitation,
                "ratio": ratio,
                "expected_exp_minus_beta_omega": expected,
                "relative_error": error,
            }
        )
    detailed_balance_err = max(balance_errors)

    temperature_from_acceleration = (
        HBAR * acceleration / (2.0 * PI * c_t_m_s * K_B)
    )
    temperature_err = safe_relerr(temperature, temperature_from_acceleration)

    result = RindlerKMSResult(
        clock_log_gradient_m_inv=clock_log_gradient_m_inv,
        length_scale_m=length_scale,
        proper_acceleration_m_s2=acceleration,
        beta_proper_time_s=beta_tau,
        unruh_temperature_k=temperature,
        metric_relerr_g_eta_eta=metric_err_eta,
        metric_abs_g_eta_xi=metric_abs_cross,
        metric_relerr_g_xi_xi=metric_err_xi,
        acceleration_relerr=acceleration_err,
        clock_gradient_relerr=clock_gradient_err,
        affine_dilation_relerr=affine_err,
        kms_complex_relerr=kms_err,
        detailed_balance_relerr=detailed_balance_err,
        temperature_identity_relerr=temperature_err,
    )
    return result, balance_rows


def rindler_scale_sweep(
    c_t_m_s: float,
    gradients_m_inv: Iterable[float],
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for gradient in gradients_m_inv:
        result, _ = run_rindler_kms_audit(c_t_m_s, float(gradient))
        rows.append(
            {
                "clock_log_gradient_m_inv": result.clock_log_gradient_m_inv,
                "length_scale_m": result.length_scale_m,
                "proper_acceleration_m_s2": result.proper_acceleration_m_s2,
                "beta_proper_time_s": result.beta_proper_time_s,
                "unruh_temperature_k": result.unruh_temperature_k,
                "kms_complex_relerr": result.kms_complex_relerr,
            }
        )
    return rows


def amplitude_scaling_test(
    n: int,
    p: PulseParameters,
    alpha: float,
    cross_section_area: float,
    u_min: float,
    finite_difference_step: float,
) -> float:
    r1, _ = run_audit(
        n, p, alpha, cross_section_area, u_min, finite_difference_step
    )
    p2 = PulseParameters(
        amplitude=2.0 * p.amplitude,
        center=p.center,
        half_width=p.half_width,
        carrier=p.carrier,
    )
    r2, _ = run_audit(
        n, p2, alpha, cross_section_area, u_min, finite_difference_step
    )
    return r2.s_rel_flux / r1.s_rel_flux


def zero_state_test(
    n: int,
    p: PulseParameters,
    alpha: float,
    cross_section_area: float,
    u_min: float,
    finite_difference_step: float,
) -> float:
    p0 = PulseParameters(
        amplitude=0.0,
        center=p.center,
        half_width=p.half_width,
        carrier=p.carrier,
    )
    r0, _ = run_audit(
        n, p0, alpha, cross_section_area, u_min, finite_difference_step
    )
    return max(
        abs(r0.s_rel_flux),
        abs(r0.delta_a_entropy),
        abs(r0.delta_a_linear_ode),
    )


def write_csv(path: Path, results: Iterable[AuditResult]) -> None:
    rows = [asdict(r) for r in results]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_plots(
    output_dir: Path,
    arrays: dict[str, np.ndarray],
    results: list[AuditResult],
) -> list[str]:
    if plt is None:
        return []

    generated: list[str] = []
    u = arrays["u"]

    fig = plt.figure(figsize=(8.0, 4.8))
    plt.plot(u, arrays["phi"], label=r"$\phi(U)$")
    plt.plot(u, arrays["t_uu"], label=r"$T_{UU}=(\partial_U\phi)^2$")
    plt.xlabel(r"Affine horizon coordinate $U$")
    plt.ylabel("Normalized field / flux")
    plt.title("Compact coherent horizon pulse")
    plt.legend()
    plt.tight_layout()
    path = output_dir / "pulse_and_flux.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    fig = plt.figure(figsize=(8.0, 4.8))
    plt.plot(u, arrays["theta_linear"], label="Linear Raychaudhuri")
    plt.plot(u, arrays["theta_nonlinear"], label="Nonlinear Raychaudhuri")
    plt.xlabel(r"Affine horizon coordinate $U$")
    plt.ylabel(r"Expansion $\theta(U)$")
    plt.title("Null-congruence focusing response")
    plt.legend()
    plt.tight_layout()
    path = output_dir / "raychaudhuri_response.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    ns = np.asarray([r.n for r in results], dtype=float)
    err_ode = np.asarray([r.relerr_linear_ode_vs_ricci for r in results])
    err_mod = np.asarray([r.relerr_modular_minus for r in results])
    positive_floor = np.finfo(float).eps

    fig = plt.figure(figsize=(8.0, 4.8))
    plt.loglog(ns, np.maximum(err_ode, positive_floor), marker="o", label="Raychaudhuri route")
    plt.loglog(ns, np.maximum(err_mod, positive_floor), marker="o", label="Modular route (matching orientation)")
    plt.xlabel("Grid points N")
    plt.ylabel("Relative error")
    plt.title("Numerical convergence")
    plt.legend()
    plt.tight_layout()
    path = output_dir / "convergence.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    return generated



def make_kms_plots(
    output_dir: Path,
    rindler: RindlerKMSResult,
    detailed_balance_rows: list[dict[str, float]],
) -> list[str]:
    if plt is None:
        return []

    generated: list[str] = []
    lstar = rindler.length_scale_m
    eta = np.linspace(-2.2, 2.2, 500)

    fig = plt.figure(figsize=(6.4, 6.0))
    horizon = np.linspace(-2.2 * lstar, 2.2 * lstar, 400)
    plt.plot(horizon, horizon, linestyle="--", label=r"$x^1=x^0$")
    plt.plot(horizon, -horizon, linestyle="--", label=r"$x^1=-x^0$")
    for ratio in (0.5, 1.0, 1.5):
        xi = ratio * lstar
        x0 = xi * np.sinh(eta)
        x1 = xi * np.cosh(eta)
        plt.plot(x0 / lstar, x1 / lstar, label=rf"$\xi/L_\star={ratio:g}$")
    plt.xlabel(r"$x^0/L_\star$")
    plt.ylabel(r"$x^1/L_\star$")
    plt.title("Effective torsion Rindler wedge")
    plt.xlim(-2.2, 2.2)
    plt.ylim(0.0, 2.8)
    plt.legend()
    plt.tight_layout()
    path = output_dir / "rindler_wedge.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)

    beta_omega = np.asarray([r["beta_omega"] for r in detailed_balance_rows])
    ratios = np.asarray([r["ratio"] for r in detailed_balance_rows])
    expected = np.asarray([
        r["expected_exp_minus_beta_omega"] for r in detailed_balance_rows
    ])
    fig = plt.figure(figsize=(7.2, 4.8))
    plt.semilogy(beta_omega, ratios, marker="o", label="Detector ratio")
    plt.semilogy(beta_omega, expected, linestyle="--", label=r"$e^{-\beta\Omega}$")
    plt.xlabel(r"$\beta_\tau\Omega$")
    plt.ylabel("Excitation / de-excitation rate")
    plt.title("KMS detailed balance")
    plt.legend()
    plt.tight_layout()
    path = output_dir / "kms_detailed_balance.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    generated.append(path.name)
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Numerical audit of the relative-entropy -> area-variation bridge."
    )
    parser.add_argument("--output-dir", default="sst_route1_poc_output")
    parser.add_argument("--grids", nargs="+", type=int, default=[101, 151, 201, 301, 501, 801, 1201, 2001])
    parser.add_argument("--amplitude", type=float, default=0.01)
    parser.add_argument("--center", type=float, default=-2.0)
    parser.add_argument("--half-width", type=float, default=0.75)
    parser.add_argument("--carrier", type=float, default=2.5 * PI)
    parser.add_argument("--alpha", type=float, default=8.0 * PI)
    parser.add_argument("--cross-section-area", type=float, default=1.0)
    parser.add_argument("--u-min", type=float, default=-4.0)
    parser.add_argument("--fd-step", type=float, default=1.0e-6)
    parser.add_argument(
        "--clock-log-gradient",
        type=float,
        default=1.0,
        help=(
            "Local logarithmic Swirl-Clock gradient |d_n ln S_clock| [m^-1]. "
            "The affine/Rindler scale is derived as L_*=1/gradient."
        ),
    )
    parser.add_argument(
        "--torsion-stiffness",
        type=float,
        default=None,
        help="K_T [Pa]. Default: calibrated rho_f*c^2 target.",
    )
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    p = PulseParameters(
        amplitude=args.amplitude,
        center=args.center,
        half_width=args.half_width,
        carrier=args.carrier,
    )

    results: list[AuditResult] = []
    last_arrays: dict[str, np.ndarray] | None = None
    for n in args.grids:
        result, arrays = run_audit(
            n=n,
            p=p,
            alpha=args.alpha,
            cross_section_area=args.cross_section_area,
            u_min=args.u_min,
            finite_difference_step=args.fd_step,
        )
        results.append(result)
        last_arrays = arrays

    finest = results[-1]
    amplitude_ratio = amplitude_scaling_test(
        results[-1].n,
        p,
        args.alpha,
        args.cross_section_area,
        args.u_min,
        args.fd_step,
    )
    zero_residual = zero_state_test(
        results[-1].n,
        p,
        args.alpha,
        args.cross_section_area,
        args.u_min,
        args.fd_step,
    )

    k_t = (
        float(args.torsion_stiffness)
        if args.torsion_stiffness is not None
        else RHO_F * C_LIGHT * C_LIGHT
    )
    c_t = math.sqrt(k_t / RHO_F)
    z_t = math.sqrt(RHO_F * k_t)
    if args.clock_log_gradient <= 0.0:
        raise ValueError("--clock-log-gradient must be positive")
    rindler_kms, detailed_balance_rows = run_rindler_kms_audit(
        c_t_m_s=c_t,
        clock_log_gradient_m_inv=args.clock_log_gradient,
    )
    derived_length_scale = rindler_kms.length_scale_m
    normalization, normalization_arrays = run_torsion_normalization_audit(
        p=p,
        rho_f=RHO_F,
        k_t=k_t,
        length_scale_m=derived_length_scale,
        cross_section_area_hat=args.cross_section_area,
    )
    normalization_sweep = normalization_scale_sweep(
        p=p,
        rho_f=RHO_F,
        k_t=k_t,
        scales_m=[derived_length_scale, 1.0e-3, R_C],
    )
    kms_scale_sweep = rindler_scale_sweep(
        c_t_m_s=c_t,
        gradients_m_inv=list(dict.fromkeys([
            args.clock_log_gradient, 1.0e-3, 1.0, 1.0e3, 1.0 / R_C
        ])),
    )

    # The source's written + dilation gives the opposite sign on this U<0
    # orientation; the - dilation convention matches the positive flux formula.
    matching_orientation = (
        "exp(-2*pi*t)" if finest.relerr_modular_minus < finest.relerr_modular_plus
        else "exp(+2*pi*t)"
    )

    tests = {
        "relative_entropy_nonnegative": finest.s_rel_flux >= -1e-13,
        "zero_state_vanishes": zero_residual < 1e-13,
        "quadratic_amplitude_scaling": abs(amplitude_ratio - 4.0) < 5e-6,
        "entropy_area_equals_weighted_ricci": finest.relerr_entropy_vs_ricci < 1e-12,
        "linear_raychaudhuri_converged": finest.relerr_linear_ode_vs_ricci < 5e-5,
        "one_modular_orientation_matches": min(
            finest.relerr_modular_plus, finest.relerr_modular_minus
        ) < 5e-5,
        "torsion_action_is_canonically_normalized": normalization.relerr_action < 1e-12,
        "torsion_hamiltonian_is_canonically_normalized": normalization.relerr_energy < 1e-12,
        "torsion_symplectic_form_is_preserved": normalization.relerr_symplectic < 1e-12,
        "dimensionless_field_roundtrip": normalization.relerr_dimensionless_roundtrip < 1e-12,
        "rindler_metric_reconstruction": max(
            rindler_kms.metric_relerr_g_eta_eta,
            rindler_kms.metric_abs_g_eta_xi,
            rindler_kms.metric_relerr_g_xi_xi,
        ) < 1e-12,
        "clock_gradient_fixes_affine_scale": rindler_kms.clock_gradient_relerr < 2e-4,
        "uniform_acceleration_matches_scale": rindler_kms.acceleration_relerr < 1e-12,
        "modular_boost_gives_affine_dilation": rindler_kms.affine_dilation_relerr < 1e-12,
        "wightman_function_satisfies_kms": rindler_kms.kms_complex_relerr < 1e-11,
        "unruh_detector_detailed_balance": rindler_kms.detailed_balance_relerr < 1e-12,
        "unruh_temperature_identity": rindler_kms.temperature_identity_relerr < 1e-12,
    }

    report = {
        "version": VERSION,
        "status": "PASS" if all(tests.values()) else "FAIL",
        "theorem_target_v0_0_3": {
            "status": "CLOSED-CONDITIONAL / EFFECTIVE-SECTOR THEOREM",
            "statement": (
                "For a homogeneous quadratic SST transverse-torsion patch, after "
                "projection to independent canonical polarizations and quantization "
                "in the effective metric with causal speed c_T, the local logarithmic "
                "Swirl-Clock gradient fixes L_*=1/|d_n ln S_clock|=c_T^2/a_clock. "
                "The right-wedge vacuum has boost modular flow U->exp(-2*pi*s)U, "
                "is KMS at beta_tau=2*pi*L_*/c_T, and therefore has "
                "T=hbar*a_clock/(2*pi*c_T*k_B). The coherent horizon field is "
                "phi_hat=L_*sqrt(Z_T/hbar)A."
            ),
            "assumptions": [
                "The local torsion coefficients rho_f and K_T are constant over the audited patch.",
                "The divergence-free torsion layer reduces to independent free transverse canonical polarizations.",
                "The chosen torsion vacuum is the quasifree effective-Minkowski/Hadamard ground state.",
                "The coarse-grained Swirl-Clock acts as the lapse of the same effective torsion cone.",
                "The clock lapse is nonzero and has an approximately constant logarithmic normal gradient over the local Rindler patch."
            ],
            "closed_items": [
                "The physical affine scale is no longer a numerical convention: L_*=1/|d_n ln S_clock|.",
                "The same scale equals c_T^2/a_clock for the reference uniformly accelerated clock orbit.",
                "The modular-flow sign is fixed geometrically: U=X0-X1 transforms as U->exp(-2*pi*s)U.",
                "The wedge two-point function satisfies the bosonic KMS identity and detector detailed balance.",
                "The quantum-normalized torsion polarization can therefore be identified with the coherent horizon field inside this effective sector."
            ],
            "remaining_nonclosure_outside_this_theorem": [
                "Derive K_T and c_T from nonlinear SST substrate microphysics without same-step calibration to measured c.",
                "Prove polarization decoupling, vacuum selection, and low-energy monometricity from the full knotted-vortex substrate.",
                "Derive the entropy-area coefficient eta_A^SST and Newton's constant without importing G or L_p.",
                "Establish the semiclassical Einstein equations as an empirical consequence of SST."
            ],
        },
        "epistemic_scope": {
            "verified": [
                "For the chosen compact coherent pulse, T_UU=(dphi/dU)^2 gives nonnegative weighted flux.",
                "S_rel=-2*pi*int U*T_UU and deltaA=alpha*S_rel/(2*pi) agree numerically with -int U*R_UU when R_UU=alpha*T_UU.",
                "The linearized Raychaudhuri ODE reproduces the same area variation under theta(0)=0.",
                "The zero state gives zero entropy and zero focusing.",
                "The response scales quadratically with pulse amplitude.",
                "The torsion field redefinition Phi_T=sqrt(Z_T)A preserves the quadratic action, physical Hamiltonian, and symplectic form numerically.",
                "The dimensionless numerical normalization is N_T(L_*)=L_*sqrt(Z_T/hbar), not a scale-free universal number.",
                "Within the stated free effective-sector assumptions, the Swirl-Clock logarithmic gradient fixes L_*=1/|d_n ln S_clock|=c_T^2/a_clock.",
                "The corresponding right-wedge vacuum has geometric boost modular flow, satisfies the complex-time KMS identity, and gives Unruh detailed balance.",
                "The affine horizon dilation orientation is fixed as U->exp(-2*pi*s)U for U=X0-X1.",
            ],
            "not_verified": [
                "That the full nonlinear SST substrate rigorously satisfies the free-field, vacuum, and polarization assumptions of the effective-sector theorem.",
                "A first-principles value of K_T or c_T from substrate microphysics.",
                "Universal species-independent monometricity for resolved vortex matter.",
                "The Bekenstein-Hawking area coefficient or Newton's constant from SST microphysics.",
                "The semiclassical Einstein equations as an empirical consequence of SST.",
            ],
        },
        "parameters": {
            "pulse": asdict(p),
            "alpha": args.alpha,
            "cross_section_area": args.cross_section_area,
            "u_min": args.u_min,
            "finite_difference_step": args.fd_step,
            "grids": args.grids,
            "clock_log_gradient_m_inv": args.clock_log_gradient,
            "derived_normalization_length_scale_m": derived_length_scale,
            "torsion_stiffness_pa": k_t,
        },
        "finest_grid_result": asdict(finest),
        "tests": tests,
        "amplitude_doubling_ratio_expected_4": amplitude_ratio,
        "zero_state_max_residual": zero_residual,
        "modular_orientation_audit": {
            "matching_orientation": matching_orientation,
            "note": (
                "With sigma(f,g)=int(f g'-g f')dU on U<0, the sign of the "
                "modular derivative depends on whether dilation acts as a pullback "
                "with exp(+2*pi*t) or exp(-2*pi*t), equivalently on horizon orientation."
            ),
        },
        "sst_transverse_torsion_constants_si": {
            "rho_f_kg_m-3": RHO_F,
            "c_T_m_s-1": c_t,
            "K_T_Pa": k_t,
            "Z_T_kg_m-2_s-1": z_t,
        },
        "rindler_kms_gate_closure": asdict(rindler_kms),
        "detailed_balance_sweep": detailed_balance_rows,
        "kms_scale_sweep": kms_scale_sweep,
        "torsion_normalization_audit": asdict(normalization),
        "normalization_scale_sweep": normalization_sweep,
        "normalization_scale_statement": (
            "The action-canonical normalization Phi_T=sqrt(Z_T)A is scale independent. "
            "In v0.0.3 the dimensionless scale is fixed locally by the Swirl-Clock lapse: "
            "L_*=1/|d_n ln S_clock|=c_T^2/a_clock. A fixed phi_hat amplitude may still "
            "violate the linear-strain regime when this derived scale is microscopic."
        ),
    }

    write_csv(output_dir / "convergence.csv", results)
    with (output_dir / "normalization_scale_sweep.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(normalization_sweep[0].keys())
        )
        writer.writeheader()
        writer.writerows(normalization_sweep)
    with (output_dir / "detailed_balance.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(detailed_balance_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(detailed_balance_rows)
    with (output_dir / "kms_scale_sweep.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(kms_scale_sweep[0].keys())
        )
        writer.writeheader()
        writer.writerows(kms_scale_sweep)
    with (output_dir / "audit_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    generated_plots: list[str] = []
    if not args.no_plots and last_arrays is not None:
        generated_plots = make_plots(output_dir, last_arrays, results)
        generated_plots.extend(
            make_kms_plots(output_dir, rindler_kms, detailed_balance_rows)
        )

    print(f"SST Route-I numerical proof-of-concept v{VERSION}")
    print(f"Status: {report['status']}")
    print(f"Finest grid: N={finest.n}")
    print(f"S_rel (flux route): {finest.s_rel_flux:.12e}")
    print(f"deltaA entropy route: {finest.delta_a_entropy:.12e}")
    print(f"deltaA Ricci route:   {finest.delta_a_weighted_ricci:.12e}")
    print(f"deltaA Raychaudhuri:  {finest.delta_a_linear_ode:.12e}")
    print(f"modular matching orientation: {matching_orientation}")
    print(f"amplitude-doubling ratio: {amplitude_ratio:.12f} (expected 4)")
    print(f"K_T = {k_t:.12e} Pa")
    print(f"c_T = sqrt(K_T/rho_f) = {c_t:.12e} m s^-1")
    print(f"Z_T = sqrt(rho_f*K_T) = {z_t:.12e} kg m^-2 s^-1")
    print("Theorem target v0.0.3: local affine/KMS gate closed in effective torsion sector")
    print(f"clock gradient = {rindler_kms.clock_log_gradient_m_inv:.12e} m^-1")
    print(f"L_* = 1/|d_n ln S_clock| = {rindler_kms.length_scale_m:.12e} m")
    print(f"a_clock = c_T^2/L_* = {rindler_kms.proper_acceleration_m_s2:.12e} m s^-2")
    print(f"beta_tau = {rindler_kms.beta_proper_time_s:.12e} s")
    print(f"T_KMS = {rindler_kms.unruh_temperature_k:.12e} K")
    print(f"KMS complex-time relative error = {rindler_kms.kms_complex_relerr:.3e}")
    print(f"N_T(L_*) = L_*sqrt(Z_T/hbar) = {normalization.dimensionless_factor_m_minus_1:.12e} m^-1")
    print(f"Equivalent torsion coefficient amplitude = {normalization.pulse_coefficient_displacement_m:.12e} m")
    print(f"Maximum linear strain = {normalization.max_linear_strain:.12e}")
    print(f"Action normalization rel. error = {normalization.relerr_action:.3e}")
    print(f"Hamiltonian normalization rel. error = {normalization.relerr_energy:.3e}")
    print(f"Symplectic normalization rel. error = {normalization.relerr_symplectic:.3e}")
    for name, passed in tests.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    print(f"Wrote: {output_dir / 'audit_report.json'}")
    print(f"Wrote: {output_dir / 'convergence.csv'}")
    print(f"Wrote: {output_dir / 'normalization_scale_sweep.csv'}")
    print(f"Wrote: {output_dir / 'detailed_balance.csv'}")
    print(f"Wrote: {output_dir / 'kms_scale_sweep.csv'}")
    for name in generated_plots:
        print(f"Wrote: {output_dir / name}")

    return 0 if all(tests.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

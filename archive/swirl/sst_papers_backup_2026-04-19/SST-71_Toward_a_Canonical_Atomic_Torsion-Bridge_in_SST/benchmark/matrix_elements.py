"""
Transition amplitudes and rates for 1s -> Coulomb continuum with helical probe.
M_{Elm}^{(h)} ∝ C_h * I_{Elm}^{(h)}, I_{Elm}^{(h)} = ∫ d³r [ψ_{Elm}]* γ_h ψ_1s.
Rate Gamma_h ∝ |C_h|² × sum_{l,m} |I_{Elm}^{(h)}|².

For axisymmetric probe (eps=0): phi integral done analytically → m = h (helical) or m = 0 (non_helical).
Main benchmark uses 2D (r, theta) Gauss-Legendre quadrature with N_r and N_theta.
When the sst_benchmark_core extension is built, the axisymmetric path uses the C++ kernel; otherwise
the pure-Python 2D loop is used (reference/fallback).
Broken axisymmetry (eps != 0) uses a slower 3D tplquad fallback; always Python.
"""

from __future__ import annotations

import logging
import numpy as np
from scipy.integrate import tplquad
from scipy.special import roots_legendre
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    import sst_benchmark_core as _cpp_core
    _CPP_AVAILABLE = True
except ImportError:
    _cpp_core = None
    _CPP_AVAILABLE = False

import constants
import hydrogen
import coulomb_continuum
import helical_probe


@dataclass
class BenchmarkParams:
    """Convergence and physical parameters for the benchmark.
    N_r and N_theta are active for the axisymmetric 2D quadrature path.
    N_phi is used for the 3D (broken-axisymmetry) path only.
    use_cpp: if True and sst_benchmark_core is available, use C++ kernels (2D and 3D).
    """
    R_max: float
    N_r: int
    N_theta: int
    l_max: int
    mp_dps: int
    w_r: float
    w_z: float
    q: float
    A_gamma: float
    eps: float = 0.0  # broken axisymmetry when > 0
    use_cpp: bool = True
    N_phi: int = 64  # azimuthal points for 3D (broken-axisymmetry) path

    @classmethod
    def default(cls) -> "BenchmarkParams":
        return cls(
            R_max=100.0 * constants.a0_sst,
            N_r=400,
            N_theta=256,
            l_max=8,
            mp_dps=50,
            w_r=constants.a0_sst,
            w_z=constants.a0_sst,
            q=1.0 / constants.a0_sst,
            A_gamma=1.0,
            eps=0.0,
            use_cpp=True,
            N_phi=64,
        )


def gauss_legendre_interval(a: float, b: float, n: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Gauss-Legendre nodes and weights mapped to [a, b].
    Returns (nodes, weights) each of length n.
    """
    if n < 1:
        raise ValueError("n must be >= 1.")
    x, w = roots_legendre(n)
    # map from [-1,1] to [a,b]: node = 0.5*(b-a)*x + 0.5*(a+b), weight *= 0.5*(b-a)
    nodes = 0.5 * (b - a) * x + 0.5 * (a + b)
    weights = 0.5 * (b - a) * w
    return nodes, weights


def allowed_m_for_axisymmetric_probe(h: int, probe_type: str) -> int:
    """
    For axisymmetric probe, the phi integral gives 2π δ_{m, m_allowed}.
    Helical: ∫ exp(i(h-m)φ) dφ → m = h.
    Non-helical: ∫ exp(-i m φ) dφ → m = 0.
    Returns the single allowed m value.
    """
    if probe_type == "non_helical":
        return 0
    return h


def _build_axisymmetric_arrays(
    E_k: float,
    params: BenchmarkParams,
    probe_type: str,
    h: int,
) -> dict[str, Any]:
    """
    Build precomputed grids and arrays for the axisymmetric C++ kernel.
    Python does all physics (Coulomb, hydrogen, probe); C++ does only the 2D quadrature sum.
    Returns dict with radial_continuum_by_l (N_l, N_r), angular_by_l (N_l, N_x), probe_grid (N_r, N_x),
    psi1s_r (N_r), r_nodes, r_weights, x_weights, phi_factor. All arrays C-contiguous complex128 or float64.
    """
    coulomb_continuum.set_coulomb_precision(params.mp_dps)
    m_allowed = allowed_m_for_axisymmetric_probe(h, probe_type)
    l_min = max(1, abs(m_allowed))
    if l_min > params.l_max:
        logger.debug("_build_axisymmetric_arrays: l_min=%d > l_max=%d, skipping", l_min, params.l_max)
        return None
    N_l = params.l_max - l_min + 1
    r_nodes, r_weights = gauss_legendre_interval(0.0, params.R_max, params.N_r)
    logger.debug(
        "_build_axisymmetric_arrays: N_r=%d, N_theta=%d, N_l=%d, m_allowed=%d, probe_type=%s",
        params.N_r, params.N_theta, N_l, m_allowed, probe_type,
    )
    x_nodes, x_w = roots_legendre(params.N_theta)
    theta_nodes = np.arccos(np.clip(x_nodes, -1.0, 1.0))
    N_r = len(r_nodes)
    N_x = len(x_nodes)
    r_ref = float(r_nodes[0]) if r_nodes[0] > 1e-30 else constants.a0_sst

    psi1s_r = np.ascontiguousarray(
        hydrogen.psi_1s(r_nodes).astype(np.complex128),
        dtype=np.complex128,
    )
    # probe_grid[i, j] = gamma_axisymmetric_reduced(r_nodes[i], theta_nodes[j], ...)
    r_2d = r_nodes[:, np.newaxis]
    theta_2d = theta_nodes[np.newaxis, :]
    probe_grid = np.ascontiguousarray(
        helical_probe.gamma_axisymmetric_reduced(
            r_2d, theta_2d, params.q, params.w_r, params.w_z, params.A_gamma
        ).astype(np.complex128),
        dtype=np.complex128,
    )
    radial_continuum_by_l = np.zeros((N_l, N_r), dtype=np.complex128)
    angular_by_l = np.zeros((N_l, N_x), dtype=np.complex128)
    for l_idx, l in enumerate(range(l_min, params.l_max + 1)):
        for i in range(N_r):
            radial_continuum_by_l[l_idx, i] = coulomb_continuum.radial_coulomb(
                E_k, l, float(r_nodes[i]), Z=1, a0=constants.a0_sst
            )
        R_ref = coulomb_continuum.radial_coulomb(E_k, l, r_ref, Z=1, a0=constants.a0_sst)
        for j in range(N_x):
            psi_elm = coulomb_continuum.continuum_wavefunction_spherical(
                r_ref, float(theta_nodes[j]), 0.0, E_k, l, m_allowed
            )
            angular_by_l[l_idx, j] = psi_elm / R_ref if abs(R_ref) > 1e-300 else 0.0
    r_nodes = np.ascontiguousarray(r_nodes, dtype=np.float64)
    r_weights = np.ascontiguousarray(r_weights, dtype=np.float64)
    x_weights = np.ascontiguousarray(x_w, dtype=np.float64)
    phi_factor = 2.0 * np.pi
    return {
        "radial_continuum_by_l": radial_continuum_by_l,
        "angular_by_l": angular_by_l,
        "probe_grid": probe_grid,
        "psi1s_r": psi1s_r,
        "r_nodes": r_nodes,
        "r_weights": r_weights,
        "x_weights": x_weights,
        "phi_factor": phi_factor,
        "N_l": N_l,
    }


def _build_axisymmetric_arrays_for_m(
    E_k: float,
    params: BenchmarkParams,
    m_target: int,
) -> dict[str, Any] | None:
    """
    Build precomputed 2D arrays for a single azimuthal channel m_target.
    Same as _build_axisymmetric_arrays but for one m; used by the multi-harmonic fast path.
    """
    coulomb_continuum.set_coulomb_precision(params.mp_dps)
    l_min = max(1, abs(m_target))
    if l_min > params.l_max:
        return None
    N_l = params.l_max - l_min + 1
    r_nodes, r_weights = gauss_legendre_interval(0.0, params.R_max, params.N_r)
    x_nodes, x_w = roots_legendre(params.N_theta)
    theta_nodes = np.arccos(np.clip(x_nodes, -1.0, 1.0))
    N_r = len(r_nodes)
    N_x = len(x_nodes)
    r_ref = float(r_nodes[0]) if r_nodes[0] > 1e-30 else constants.a0_sst

    psi1s_r = np.ascontiguousarray(
        hydrogen.psi_1s(r_nodes).astype(np.complex128),
        dtype=np.complex128,
    )
    r_2d = r_nodes[:, np.newaxis]
    theta_2d = theta_nodes[np.newaxis, :]
    probe_grid = np.ascontiguousarray(
        helical_probe.gamma_axisymmetric_reduced(
            r_2d, theta_2d, params.q, params.w_r, params.w_z, params.A_gamma
        ).astype(np.complex128),
        dtype=np.complex128,
    )
    radial_continuum_by_l = np.zeros((N_l, N_r), dtype=np.complex128)
    angular_by_l = np.zeros((N_l, N_x), dtype=np.complex128)
    for l_idx, l in enumerate(range(l_min, params.l_max + 1)):
        for i in range(N_r):
            radial_continuum_by_l[l_idx, i] = coulomb_continuum.radial_coulomb(
                E_k, l, float(r_nodes[i]), Z=1, a0=constants.a0_sst
            )
        R_ref = coulomb_continuum.radial_coulomb(E_k, l, r_ref, Z=1, a0=constants.a0_sst)
        for j in range(N_x):
            psi_elm = coulomb_continuum.continuum_wavefunction_spherical(
                r_ref, float(theta_nodes[j]), 0.0, E_k, l, m_target
            )
            angular_by_l[l_idx, j] = psi_elm / R_ref if abs(R_ref) > 1e-300 else 0.0
    r_nodes = np.ascontiguousarray(r_nodes, dtype=np.float64)
    r_weights = np.ascontiguousarray(r_weights, dtype=np.float64)
    x_weights = np.ascontiguousarray(x_w, dtype=np.float64)
    return {
        "radial_continuum_by_l": radial_continuum_by_l,
        "angular_by_l": angular_by_l,
        "probe_grid": probe_grid,
        "psi1s_r": psi1s_r,
        "r_nodes": r_nodes,
        "r_weights": r_weights,
        "x_weights": x_weights,
        "N_l": N_l,
    }


def _compute_channel_rate_axisymmetric_python(data: dict[str, Any]) -> float:
    """
    Compute sum_l |I_l|^2 from prebuilt 2D arrays (raw 2D quadrature, no phi factor).
    Used as Python fallback for multi-harmonic (helical_mode_plus1) path.
    """
    radial = data["radial_continuum_by_l"]
    angular = data["angular_by_l"]
    probe = data["probe_grid"]
    psi1s_r = data["psi1s_r"]
    r_nodes = data["r_nodes"]
    r_weights = data["r_weights"]
    x_weights = data["x_weights"]
    N_l, N_r = radial.shape
    N_x = angular.shape[1]
    total = 0.0
    for l_idx in range(N_l):
        I_l = 0.0 + 0.0j
        for i in range(N_r):
            r = r_nodes[i]
            r2 = r * r
            wr = r_weights[i]
            ps = psi1s_r[i]
            for j in range(N_x):
                conj_RY = np.conj(radial[l_idx, i] * angular[l_idx, j])
                I_l += wr * x_weights[j] * r2 * conj_RY * probe[i, j] * ps
        total += np.abs(I_l) ** 2
    return float(total)


def _build_general_3d_arrays(
    E_k: float,
    params: BenchmarkParams,
    probe_type: str,
    h: int,
    eps: float,
) -> dict[str, Any] | None:
    """
    Build precomputed 3D grids and arrays for the broken-axisymmetry C++ kernel.
    Python evaluates Coulomb, Y_lm, and probe; C++ does the weighted 3D sum.
    Returns dict with radial_continuum_by_lm (N_lm, N_r), angular_by_lm (N_lm, N_theta, N_phi),
    probe_grid (N_r, N_theta, N_phi), psi1s_r, r/theta/phi nodes and weights. All C-contiguous.
    """
    coulomb_continuum.set_coulomb_precision(params.mp_dps)
    N_r = params.N_r
    N_theta = params.N_theta
    N_phi = params.N_phi
    probe_h = 0 if probe_type == "non_helical" else h

    r_nodes, r_weights = gauss_legendre_interval(0.0, params.R_max, N_r)
    theta_nodes, theta_weights = gauss_legendre_interval(0.0, np.pi, N_theta)
    phi_nodes, phi_weights = gauss_legendre_interval(0.0, 2.0 * np.pi, N_phi)

    r_nodes = np.ascontiguousarray(r_nodes, dtype=np.float64)
    r_weights = np.ascontiguousarray(r_weights, dtype=np.float64)
    theta_nodes = np.ascontiguousarray(theta_nodes, dtype=np.float64)
    theta_weights = np.ascontiguousarray(theta_weights, dtype=np.float64)
    phi_nodes = np.ascontiguousarray(phi_nodes, dtype=np.float64)
    phi_weights = np.ascontiguousarray(phi_weights, dtype=np.float64)

    psi1s_r = np.ascontiguousarray(
        hydrogen.psi_1s(r_nodes).astype(np.complex128),
        dtype=np.complex128,
    )

    # (l, m) pairs: l=1..l_max, m=-l..l
    lm_pairs = [(l, m) for l in range(1, params.l_max + 1) for m in range(-l, l + 1)]
    N_lm = len(lm_pairs)

    radial_continuum_by_lm = np.zeros((N_lm, N_r), dtype=np.complex128)
    angular_by_lm = np.zeros((N_lm, N_theta, N_phi), dtype=np.complex128)
    r_ref = float(r_nodes[0]) if r_nodes[0] > 1e-30 else constants.a0_sst

    for lm_idx, (l, m) in enumerate(lm_pairs):
        for i in range(N_r):
            radial_continuum_by_lm[lm_idx, i] = coulomb_continuum.radial_coulomb(
                E_k, l, float(r_nodes[i]), Z=1, a0=constants.a0_sst
            )
        R_ref = coulomb_continuum.radial_coulomb(E_k, l, r_ref, Z=1, a0=constants.a0_sst)
        for j in range(N_theta):
            for k in range(N_phi):
                psi_elm = coulomb_continuum.continuum_wavefunction_spherical(
                    r_ref, float(theta_nodes[j]), float(phi_nodes[k]), E_k, l, m
                )
                angular_by_lm[lm_idx, j, k] = psi_elm / R_ref if abs(R_ref) > 1e-300 else 0.0

    # probe_grid[i, j, k] = gamma_h(r_nodes[i], theta_nodes[j], phi_nodes[k], ...)
    r_3d = r_nodes[:, np.newaxis, np.newaxis]
    th_3d = theta_nodes[np.newaxis, :, np.newaxis]
    phi_3d = phi_nodes[np.newaxis, np.newaxis, :]
    probe_grid = np.ascontiguousarray(
        helical_probe.gamma_h(
            r_3d, th_3d, phi_3d,
            probe_h, params.q, params.w_r, params.w_z, params.A_gamma, eps,
        ).astype(np.complex128),
        dtype=np.complex128,
    )

    return {
        "radial_continuum_by_lm": radial_continuum_by_lm,
        "angular_by_lm": angular_by_lm,
        "probe_grid": probe_grid,
        "psi1s_r": psi1s_r,
        "r_nodes": r_nodes,
        "r_weights": r_weights,
        "theta_nodes": theta_nodes,
        "theta_weights": theta_weights,
        "phi_weights": phi_weights,
        "N_lm": N_lm,
    }


def get_C_h(h: int, use_anticommutator: bool, probe_type: str = "helical") -> float:
    """
    Coupling C_h: full model C_h = -2 + h/2 (so -3/2, -5/2);
    null (no anticommutator) C_h = -2 for both.
    For non_helical control we use the same scalar coupling C = -2 for both channels
    (no helicity discrimination), so both rates are equal by construction.
    helical_mode_plus1 uses the same C_h as helical.
    """
    if probe_type == "non_helical":
        return -2.0
    if probe_type in ("helical", "helical_mode_plus1"):
        if use_anticommutator:
            return -2.0 + 0.5 * h
        return -2.0
    if use_anticommutator:
        return -2.0 + 0.5 * h
    return -2.0


def _integrand_real(
    phi: float, theta: float, r: float,
    E_k: float, l: int, m: int, h: int, params: BenchmarkParams,
    probe_type: str, eps: float,
) -> float:
    """Real part of integrand for general (3D) path: Re(ψ*_Elm γ_h ψ_1s) * r² * sin(theta)."""
    if r <= 0 or r > params.R_max:
        return 0.0
    psi_c = coulomb_continuum.continuum_wavefunction_spherical(r, theta, phi, E_k, l, m)
    probe_h = 0 if probe_type == "non_helical" else h
    gam = helical_probe.gamma_h(r, theta, phi, probe_h, params.q, params.w_r, params.w_z, params.A_gamma, eps)
    p1s = hydrogen.psi_1s(r)
    jac = r ** 2 * np.sin(theta)
    val = np.conj(psi_c) * gam * p1s * jac
    return float(np.real(val))


def _integrand_imag(
    phi: float, theta: float, r: float,
    E_k: float, l: int, m: int, h: int, params: BenchmarkParams,
    probe_type: str, eps: float,
) -> float:
    """Imaginary part of integrand for general (3D) path."""
    if r <= 0 or r > params.R_max:
        return 0.0
    psi_c = coulomb_continuum.continuum_wavefunction_spherical(r, theta, phi, E_k, l, m)
    probe_h = 0 if probe_type == "non_helical" else h
    gam = helical_probe.gamma_h(r, theta, phi, probe_h, params.q, params.w_r, params.w_z, params.A_gamma, eps)
    p1s = hydrogen.psi_1s(r)
    jac = r ** 2 * np.sin(theta)
    val = np.conj(psi_c) * gam * p1s * jac
    return float(np.imag(val))


# One-time log for which path is active (C++ vs Python fallback).
_cpp_path_logged = False
_python_fallback_logged = False
_cpp_3d_path_logged = False


def compute_partial_amplitude_axisymmetric(
    E_k: float,
    l: int,
    m: int,
    h: int,
    params: BenchmarkParams,
    probe_type: str,
    eps: float,
) -> complex:
    """
    Pure-Python 2D (r, theta) quadrature for axisymmetric probe (reference/fallback).
    Used when sst_benchmark_core is not available or use_cpp is False.
    Phi integral done analytically: 2π and m = allowed_m (h for helical, 0 for non_helical).
    Integrand: 2π * conj(R_El Y_lm(θ,0)) * gamma_axisymmetric_reduced(r,θ) * psi_1s(r) * r² sin(θ).
    x = cos(θ), ∫_0^π sin(θ)dθ = ∫_{-1}^1 dx.
    """
    m_allowed = allowed_m_for_axisymmetric_probe(h, probe_type)
    if m != m_allowed:
        return 0.0 + 0.0j
    if abs(m) > l:
        return 0.0 + 0.0j

    coulomb_continuum.set_coulomb_precision(params.mp_dps)
    phi_val = 0.0  # consistent phi for Y_lm after phi integration

    r_nodes, r_w = gauss_legendre_interval(0.0, params.R_max, params.N_r)
    x_nodes, x_w = roots_legendre(params.N_theta)
    # x in [-1,1] -> theta = arccos(x), sin(theta) dtheta = dx
    theta_nodes = np.arccos(np.clip(x_nodes, -1.0, 1.0))

    # Integrand: 2π * conj(ψ_Elm(r,θ,0)) * gamma_axisymmetric_reduced(r,θ) * psi_1s(r) * r².
    # With x = cos(θ), ∫_0^π sin(θ)dθ = ∫_{-1}^1 dx, so we use x_w as weights.
    I = 0.0 + 0.0j
    two_pi = 2.0 * np.pi
    for ir, (r, wr) in enumerate(zip(r_nodes, r_w)):
        if r <= 0:
            continue
        p1s = hydrogen.psi_1s(r)
        gam_red = helical_probe.gamma_axisymmetric_reduced(r, theta_nodes, params.q, params.w_r, params.w_z, params.A_gamma)
        for it, (theta, xw) in enumerate(zip(theta_nodes, x_w)):
            psi_Elm = coulomb_continuum.continuum_wavefunction_spherical(r, theta, phi_val, E_k, l, m)
            val = np.conj(psi_Elm) * gam_red[it] * p1s * (r ** 2)
            I += two_pi * wr * xw * val
    return I


def compute_partial_amplitude_general(
    E_k: float,
    l: int,
    m: int,
    h: int,
    params: BenchmarkParams,
    use_anticommutator: bool,
    probe_type: str,
    eps: float,
) -> complex:
    """
    Slow 3D tplquad fallback for broken axisymmetry (eps != 0).
    The main axisymmetric benchmark never uses this path.
    """
    if abs(m) > l:
        return 0.0 + 0.0j
    coulomb_continuum.set_coulomb_precision(params.mp_dps)

    def re_int(phi: float, theta: float, r: float) -> float:
        return _integrand_real(phi, theta, r, E_k, l, m, h, params, probe_type, eps)

    def im_int(phi: float, theta: float, r: float) -> float:
        return _integrand_imag(phi, theta, r, E_k, l, m, h, params, probe_type, eps)

    I_re, _ = tplquad(re_int, 0, params.R_max, lambda r: 0, lambda r: np.pi, lambda r, t: 0, lambda r, t: 2 * np.pi)
    I_im, _ = tplquad(im_int, 0, params.R_max, lambda r: 0, lambda r: np.pi, lambda r, t: 0, lambda r, t: 2 * np.pi)
    return I_re + 1j * I_im


def compute_partial_amplitude(
    E_k: float,
    l: int,
    m: int,
    h: int,
    params: BenchmarkParams,
    use_anticommutator: bool = True,
    probe_type: str = "helical",
    eps: float | None = None,
) -> complex:
    """
    Compute overlap I_{Elm}^{(h)} = ∫ d³r ψ*_{Elm} γ_h ψ_1s.
    For axisymmetric (eps=0, helical or non_helical): use 2D quadrature and analytic phi → m = h or m = 0.
    Otherwise: use 3D tplquad fallback.
    """
    if E_k <= 0:
        raise ValueError("E_k must be positive.")
    effective_eps = eps if eps is not None else params.eps
    is_axisymmetric = (effective_eps == 0.0 and probe_type in ("helical", "non_helical"))

    if is_axisymmetric:
        return compute_partial_amplitude_axisymmetric(E_k, l, m, h, params, probe_type, effective_eps)
    return compute_partial_amplitude_general(E_k, l, m, h, params, use_anticommutator, probe_type, effective_eps)


def compute_total_rate(
    E_k: float,
    h: int,
    params: BenchmarkParams,
    use_anticommutator: bool = True,
    probe_type: str = "helical",
    eps: float | None = None,
) -> float:
    """
    Total rate Gamma_h ∝ |C_h|² × sum_{l,m} |I_{Elm}^{(h)}|².
    For axisymmetric probe only the allowed m contributes (m=h for helical, m=0 for non_helical).
    When use_cpp and sst_benchmark_core are available, the axisymmetric path uses the C++ kernel;
    otherwise the pure-Python 2D quadrature is used (reference/fallback).
    For non_helical, C = -2 for both channels so both rates are computed and are equal by physics.
    """
    if E_k <= 0:
        raise ValueError("E_k must be positive.")
    effective_eps = eps if eps is not None else params.eps
    is_axisymmetric = (effective_eps == 0.0 and probe_type in ("helical", "non_helical"))
    C = get_C_h(h, use_anticommutator, probe_type)
    probe_h = 0 if probe_type == "non_helical" else h

    # Multi-harmonic fast path: helical_mode_plus1 (one-sided Fourier); uses 2D kernel per channel.
    if probe_type == "helical_mode_plus1":
        components = helical_probe.get_probe_harmonic_components("helical_mode_plus1", h, effective_eps)
        total_raw = 0.0
        two_pi = 2.0 * np.pi
        if params.use_cpp and _CPP_AVAILABLE:
            for m_target, coeff in components:
                data = _build_axisymmetric_arrays_for_m(E_k, params, m_target)
                if data is None:
                    continue
                phi_factor = two_pi * np.complex128(coeff)
                channel_rate = _cpp_core.compute_total_rate_axisymmetric_cpp(
                    data["radial_continuum_by_l"],
                    data["angular_by_l"],
                    data["probe_grid"],
                    data["psi1s_r"],
                    data["r_nodes"],
                    data["r_weights"],
                    data["x_weights"],
                    1.0,
                    phi_factor,
                )
                total_raw += channel_rate
            gamma_out = (C ** 2) * total_raw
            logger.debug(
                "compute_total_rate: E_k=%.4e J, h=%d, probe_type=helical_mode_plus1, eps=%.4f -> multi-harmonic C++ path, Gamma=%.4e",
                E_k, h, effective_eps, gamma_out,
            )
            return gamma_out
        # Python fallback for helical_mode_plus1
        for m_target, coeff in components:
            data = _build_axisymmetric_arrays_for_m(E_k, params, m_target)
            if data is None:
                continue
            channel_sum_sq = _compute_channel_rate_axisymmetric_python(data)
            total_raw += (two_pi * np.abs(coeff)) ** 2 * channel_sum_sq
        gamma_out = (C ** 2) * total_raw
        logger.debug(
            "compute_total_rate: E_k=%.4e J, h=%d, probe_type=helical_mode_plus1, eps=%.4f -> multi-harmonic Python path, Gamma=%.4e",
            E_k, h, effective_eps, gamma_out,
        )
        return gamma_out

    # Axisymmetric fast path: use C++ kernel when available, else Python 2D loop.
    if is_axisymmetric and params.use_cpp and _CPP_AVAILABLE:
        global _cpp_path_logged
        if not _cpp_path_logged:
            _cpp_path_logged = True
            print("SST-71 benchmark: using sst_benchmark_core (C++) for axisymmetric path.")
        data = _build_axisymmetric_arrays(E_k, params, probe_type, h)
        if data is not None and data["N_l"] > 0:
            gamma_out = _cpp_core.compute_total_rate_axisymmetric_cpp(
                data["radial_continuum_by_l"],
                data["angular_by_l"],
                data["probe_grid"],
                data["psi1s_r"],
                data["r_nodes"],
                data["r_weights"],
                data["x_weights"],
                float(C ** 2),
                np.complex128(data["phi_factor"]),
            )
            logger.debug(
                "compute_total_rate: E_k=%.4e J, h=%d, probe_type=%s -> C++ path, Gamma=%.4e",
                E_k, h, probe_type, gamma_out,
            )
            return gamma_out
        # N_l == 0 (e.g. |m_allowed| > l_max): fall through to Python with zero total

    total = 0.0
    if is_axisymmetric:
        # Pure-Python axisymmetric path (reference/fallback when C++ not used).
        global _python_fallback_logged
        if not _python_fallback_logged:
            _python_fallback_logged = True
            print("SST-71 benchmark: using Python fallback for axisymmetric path.")
        m_allowed = allowed_m_for_axisymmetric_probe(h, probe_type)
        for l in range(1, params.l_max + 1):
            if abs(m_allowed) > l:
                continue
            I_lm = compute_partial_amplitude(E_k, l, m_allowed, probe_h, params, use_anticommutator, probe_type, eps)
            total += (np.abs(I_lm) ** 2)
        gamma_out = (C ** 2) * total
        logger.debug(
            "compute_total_rate: E_k=%.4e J, h=%d, probe_type=%s -> Python axisymmetric path (N_r=%d, N_theta=%d), Gamma=%.4e",
            E_k, h, probe_type, params.N_r, params.N_theta, gamma_out,
        )
        return gamma_out
    else:
        # General (3D) path: broken-axisymmetry control. Use C++ kernel when available.
        if (
            params.use_cpp
            and _CPP_AVAILABLE
            and getattr(_cpp_core, "compute_total_rate_3d_cpp", None) is not None
        ):
            global _cpp_3d_path_logged
            if not _cpp_3d_path_logged:
                _cpp_3d_path_logged = True
                print("SST-71 benchmark: using sst_benchmark_core (C++) for 3D (broken-axisymmetry) path.")
            data = _build_general_3d_arrays(E_k, params, probe_type, h, effective_eps)
            if data is not None and data["N_lm"] > 0:
                gamma_out = _cpp_core.compute_total_rate_3d_cpp(
                    data["radial_continuum_by_lm"],
                    data["angular_by_lm"],
                    data["probe_grid"],
                    data["psi1s_r"],
                    data["r_nodes"],
                    data["r_weights"],
                    data["theta_nodes"],
                    data["theta_weights"],
                    data["phi_weights"],
                    float(C ** 2),
                )
                logger.debug(
                    "compute_total_rate: E_k=%.4e J, h=%d, probe_type=%s, eps=%s -> C++ 3D path, Gamma=%.4e",
                    E_k, h, probe_type, effective_eps, gamma_out,
                )
                return gamma_out
        # Python 3D fallback (tplquad per partial wave)
        for l in range(1, params.l_max + 1):
            for m in range(-l, l + 1):
                I_lm = compute_partial_amplitude(E_k, l, m, probe_h, params, use_anticommutator, probe_type, eps)
                total += (np.abs(I_lm) ** 2)
    gamma_out = (C ** 2) * total
    logger.debug(
        "compute_total_rate: E_k=%.4e J, h=%d, probe_type=%s, eps=%s -> general 3D path, Gamma=%.4e",
        E_k, h, probe_type, effective_eps, gamma_out,
    )
    return gamma_out


def compute_asymmetry(
    E_k: float,
    params: BenchmarkParams,
    use_anticommutator: bool = True,
    probe_type: str = "helical",
    eps: float | None = None,
) -> float:
    """
    A_tot = (Gamma_+1 - Gamma_-1) / (Gamma_+1 + Gamma_-1).
    For non_helical both rates are computed (C=-2 for both); asymmetry should be ~0 from the physics.
    """
    Gp = compute_total_rate(E_k, 1, params, use_anticommutator, probe_type, eps)
    Gm = compute_total_rate(E_k, -1, params, use_anticommutator, probe_type, eps)
    s = Gp + Gm
    if s == 0:
        return 0.0
    return (Gp - Gm) / s


def verify_selection_rule(
    E_k: float,
    h: int,
    params: BenchmarkParams,
    l_max: int | None = None,
    probe_type: str = "helical",
    eps: float | None = None,
) -> dict[str, Any]:
    """
    Report partial amplitudes and the analytically expected allowed m.
    For axisymmetric cases, expected_allowed_m is the only contributing m; axisymmetric_exact_rule_used = True.
    """
    if l_max is None:
        l_max = params.l_max
    effective_eps = eps if eps is not None else params.eps
    is_axisymmetric = (effective_eps == 0.0 and probe_type in ("helical", "non_helical"))
    expected_allowed_m = allowed_m_for_axisymmetric_probe(h, probe_type)

    coulomb_continuum.set_coulomb_precision(params.mp_dps)
    probe_h = 0 if probe_type == "non_helical" else h
    results = []
    for l in range(1, l_max + 1):
        for m in range(-l, l + 1):
            I_lm = compute_partial_amplitude(E_k, l, m, probe_h, params, True, probe_type, eps)
            results.append({"l": l, "m": m, "|I_lm|": np.abs(I_lm)})
    return {
        "expected_allowed_m": expected_allowed_m,
        "computed_partial_amplitudes": results,
        "axisymmetric_exact_rule_used": is_axisymmetric,
    }

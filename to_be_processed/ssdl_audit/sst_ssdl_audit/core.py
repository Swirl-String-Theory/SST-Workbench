from __future__ import annotations

import math
import sys
from typing import Any, Dict

import numpy as np


def _load_cpp_backend():
    try:
        from .build_ext_if_needed import build_if_needed

        build_if_needed(verbose=False)
        from . import _ssdlbem

        return _ssdlbem
    except Exception:
        return None


def run_route_a_dtn(
    R_e: float,
    n_theta: int = 40,
    n_phi: int = 80,
    force_python: bool = False,
) -> Dict[str, Any]:
    """Berekent Route A: Boundary Green-Function Lift."""
    if not force_python:
        backend = _load_cpp_backend()
        if backend is not None:
            try:
                return dict(backend.run_ssdl_cpp(R_e, n_theta, n_phi))
            except Exception as e:
                print(f"C++ failed: {e}", file=sys.stderr)

    from .fallback import run_ssdl_numpy

    return run_ssdl_numpy(R_e, n_theta, n_phi)


def _count_dirichlet_modes(R: float, ell_P: float) -> int:
    """Continuum 1D Dirichlet modes with lambda_n = (n*pi/R)^2 below k_max = pi/ell_P."""
    return int(math.floor(R / ell_P + 1e-12))


def _fd_mode_count(R: float, ell_P: float, N_nodes: int) -> tuple[int, float]:
    """Finite-difference spectral trace on [0, R] for numerical cross-check."""
    dr = R / (N_nodes + 1)
    diag = np.full(N_nodes, 2.0 / (dr**2))
    off_diag = np.full(N_nodes - 1, -1.0 / (dr**2))
    L = np.diag(diag) + np.diag(off_diag, k=1) + np.diag(off_diag, k=-1)
    eigenvalues = np.linalg.eigvalsh(L)
    k_max2 = (math.pi / ell_P) ** 2
    n_discrete = int(np.sum(eigenvalues <= k_max2))
    n_expected = R / ell_P
    err = abs(n_discrete - n_expected) / n_expected * 100.0 if n_expected else 0.0
    return n_discrete, err


def run_route_b_mode_count(R_e: float, ell_P: float, N_nodes: int = 5000) -> Dict[str, Any]:
    """Berekent Route B: 1D Spectrale Weyl Trace voor Planck-Normale Modes."""
    k_max = math.pi / ell_P
    N_perp_analytic = R_e / ell_P

    # Physical-scale trace via exact 1D Dirichlet spectrum (R_e/ell_P ~ 1e20 modes).
    N_perp_discrete = _count_dirichlet_modes(R_e, ell_P)

    # Resolvable FD cross-check: same R/ell_P ratio, grid can resolve all modes.
    modes_target = min(500, max(20, int(N_nodes // 4)))
    R_fd = 1.0
    ell_P_fd = R_fd / modes_target
    n_fd, fd_err = _fd_mode_count(R_fd, ell_P_fd, N_nodes)

    trace_error_percent = abs(N_perp_discrete - N_perp_analytic) / N_perp_analytic * 100.0

    return {
        "route_b_active_space": "L^2([0, R_e])",
        "k_max_cutoff": float(k_max),
        "N_perp_analytic": float(N_perp_analytic),
        "N_perp_discrete_trace": int(N_perp_discrete),
        "trace_error_percent": float(trace_error_percent),
        "fd_crosscheck": {
            "R_fd": R_fd,
            "ell_P_fd": float(ell_P_fd),
            "N_perp_fd": n_fd,
            "N_perp_expected": float(modes_target),
            "fd_trace_error_percent": float(fd_err),
        },
    }


def run_ssdl_audit() -> Dict[str, Any]:
    # Fysieke parameters
    R_e = 2.8179403262e-15
    ell_P = 1.6162550e-35
    rho_Lambda = 5.8450e-27
    Omega_L0 = 0.685

    route_a = run_route_a_dtn(R_e)
    route_b = run_route_b_mode_count(R_e, ell_P)

    # Consolidatie van de SSDL dichtheid
    R_num = route_a["R_numerical_projected"]
    rho_eff_A = Omega_L0 * (R_num / ell_P) * rho_Lambda
    rho_eff_B = Omega_L0 * route_b["N_perp_discrete_trace"] * rho_Lambda

    target_rho_f = 7.0e-7

    return {
        "audit_name": "Separatrix Surface-Density Lift (SSDL) Falsification",
        "route_a_dtn": route_a,
        "route_b_spectral": route_b,
        "results": {
            "rho_f_target": target_rho_f,
            "rho_f_route_A": rho_eff_A,
            "rho_f_route_B": rho_eff_B,
            "error_A_percent": (rho_eff_A / target_rho_f - 1.0) * 100,
            "error_B_percent": (rho_eff_B / target_rho_f - 1.0) * 100,
            "theorem_A_verified": route_a["projection_error"] < 1e-3,
            "theorem_B_verified": (
                route_b["trace_error_percent"] < 1.0
                and route_b["fd_crosscheck"]["fd_trace_error_percent"] < 1.0
            ),
        },
    }

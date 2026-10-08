from __future__ import annotations
import numpy as np


def cauchy_population_control(strain_rate: float = 0.37, time: float = 0.8) -> dict:
    """Exact incompressible diagonal strain control.

    u=A x, A=diag(a,-a/2,-a/2), F=exp(A t), det F=1.
    For omega0 parallel to x: omega(t)=F omega0 and A_perp(t)=A0/exp(a t).
    """
    a = float(strain_rate)
    t = float(time)
    F = np.diag([np.exp(a * t), np.exp(-0.5 * a * t), np.exp(-0.5 * a * t)])
    J = float(np.linalg.det(F))
    omega0_nonzero = np.array([1.25, 0.0, 0.0])
    omega0_zero = np.zeros(3)
    omega_nonzero = F @ omega0_nonzero
    omega_zero = F @ omega0_zero
    exact_nonzero = np.array([np.exp(a * t) * omega0_nonzero[0], 0.0, 0.0])
    rel = float(np.linalg.norm(omega_nonzero - exact_nonzero) / max(np.linalg.norm(exact_nonzero), 1e-300))
    zero_abs = float(np.linalg.norm(omega_zero))
    A0 = 0.73
    Aperp = A0 * np.exp(-a * t)
    phi0 = omega0_nonzero[0] * A0
    phit = omega_nonzero[0] * Aperp
    flux_rel = float(abs(phit - phi0) / max(abs(phi0), 1e-300))
    return {
        "strain_rate": a,
        "time": t,
        "F": F.tolist(),
        "det_F": J,
        "jacobian_abs_error": abs(J - 1.0),
        "omega0_nonzero": omega0_nonzero.tolist(),
        "omega_nonzero": omega_nonzero.tolist(),
        "omega0_zero": omega0_zero.tolist(),
        "omega_zero": omega_zero.tolist(),
        "cauchy_relative_error": rel,
        "zero_population_abs_error": zero_abs,
        "nonzero_remains_nonzero": bool(np.linalg.norm(omega_nonzero) > 0),
        "zero_remains_zero": bool(zero_abs == 0.0),
        "flux_initial": float(phi0),
        "flux_final": float(phit),
        "flux_relative_error": flux_rel,
    }

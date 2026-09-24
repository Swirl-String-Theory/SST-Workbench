from __future__ import annotations
import numpy as np
from .geometry import length, resample_closed_curve, centered, segment_stats
from .drive import drive_matrix


def finite_core_velocity_python(X: np.ndarray, bs_strength: float, core_radius_over_ds: float,
                                contact_skip: int = 2) -> np.ndarray:
    """Dimensionless regularized nonlocal vortex-filament surrogate.

    The coefficient `bs_strength` is an opaque dimensionless prefactor in the blind campaign.
    No SST calibration constants are used.
    """
    X = np.asarray(X, dtype=float)
    n = len(X)
    seg = np.roll(X, -1, axis=0) - X
    mid = 0.5*(X + np.roll(X, -1, axis=0))
    mean_ds = float(np.mean(np.linalg.norm(seg, axis=1)))
    core = float(core_radius_over_ds)*mean_ds
    r = X[:, None, :] - mid[None, :, :]
    den = (np.sum(r*r, axis=2) + core*core)**1.5
    cross = np.cross(seg[None, :, :], r)
    ii = np.arange(n)[:, None]
    jj = np.arange(n)[None, :]
    cyc = np.minimum((jj-ii) % n, (ii-jj) % n)
    den = np.where(cyc <= int(contact_skip), np.inf, den)
    return float(bs_strength)/(4.0*np.pi)*np.sum(cross/den[:, :, None], axis=1)


def rhs_python(X: np.ndarray, t: float, cfg: dict, t_origin: float = 0.0) -> np.ndarray:
    vel = finite_core_velocity_python(
        X,
        float(cfg["bs_strength"]),
        float(cfg["core_radius_over_ds"]),
        int(cfg.get("contact_skip", 2)),
    )
    A = drive_matrix(
        t+t_origin,
        float(cfg["omega"]), float(cfg["a1"]), float(cfg["a2"]), float(cfg["phase"]),
        str(cfg["chirality"]), float(cfg["total_time"]), str(cfg.get("envelope", "flat")),
    )
    forced = float(cfg["drive_strength"])*(centered(X) @ A.T)
    return vel + forced


def rk4_step_python(X: np.ndarray, t: float, dt: float, cfg: dict,
                    t_origin: float = 0.0) -> np.ndarray:
    k1 = rhs_python(X, t, cfg, t_origin)
    k2 = rhs_python(X+0.5*dt*k1, t+0.5*dt, cfg, t_origin)
    k3 = rhs_python(X+0.5*dt*k2, t+0.5*dt, cfg, t_origin)
    k4 = rhs_python(X+dt*k3, t+dt, cfg, t_origin)
    return X + (dt/6.0)*(k1+2*k2+2*k3+k4)


def evolve_python(X0: np.ndarray, cfg: dict, duration: float | None = None,
                  t_origin: float = 0.0) -> np.ndarray:
    X = np.array(X0, dtype=float, copy=True)
    if duration is None:
        duration = float(cfg["total_time"])
    steps = max(1, int(np.ceil(float(duration)/float(cfg["dt"]))))
    dt = float(duration)/steps
    t = 0.0
    reparam_every = int(cfg.get("reparam_every", 0))
    for step in range(steps):
        X = rk4_step_python(X, t, dt, cfg, t_origin)
        if reparam_every and (step+1) % reparam_every == 0:
            X = resample_closed_curve(X, len(X))
        if not np.isfinite(X).all():
            raise FloatingPointError("non-finite state")
        t += dt
    return X


def evolve(X0: np.ndarray, cfg: dict, backend: str = "python", duration: float | None = None,
           t_origin: float = 0.0) -> np.ndarray:
    if backend == "python":
        return evolve_python(X0, cfg, duration=duration, t_origin=t_origin)
    if backend == "native":
        if int(cfg.get("reparam_every", 0)) != 0:
            raise ValueError("native v0.2.1 requires reparam_every=0 for parity")
        try:
            from . import _native
        except Exception as e:
            raise RuntimeError("native backend not built") from e
        if duration is None:
            duration = float(cfg["total_time"])
        return _native.evolve(np.asarray(X0, float), float(duration), float(t_origin), cfg)
    raise ValueError(f"unknown backend {backend}")

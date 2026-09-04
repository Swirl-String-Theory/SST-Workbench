from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .constants import RHO_F, GAMMA_CANONICAL
from .geometry import CurveGeometry


@dataclass
class VelocityResult:
    velocity_dimensionless: np.ndarray
    rigid_velocity: np.ndarray
    translation_dimensionless: np.ndarray
    rotation_dimensionless: np.ndarray
    relative_equilibrium_residual: float


@dataclass
class HydroForceResult:
    core_ratio: float
    interaction: str
    local_band: int
    energy_dimensionless: float
    force_density_dimensionless: np.ndarray
    force_density_physical: np.ndarray
    force_density_rms_dimensionless: float
    force_density_rms_N_m: float
    normal_alignment_cosine: float
    fitted_shape_residual: float
    fitted_scale_N: float
    tension_N: np.ndarray
    tension_cv: float
    binormal_leakage: float
    tangential_leakage: float
    relative_equilibrium_residual: float
    translation_m_s: np.ndarray
    rotation_s_inv: np.ndarray


def segment_geometry(points: np.ndarray):
    dx = np.roll(points, -1, axis=0) - points
    mids = 0.5 * (points + np.roll(points, -1, axis=0))
    return mids, dx


def regularized_energy_dimensionless(points: np.ndarray, core: float, interaction: str = "full", local_band: int = 3) -> float:
    mids, dx = segment_geometry(points)
    delta = mids[:, None, :] - mids[None, :, :]
    r2 = np.sum(delta * delta, axis=2)
    kernel = 1.0 / np.sqrt(r2 + core * core)
    dots = dx @ dx.T
    n = len(points)
    ii = np.arange(n)
    direct = np.abs(ii[:, None] - ii[None, :])
    sep = np.minimum(direct, n - direct)
    if interaction == "nonlocal":
        kernel = np.where(sep > local_band, kernel, 0.0)
    elif interaction == "local":
        kernel = np.where(sep <= local_band, kernel, 0.0)
    elif interaction != "full":
        raise ValueError(f"unknown interaction mode {interaction!r}")
    return float(np.sum(dots * kernel))


def regularized_biot_savart_dimensionless(
    points: np.ndarray,
    core: float,
    interaction: str = "full",
    local_band: int = 3,
) -> np.ndarray:
    mids, dx = segment_geometry(points)
    x = points[:, None, :] - mids[None, :, :]
    r2 = np.sum(x * x, axis=2) + core * core
    cross = np.cross(dx[None, :, :], x)
    n = len(points)
    ii = np.arange(n)
    # Observation vertex i is adjacent to segment j when their cyclic index
    # separation is small.  The split is a numerical diagnostic, not a unique
    # physical decomposition.
    direct = np.abs(ii[:, None] - ii[None, :])
    sep = np.minimum(direct, n - direct)
    if interaction == "nonlocal":
        mask = sep > local_band
    elif interaction == "local":
        mask = sep <= local_band
    elif interaction == "full":
        mask = np.ones_like(sep, dtype=bool)
    else:
        raise ValueError(f"unknown interaction mode {interaction!r}")
    kernel = np.where(mask[:, :, None], cross / np.power(r2[:, :, None], 1.5), 0.0)
    return np.sum(kernel, axis=1) / (4.0 * math.pi)


def fit_rigid_velocity(points: np.ndarray, velocity: np.ndarray) -> VelocityResult:
    center = np.mean(points, axis=0)
    r = points - center
    n = len(points)
    A = np.zeros((3 * n, 6), dtype=float)
    y = velocity.reshape(-1)
    for i, (x, yv, z) in enumerate(r):
        A[3 * i:3 * i + 3, :3] = np.eye(3)
        A[3 * i:3 * i + 3, 3:] = np.array([
            [0.0, z, -yv],
            [-z, 0.0, x],
            [yv, -x, 0.0],
        ])
    coeff, *_ = np.linalg.lstsq(A, y, rcond=None)
    rigid = (A @ coeff).reshape(n, 3)
    residual = float(np.linalg.norm(velocity - rigid) / max(np.linalg.norm(velocity), 1e-15))
    return VelocityResult(velocity, rigid, coeff[:3], coeff[3:], residual)


def energy_gradient_dimensionless(
    points: np.ndarray,
    core: float,
    fd_rel: float = 1e-5,
    interaction: str = "full",
    local_band: int = 3,
) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    edge = np.mean(np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1))
    h = max(fd_rel * edge, 1e-9 * max(np.ptp(points, axis=0).max(), 1.0))
    grad = np.empty_like(points)
    for i in range(len(points)):
        for k in range(3):
            plus = points.copy()
            minus = points.copy()
            plus[i, k] += h
            minus[i, k] -= h
            ep = regularized_energy_dimensionless(plus, core, interaction, local_band)
            em = regularized_energy_dimensionless(minus, core, interaction, local_band)
            grad[i, k] = (ep - em) / (2.0 * h)
    return grad


def hydrodynamic_force_test(
    geom: CurveGeometry,
    thickness: float,
    core_ratio: float,
    physical_thickness_m: float,
    rho_f: float = RHO_F,
    gamma: float = GAMMA_CANONICAL,
    fd_rel: float = 1e-5,
    interaction: str = "full",
    local_band: int = 3,
) -> HydroForceResult:
    if thickness <= 0:
        raise ValueError("thickness must be positive")
    if core_ratio <= 0:
        raise ValueError("core_ratio must be positive")
    if physical_thickness_m <= 0:
        raise ValueError("physical_thickness_m must be positive")
    scale_m_per_unit = physical_thickness_m / thickness
    core = core_ratio * thickness
    energy_bar = regularized_energy_dimensionless(geom.points, core, interaction, local_band)
    grad_bar = energy_gradient_dimensionless(geom.points, core, fd_rel, interaction, local_band)
    # Compare the Hamiltonian variational derivative δH/δX with the
    # contact-reaction target -kappa n.  The actual filament velocity is
    # generated by the non-canonical cross-product operator, not by gradient
    # descent; therefore this is deliberately not labelled a dissipative force.
    force_vertex_bar = grad_bar
    force_density_bar = force_vertex_bar / geom.ds

    coefficient_N = rho_f * gamma * gamma / (8.0 * math.pi)
    force_density_phys = coefficient_N / scale_m_per_unit * force_density_bar

    target = -geom.curvature_vectors
    tangential = np.sum(force_density_bar * geom.tangents, axis=1)
    binormal = np.sum(force_density_bar * geom.binormals, axis=1)
    normal = np.sum(force_density_bar * geom.normals, axis=1)
    f_norm = np.linalg.norm(force_density_bar, axis=1)
    target_norm = np.linalg.norm(target, axis=1)
    dot = float(np.sum(force_density_bar * target))
    cosine = dot / max(float(np.linalg.norm(force_density_bar) * np.linalg.norm(target)), 1e-15)
    lam = dot / max(float(np.sum(target * target)), 1e-15)
    fit_res = float(np.linalg.norm(force_density_bar - lam * target) / max(np.linalg.norm(force_density_bar), 1e-15))

    kappa_phys = geom.curvature / scale_m_per_unit
    normal_phys = np.sum(force_density_phys * geom.normals, axis=1)
    tension = np.divide(-normal_phys, kappa_phys, out=np.full_like(normal_phys, np.nan), where=kappa_phys > 1e-15)
    valid_t = np.isfinite(tension) & (np.abs(tension) > 1e-30)
    tension_cv = float(np.std(tension[valid_t]) / max(abs(np.mean(tension[valid_t])), 1e-30)) if np.any(valid_t) else float("inf")
    bin_leak = float(np.linalg.norm(binormal) / max(np.linalg.norm(f_norm), 1e-15))
    tan_leak = float(np.linalg.norm(tangential) / max(np.linalg.norm(f_norm), 1e-15))

    vel_bar = regularized_biot_savart_dimensionless(geom.points, core, interaction, local_band)
    rigid = fit_rigid_velocity(geom.points, vel_bar)
    # Physical BS scale: Gamma / length.
    velocity_scale = gamma / scale_m_per_unit
    translation = rigid.translation_dimensionless * velocity_scale
    rotation = rigid.rotation_dimensionless * gamma / (scale_m_per_unit * scale_m_per_unit)
    fitted_scale_N = lam * coefficient_N
    return HydroForceResult(
        core_ratio=core_ratio,
        interaction=interaction,
        local_band=local_band,
        energy_dimensionless=energy_bar,
        force_density_dimensionless=force_density_bar,
        force_density_physical=force_density_phys,
        force_density_rms_dimensionless=float(np.sqrt(np.mean(np.sum(force_density_bar * force_density_bar, axis=1)))),
        force_density_rms_N_m=float(np.sqrt(np.mean(np.sum(force_density_phys * force_density_phys, axis=1)))),
        normal_alignment_cosine=float(cosine),
        fitted_shape_residual=fit_res,
        fitted_scale_N=float(fitted_scale_N),
        tension_N=tension,
        tension_cv=tension_cv,
        binormal_leakage=bin_leak,
        tangential_leakage=tan_leak,
        relative_equilibrium_residual=rigid.relative_equilibrium_residual,
        translation_m_s=translation,
        rotation_s_inv=rotation,
    )

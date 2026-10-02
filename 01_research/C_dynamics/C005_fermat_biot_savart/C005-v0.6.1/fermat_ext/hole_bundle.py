from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from . import constants
from .core import PACKAGE_VERSION, backend_biot_savart_with_jacobian


@dataclass(frozen=True)
class HoleBundleParameters:
    core_radius_over_rc: float
    return_radius_over_rc: float
    circulation_ratio: float
    axis_origin_over_rc: tuple[float, float, float] = (0.0, 0.0, 0.0)
    axis_direction: tuple[float, float, float] = (0.0, 0.0, 1.0)
    model: str = "smooth_coaxial_return_periodic"

    def validate(self) -> None:
        if self.core_radius_over_rc <= 0:
            raise ValueError("core radius must be positive")
        if self.return_radius_over_rc <= self.core_radius_over_rc:
            raise ValueError("return radius must exceed core radius")
        if not math.isfinite(self.circulation_ratio):
            raise ValueError("circulation ratio must be finite")
        origin = np.asarray(self.axis_origin_over_rc, dtype=float)
        direction = np.asarray(self.axis_direction, dtype=float)
        if origin.shape != (3,) or not np.all(np.isfinite(origin)):
            raise ValueError("axis origin must be a finite 3-vector")
        if direction.shape != (3,) or not np.all(np.isfinite(direction)) or np.linalg.norm(direction) <= 0:
            raise ValueError("axis direction must be a finite nonzero 3-vector")
        if self.model != "smooth_coaxial_return_periodic":
            raise ValueError(f"unsupported model: {self.model}")


@dataclass(frozen=True)
class BundleGridDefinition:
    radius_min: float = 0.06125
    radius_max: float = 8.0
    radius_count: int = 33
    radius_spacing: str = "log"
    circulation_min: float = -8.0
    circulation_max: float = 8.0
    circulation_step: float = 0.25
    radius_anchors: tuple[float, ...] = (0.06125, 0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 4.0, 8.0)
    circulation_anchors: tuple[float, ...] = (-8.0, -4.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 4.0, 8.0)

    def validate(self) -> None:
        if not (0 < self.radius_min <= self.radius_max):
            raise ValueError("radius range must satisfy 0 < min <= max")
        if self.radius_count < 2:
            raise ValueError("radius_count must be at least 2")
        if self.radius_spacing not in {"log", "linear"}:
            raise ValueError("radius_spacing must be log or linear")
        if not self.circulation_min <= self.circulation_max:
            raise ValueError("circulation range must satisfy min <= max")
        if self.circulation_step <= 0 or not math.isfinite(self.circulation_step):
            raise ValueError("circulation_step must be positive and finite")

    def values(self) -> tuple[np.ndarray, np.ndarray]:
        self.validate()
        if self.radius_spacing == "log":
            radii = np.geomspace(self.radius_min, self.radius_max, self.radius_count)
        else:
            radii = np.linspace(self.radius_min, self.radius_max, self.radius_count)
        radii = _merge_anchors(radii, self.radius_anchors, self.radius_min, self.radius_max)

        span = self.circulation_max - self.circulation_min
        n = int(math.floor(span / self.circulation_step + 1e-12))
        gamma = self.circulation_min + self.circulation_step * np.arange(n + 1, dtype=float)
        if gamma[-1] < self.circulation_max - 1e-12:
            gamma = np.append(gamma, self.circulation_max)
        else:
            gamma[-1] = self.circulation_max
        gamma = _merge_anchors(gamma, self.circulation_anchors, self.circulation_min, self.circulation_max)
        # The null bundle is an essential control and must always be sampled.
        if self.circulation_min <= 0 <= self.circulation_max:
            gamma = np.unique(np.append(gamma, 0.0))
        return radii, gamma


def _merge_anchors(values: np.ndarray, anchors: Iterable[float], lo: float, hi: float) -> np.ndarray:
    a = np.asarray([float(x) for x in anchors if lo - 1e-14 <= float(x) <= hi + 1e-14], dtype=float)
    out = np.unique(np.concatenate([np.asarray(values, dtype=float), a, np.array([lo, hi], dtype=float)]))
    out = out[(out >= lo - 1e-14) & (out <= hi + 1e-14)]
    out[0], out[-1] = lo, hi
    return out


def _unit(v: Sequence[float]) -> np.ndarray:
    a = np.asarray(v, float)
    n = float(np.linalg.norm(a))
    if n <= 0 or not math.isfinite(n):
        raise ValueError("axis direction must be finite and nonzero")
    return a / n


def axis_direction_from_tilts(tilt_x_deg: float = 0.0, tilt_y_deg: float = 0.0) -> tuple[float, float, float]:
    """Return R_y(tilt_y) R_x(tilt_x) z-hat as a unit vector."""
    tx = math.radians(float(tilt_x_deg))
    ty = math.radians(float(tilt_y_deg))
    # Rx z = (0,-sin tx,cos tx); then apply Ry.
    v = np.array([math.sin(ty) * math.cos(tx), -math.sin(tx), math.cos(ty) * math.cos(tx)])
    v = _unit(v)
    return tuple(float(x) for x in v)


def _q_and_dq_arrays(r: np.ndarray, rb: float, rr: float) -> tuple[np.ndarray, np.ndarray]:
    """Enclosed-circulation fraction and radial derivative, vectorized."""
    q = np.zeros_like(r, dtype=float)
    dq = np.zeros_like(r, dtype=float)
    core = (r > 0) & (r < rb)
    if np.any(core):
        t = r[core] / rb
        q[core] = 2.0 * t * t - t**4
        dq[core] = (4.0 * t - 4.0 * t**3) / rb
    ret = (r >= rb) & (r < rr)
    if np.any(ret):
        s = (r[ret] - rb) / (rr - rb)
        q[ret] = 1.0 - 3.0 * s * s + 2.0 * s**3
        dq[ret] = (-6.0 * s + 6.0 * s * s) / (rr - rb)
    return q, dq


def bundle_beta_and_jacobian(points: np.ndarray, params: HoleBundleParameters) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate the smooth coaxial bundle field and analytic Cartesian Jacobian.

    The central circulation is exactly cancelled by the return annulus for r >= R_return.
    The model is radially compact and axially periodic; it does not certify a finite closed
    vortex bundle in unbounded space.
    """
    params.validate()
    p = np.asarray(points, float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("points must have shape (M,3)")

    origin = np.asarray(params.axis_origin_over_rc, float)
    ez = _unit(params.axis_direction)
    ref = np.array([1.0, 0.0, 0.0]) if abs(ez[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    ex = ref - np.dot(ref, ez) * ez
    ex /= np.linalg.norm(ex)
    ey = np.cross(ez, ex)
    R = np.column_stack([ex, ey, ez])

    local = (p - origin) @ R
    x = local[:, 0]
    y = local[:, 1]
    r = np.hypot(x, y)
    rb = float(params.core_radius_over_rc)
    rr = float(params.return_radius_over_rc)
    g = float(params.circulation_ratio) * constants.BETA_0
    q, dq = _q_and_dq_arrays(r, rb, rr)

    tiny = r < 1e-14
    A = np.empty_like(r)
    Aprime = np.zeros_like(r)
    A[tiny] = 2.0 * g / (rb * rb)
    regular = ~tiny
    if np.any(regular):
        rg = r[regular]
        A[regular] = g * q[regular] / (rg * rg)
        Aprime[regular] = g * (dq[regular] / (rg * rg) - 2.0 * q[regular] / (rg**3))

    b_local = np.column_stack([-A * y, A * x, np.zeros_like(A)])
    J = np.zeros((len(p), 3, 3), dtype=float)
    J[tiny, 0, 1] = -A[tiny]
    J[tiny, 1, 0] = A[tiny]
    if np.any(regular):
        xr = x[regular] / r[regular]
        yr = y[regular] / r[regular]
        ap = Aprime[regular]
        ar = A[regular]
        xx = x[regular]
        yy = y[regular]
        J[regular, 0, 0] = -yy * ap * xr
        J[regular, 0, 1] = -ar - yy * ap * yr
        J[regular, 1, 0] = ar + xx * ap * xr
        J[regular, 1, 1] = xx * ap * yr

    out = b_local @ R.T
    jac = np.einsum("ab,nbc,dc->nad", R, J, R, optimize=True)
    return out, jac


class RigidMotionProjector:
    """Reusable least-squares projector for U + Omega x (x-xc)."""

    def __init__(self, points: np.ndarray):
        x = np.asarray(points, float)
        if x.ndim != 2 or x.shape[1] != 3:
            raise ValueError("points must have shape (N,3)")
        self.points = x
        self.center = x.mean(axis=0)
        r = x - self.center
        A = np.zeros((3 * len(x), 6), float)
        for i, (rx, ry, rz) in enumerate(r):
            A[3 * i : 3 * i + 3, :3] = np.eye(3)
            A[3 * i : 3 * i + 3, 3:] = np.array(
                [[0.0, rz, -ry], [-rz, 0.0, rx], [ry, -rx, 0.0]], float
            )
        self.design = A
        self.pseudoinverse = np.linalg.pinv(A)

    def fit(self, velocities: np.ndarray, *, include_vectors: bool = False) -> dict[str, Any]:
        u = np.asarray(velocities, float)
        if u.shape != self.points.shape:
            raise ValueError("velocities must match points")
        flat = u.reshape(-1)
        coeff = self.pseudoinverse @ flat
        pred = (self.design @ coeff).reshape(-1, 3)
        res = u - pred
        denom = float(np.linalg.norm(u))
        rel = float(np.linalg.norm(res) / denom) if denom > 0 else 0.0
        out: dict[str, Any] = {
            "translation_beta": coeff[:3].tolist(),
            "angular_rate_dimensionless": coeff[3:].tolist(),
            "relative_shape_residual": rel,
            "residual_norm": float(np.linalg.norm(res)),
            "velocity_norm": denom,
        }
        if include_vectors:
            out["predicted_rigid_velocity"] = pred.tolist()
            out["shape_residual_vectors"] = res.tolist()
        return out

    def residual_vectors(self, velocities: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        u = np.asarray(velocities, float)
        coeff = self.pseudoinverse @ u.reshape(-1)
        pred = (self.design @ coeff).reshape(-1, 3)
        return u - pred, pred, coeff


def make_combined_clock_evaluator(
    curve: np.ndarray,
    *,
    epsilon: float,
    bundle: HoleBundleParameters,
    force_python: bool = False,
    auto_build: bool = True,
    minimum_s2: float = 1e-14,
):
    c = np.asarray(curve, float)
    backend_cache = None

    def evaluate(point: np.ndarray):
        nonlocal backend_cache
        p = np.asarray(point, float).reshape(1, 3)
        kb, kj, backend = backend_biot_savart_with_jacobian(
            c.tolist(),
            p.tolist(),
            epsilon=epsilon,
            force_python=force_python,
            auto_build=auto_build if backend_cache is None else False,
        )
        if backend_cache is None:
            backend_cache = backend
        bb, bj = bundle_beta_and_jacobian(p, bundle)
        b = np.asarray(kb, float)[0] + bb[0]
        j = np.asarray(kj, float)[0] + bj[0]
        s2 = 1.0 - float(np.dot(b, b))
        if not math.isfinite(s2) or s2 <= minimum_s2:
            from .geodesic import ClockDomainError

            raise ClockDomainError(f"combined clock domain violated: S^2={s2!r}")
        s = math.sqrt(s2)
        grad = -(j.T @ b) / s
        return s, grad, {
            "backend": backend_cache,
            "beta": b,
            "jacobian": j,
            "S2": s2,
            "S": s,
            "grad_S": grad,
            "bundle": asdict(bundle),
        }

    return evaluate


def fit_rigid_motion(
    points: np.ndarray,
    velocities: np.ndarray,
    *,
    projector: RigidMotionProjector | None = None,
    include_vectors: bool = False,
) -> dict[str, Any]:
    proj = projector if projector is not None else RigidMotionProjector(points)
    return proj.fit(velocities, include_vectors=include_vectors)


def evaluate_bundle_shape_residual(
    curve: np.ndarray,
    *,
    epsilon: float,
    bundle: HoleBundleParameters | None,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    c = np.asarray(curve, float)
    kb, _kj, backend = backend_biot_savart_with_jacobian(
        c.tolist(), c.tolist(), epsilon=epsilon, force_python=force_python, auto_build=auto_build
    )
    knot = np.asarray(kb, float)
    if bundle is None:
        bg = np.zeros_like(knot)
        params = None
    else:
        bg, _ = bundle_beta_and_jacobian(c, bundle)
        params = asdict(bundle)
    total = knot + bg
    fit = fit_rigid_motion(c, total)
    return {
        "schema": "sst.fermat.hole-bundle-shape-residual.v0.6.1",
        "package_version": PACKAGE_VERSION,
        "bundle": params,
        "backend": backend,
        "fit": fit,
        "knot_beta_rms": float(np.sqrt(np.mean(np.sum(knot * knot, axis=1)))),
        "bundle_beta_rms": float(np.sqrt(np.mean(np.sum(bg * bg, axis=1)))),
        "total_beta_max": float(np.max(np.linalg.norm(total, axis=1))),
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def estimate_axial_hole_radius(curve: np.ndarray, *, quantile: float = 0.02) -> float:
    c = np.asarray(curve, float)
    centered = c - c.mean(axis=0)
    radial = np.linalg.norm(centered[:, :2], axis=1)
    return float(np.quantile(radial, quantile))


def clock_chain(
    bundle: HoleBundleParameters,
    *,
    effective_area_over_rc2: float | None = None,
    reference_omega_over_c_per_rc: float = 1.0,
) -> dict[str, Any]:
    bundle.validate()
    area = (
        effective_area_over_rc2
        if effective_area_over_rc2 is not None
        else math.pi * bundle.core_radius_over_rc**2
    )
    gamma_dimless = 2.0 * math.pi * constants.BETA_0 * bundle.circulation_ratio
    mean_vorticity_dimless = gamma_dimless / area
    angular_rate_dimless = 0.5 * mean_vorticity_dimless
    d_tau_dt = angular_rate_dimless / reference_omega_over_c_per_rc
    return {
        "Gamma_over_c_rc": gamma_dimless,
        "A_eff_over_rc2": area,
        "mean_vorticity_over_c_per_rc": mean_vorticity_dimless,
        "Omega_clock_over_c_per_rc": angular_rate_dimless,
        "reference_omega_over_c_per_rc": reference_omega_over_c_per_rc,
        "d_tau_dt_oriented": d_tau_dt,
        "tick_rate_magnitude": abs(d_tau_dt),
        "orientation_sign": int(np.sign(angular_rate_dimless)),
        "guard": (
            "Omega=zeta/2 is specific to a locally solid-body-like core; tau requires an "
            "independently fixed reference frequency. The circulation sign is orientation, "
            "not negative elapsed proper time."
        ),
    }


def fourier_mode_projection(
    baseline_residual_vectors: np.ndarray,
    bundle_residual_vectors: np.ndarray,
    *,
    max_mode: int = 64,
) -> dict[str, Any]:
    """Project residual vector fields along the closed centerline onto Fourier modes."""
    base = np.asarray(baseline_residual_vectors, float)
    bundled = np.asarray(bundle_residual_vectors, float)
    if base.shape != bundled.shape or base.ndim != 2 or base.shape[1] != 3:
        raise ValueError("residual vector arrays must have equal shape (N,3)")
    fb = np.fft.rfft(base, axis=0) / math.sqrt(len(base))
    ff = np.fft.rfft(bundled, axis=0) / math.sqrt(len(base))
    eb = np.sum(np.abs(fb) ** 2, axis=1)
    ef = np.sum(np.abs(ff) ** 2, axis=1)
    upper = min(int(max_mode), len(eb) - 1)
    rows = []
    for m in range(upper + 1):
        gain = 1.0 - float(ef[m] / eb[m]) if eb[m] > 0 else None
        rows.append(
            {
                "mode": m,
                "baseline_energy": float(eb[m]),
                "bundle_energy": float(ef[m]),
                "mode_energy_gain": gain,
            }
        )
    ranked_reductions = sorted(
        (r for r in rows[1:] if r["mode_energy_gain"] is not None),
        key=lambda r: r["baseline_energy"] - r["bundle_energy"],
        reverse=True,
    )
    ranked_increases = sorted(
        (r for r in rows[1:] if r["mode_energy_gain"] is not None),
        key=lambda r: r["bundle_energy"] - r["baseline_energy"],
        reverse=True,
    )
    return {
        "schema": "sst.fermat.hole-bundle-mode-projection.v0.6.1",
        "package_version": PACKAGE_VERSION,
        "normalization": "orthonormal discrete rFFT along centerline sample index",
        "max_mode_reported": upper,
        "rows": rows,
        "largest_absolute_reductions": ranked_reductions[:10],
        "largest_absolute_increases": ranked_increases[:10],
        "guard": (
            "Fourier index is a centerline diagnostic, not yet a normal-mode eigenlabel of "
            "the coupled finite-core dynamical operator."
        ),
    }

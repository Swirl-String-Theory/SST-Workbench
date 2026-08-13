"""Shared numerical utilities for the SST Hopf benchmark scripts.

The functions in this module implement mathematical diagnostics. They do not
constitute an independent derivation of SST dynamics, quantum spin, or the
electron. Every script writes explicit gate status and epistemic metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence
import hashlib
import json
import math
import platform
import sys
from importlib import metadata as importlib_metadata

import numpy as np

EPS = np.finfo(float).eps


@dataclass(frozen=True)
class CartesianGrid:
    n: int
    extent: float
    spacing: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_cartesian_grid(n: int, extent: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, CartesianGrid]:
    if n < 8:
        raise ValueError("n must be >= 8")
    if not np.isfinite(extent) or extent <= 0:
        raise ValueError("extent must be finite and > 0")
    axis = np.linspace(-extent, extent, n, dtype=np.float64)
    spacing = float(axis[1] - axis[0])
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    return x, y, z, CartesianGrid(n=n, extent=float(extent), spacing=spacing)


def canonical_array_sha256(array: np.ndarray) -> str:
    """Hash an ndarray with explicit little-endian canonical numeric storage."""
    arr = np.asarray(array)
    if np.iscomplexobj(arr):
        canon = np.ascontiguousarray(arr.astype("<c16", copy=False))
        dtype = "complex128-le"
    elif np.issubdtype(arr.dtype, np.floating):
        canon = np.ascontiguousarray(arr.astype("<f8", copy=False))
        dtype = "float64-le"
    elif np.issubdtype(arr.dtype, np.integer):
        canon = np.ascontiguousarray(arr.astype("<i8", copy=False))
        dtype = "int64-le"
    else:
        raise TypeError(f"Unsupported array dtype for canonical hashing: {arr.dtype}")
    h = hashlib.sha256()
    header = json.dumps({"shape": canon.shape, "dtype": dtype}, sort_keys=True).encode("utf-8")
    h.update(header)
    h.update(b"\0")
    h.update(canon.tobytes(order="C"))
    return h.hexdigest()


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_dump(path: str | Path, payload: dict[str, Any]) -> None:
    """Write standards-compliant JSON; reject non-finite values."""
    def convert(value: Any) -> Any:
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"Non-finite JSON value: {value!r}")
            return value
        if isinstance(value, complex):
            if not (math.isfinite(value.real) and math.isfinite(value.imag)):
                raise ValueError("Non-finite complex JSON value")
            return {"real": value.real, "imag": value.imag}
        if isinstance(value, np.ndarray):
            return convert(value.tolist())
        if isinstance(value, dict):
            return {str(k): convert(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [convert(v) for v in value]
        return value

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(convert(payload), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def gate_record(
    gate: str,
    status: str,
    epistemic_class: str,
    residuals: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    notes: Sequence[str] | None = None,
    input_sha256: str = "",
) -> dict[str, Any]:
    if status not in {"PASS", "FAIL", "INDETERMINATE", "DEMONSTRATION"}:
        raise ValueError(f"Invalid gate status: {status}")
    return {
        "gate": gate,
        "status": status,
        "epistemic_class": epistemic_class,
        "parameters": parameters or {},
        "residuals": residuals,
        "input_sha256": input_sha256,
        "notes": list(notes or []),
    }


def normalize_spinor(phi: np.ndarray, epsilon: float = 1e-14) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    phi = np.asarray(phi, dtype=np.complex128)
    if phi.shape[-1] != 2:
        raise ValueError("Spinor array must have final dimension 2")
    norm2 = np.sum(np.abs(phi) ** 2, axis=-1)
    defects = norm2 <= epsilon
    safe = np.where(defects, 1.0, norm2)
    psi = phi / np.sqrt(safe)[..., None]
    psi[defects] = 0.0
    return psi, norm2, defects


def hopf_map(psi: np.ndarray) -> np.ndarray:
    psi = np.asarray(psi, dtype=np.complex128)
    p1, p2 = psi[..., 0], psi[..., 1]
    return np.stack(
        [
            2.0 * np.real(np.conj(p1) * p2),
            2.0 * np.imag(np.conj(p1) * p2),
            np.abs(p1) ** 2 - np.abs(p2) ** 2,
        ],
        axis=-1,
    )


def spinor_norm_residual(psi: np.ndarray) -> float:
    return float(np.max(np.abs(np.sum(np.abs(psi) ** 2, axis=-1) - 1.0)))


def director_norm_residual(n_field: np.ndarray) -> float:
    return float(np.max(np.abs(np.sum(np.asarray(n_field) ** 2, axis=-1) - 1.0)))


def derivative(field: np.ndarray, spacing: float, axis: int) -> np.ndarray:
    return np.gradient(field, spacing, axis=axis, edge_order=2)


def derivative_fourth_order(field: np.ndarray, spacing: float, axis: int) -> np.ndarray:
    """Fourth-order centered derivative in the interior, edge-order-2 near boundaries."""
    arr = np.asarray(field)
    if arr.shape[axis] < 5:
        return derivative(arr, spacing, axis)
    moved = np.moveaxis(arr, axis, 0)
    out = np.asarray(np.gradient(moved, spacing, axis=0, edge_order=2))
    out[2:-2] = (
        -moved[4:]
        + 8.0 * moved[3:-1]
        - 8.0 * moved[1:-3]
        + moved[:-4]
    ) / (12.0 * spacing)
    return np.moveaxis(out, 0, axis)


def connection_from_spinor(psi: np.ndarray, spacing: float) -> np.ndarray:
    components: list[np.ndarray] = []
    for axis in range(3):
        dpsi = np.stack([derivative(psi[..., c], spacing, axis) for c in range(2)], axis=-1)
        components.append(np.real(-1j * np.sum(np.conj(psi) * dpsi, axis=-1)))
    return np.stack(components, axis=-1)


def curl(field: np.ndarray, spacing: float) -> np.ndarray:
    field = np.asarray(field)
    if field.shape[-1] != 3:
        raise ValueError("Vector field must have final dimension 3")
    bx = derivative(field[..., 2], spacing, 1) - derivative(field[..., 1], spacing, 2)
    by = derivative(field[..., 0], spacing, 2) - derivative(field[..., 2], spacing, 0)
    bz = derivative(field[..., 1], spacing, 0) - derivative(field[..., 0], spacing, 1)
    return np.stack([bx, by, bz], axis=-1)


def divergence(field: np.ndarray, spacing: float) -> np.ndarray:
    return sum(derivative(field[..., axis], spacing, axis) for axis in range(3))


def _director_curvature_with_derivative(
    n_field: np.ndarray,
    spacing: float,
    derivative_fn,
) -> np.ndarray:
    n_field = np.asarray(n_field, dtype=np.float64)
    dn = [
        np.stack([derivative_fn(n_field[..., c], spacing, axis) for c in range(3)], axis=-1)
        for axis in range(3)
    ]

    def triple(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.sum(n_field * np.cross(a, b), axis=-1)

    return np.stack(
        [
            0.5 * triple(dn[1], dn[2]),
            0.5 * triple(dn[2], dn[0]),
            0.5 * triple(dn[0], dn[1]),
        ],
        axis=-1,
    )


def director_curvature_b(n_field: np.ndarray, spacing: float) -> np.ndarray:
    """Second-order director curvature retained for regression/parity."""
    return _director_curvature_with_derivative(n_field, spacing, derivative)


def director_curvature_b_fourth_order(n_field: np.ndarray, spacing: float) -> np.ndarray:
    """Higher-accuracy director curvature for H1/H3 certification runs."""
    return _director_curvature_with_derivative(n_field, spacing, derivative_fourth_order)


def hodge_project_divergence_free(
    b_field: np.ndarray,
    spacing: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Periodic FFT Helmholtz/Hodge projection B = B_perp + B_long.

    The k=0 mode is retained in B_perp because it is divergence-free.
    Returns (B_perp, B_longitudinal, ||B_long||_2/||B||_2).
    """
    b_field = np.asarray(b_field, dtype=np.float64)
    if b_field.ndim != 4 or b_field.shape[-1] != 3:
        raise ValueError("b_field must have shape (nx, ny, nz, 3)")
    nx, ny, nz, _ = b_field.shape
    kx = 2.0 * np.pi * np.fft.fftfreq(nx, d=spacing)
    ky = 2.0 * np.pi * np.fft.fftfreq(ny, d=spacing)
    kz = 2.0 * np.pi * np.fft.fftfreq(nz, d=spacing)
    k = np.stack(np.meshgrid(kx, ky, kz, indexing="ij"), axis=-1)
    k2 = np.sum(k * k, axis=-1)

    b_hat = np.stack([np.fft.fftn(b_field[..., c]) for c in range(3)], axis=-1)
    kdotb = np.sum(k * b_hat, axis=-1)
    long_hat = np.zeros_like(b_hat)
    mask = k2 > 0.0
    long_hat[mask] = k[mask] * (kdotb[mask] / k2[mask])[:, None]
    perp_hat = b_hat - long_hat
    perp_hat[~mask] = b_hat[~mask]
    long_hat[~mask] = 0.0

    b_perp = np.stack([np.fft.ifftn(perp_hat[..., c]).real for c in range(3)], axis=-1)
    b_long = b_field - b_perp
    delta_longitudinal = relative_l2(b_long, b_field)
    return b_perp, b_long, float(delta_longitudinal)


def reconstruct_coulomb_connection(b_field: np.ndarray, spacing: float) -> np.ndarray:
    """Periodic FFT reconstruction A_k=i k×B_k/|k|² with A_0=0."""
    b_field = np.asarray(b_field, dtype=np.float64)
    nx, ny, nz, _ = b_field.shape
    kx = 2.0 * np.pi * np.fft.fftfreq(nx, d=spacing)
    ky = 2.0 * np.pi * np.fft.fftfreq(ny, d=spacing)
    kz = 2.0 * np.pi * np.fft.fftfreq(nz, d=spacing)
    k_x, k_y, k_z = np.meshgrid(kx, ky, kz, indexing="ij")
    k = np.stack([k_x, k_y, k_z], axis=-1)
    k2 = np.sum(k * k, axis=-1)
    b_hat = np.stack([np.fft.fftn(b_field[..., c]) for c in range(3)], axis=-1)
    a_hat = 1j * np.cross(k, b_hat)
    mask = k2 > 0
    a_hat[mask] /= k2[mask, None]
    a_hat[~mask] = 0.0
    a = np.stack([np.fft.ifftn(a_hat[..., c]).real for c in range(3)], axis=-1)
    return a


def integrate_scalar(field: np.ndarray, spacing: float) -> float:
    return float(np.sum(field, dtype=np.float64) * spacing ** 3)


def hopf_charge(a_field: np.ndarray, b_field: np.ndarray, spacing: float) -> float:
    density = np.sum(np.asarray(a_field) * np.asarray(b_field), axis=-1)
    return integrate_scalar(density, spacing) / (4.0 * np.pi ** 2)


def relative_l2(numerator: np.ndarray, denominator_reference: np.ndarray, epsilon: float = 1e-15) -> float:
    num = float(np.linalg.norm(np.ravel(numerator)))
    den = float(np.linalg.norm(np.ravel(denominator_reference))) + epsilon
    return num / den


def analytic_hopf_spinor(x: np.ndarray, y: np.ndarray, z: np.ndarray, scale: float = 1.0) -> np.ndarray:
    if scale <= 0:
        raise ValueError("scale must be > 0")
    xs, ys, zs = x / scale, y / scale, z / scale
    r2 = xs * xs + ys * ys + zs * zs
    den = 1.0 + r2
    z1 = 2.0 * (xs + 1j * ys) / den
    z2 = (2.0 * zs + 1j * (r2 - 1.0)) / den
    return np.stack([z1, z2], axis=-1)


def representative_spinor(n_vector: Sequence[float]) -> np.ndarray:
    n = np.asarray(n_vector, dtype=float)
    norm = np.linalg.norm(n)
    if norm == 0:
        raise ValueError("n_vector must be nonzero")
    n /= norm
    theta = math.acos(float(np.clip(n[2], -1.0, 1.0)))
    phi = math.atan2(float(n[1]), float(n[0]))
    return np.array([math.cos(theta / 2.0), np.exp(1j * phi) * math.sin(theta / 2.0)], dtype=np.complex128)


def hopf_fiber_curve(n_vector: Sequence[float], samples: int = 600) -> np.ndarray:
    """Analytic Hopf fiber, stereographically projected from S³ to R³."""
    psi0 = representative_spinor(n_vector)
    chi = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    z = np.exp(1j * chi)[:, None] * psi0[None, :]
    u1, u2 = np.real(z[:, 0]), np.imag(z[:, 0])
    u3, u4 = np.real(z[:, 1]), np.imag(z[:, 1])
    denominator = 1.0 - u4
    if np.any(np.abs(denominator) < 1e-10):
        raise ValueError("Chosen fiber passes too close to stereographic projection point")
    return np.stack([u1 / denominator, u2 / denominator, u3 / denominator], axis=-1)


def gauss_linking_number(curve_a: np.ndarray, curve_b: np.ndarray, epsilon: float = 1e-14) -> float:
    """Midpoint discretization of the Gauss linking integral for closed curves."""
    a = np.asarray(curve_a, dtype=np.float64)
    b = np.asarray(curve_b, dtype=np.float64)
    da = np.roll(a, -1, axis=0) - a
    db = np.roll(b, -1, axis=0) - b
    ma = 0.5 * (a + np.roll(a, -1, axis=0))
    mb = 0.5 * (b + np.roll(b, -1, axis=0))
    total = 0.0
    for i in range(len(a)):
        diff = ma[i][None, :] - mb
        distance = np.linalg.norm(diff, axis=1)
        valid = distance > epsilon
        cross = np.cross(da[i][None, :], db)
        total += float(np.sum(np.einsum("ij,ij->i", cross[valid], diff[valid]) / distance[valid] ** 3))
    return total / (4.0 * np.pi)


def smoothstep01(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def circular_toroflux_spinor(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    major_radius: float,
    tube_radius: float,
    m: int,
    n: int,
    profile_orientation: str = "regularized",
) -> tuple[np.ndarray, dict[str, np.ndarray | str]]:
    """Construct a Cartesian circular-torus spinor ansatz.

    regularized: beta(0)=0, beta(out)=pi; the phi-dependent component vanishes
    on the core and the director is constant outside the tube.

    source: reproduces the profile orientation written in the design document
    (beta(0)=pi, beta(out)=0). For n!=0 the axis is not smooth; this is flagged.
    """
    radial = np.sqrt(x * x + y * y)
    s = np.arctan2(y, x)
    q = radial - major_radius
    rho = np.sqrt(q * q + z * z)
    phi = np.arctan2(z, q)
    t = smoothstep01(rho / tube_radius)
    if profile_orientation == "regularized":
        beta = np.pi * t
        psi1 = np.cos(beta / 2.0) * np.exp(1j * m * s)
        psi2 = np.sin(beta / 2.0) * np.exp(1j * n * phi)
        warning = ""
    elif profile_orientation == "source":
        beta = np.pi * (1.0 - t)
        psi1 = np.cos(beta / 2.0) * np.exp(1j * m * s)
        psi2 = np.sin(beta / 2.0) * np.exp(1j * n * phi)
        warning = "Source profile is axis-singular for n != 0 because phi is undefined where rho=0 and psi2 remains nonzero."
    else:
        raise ValueError("profile_orientation must be 'regularized' or 'source'")
    psi = np.stack([psi1, psi2], axis=-1)
    psi, _, defects = normalize_spinor(psi)
    return psi, {"s": s, "rho": rho, "phi": phi, "beta": beta, "defects": defects, "warning": warning}


def su2_rotation(axis: Sequence[float], angle: float) -> np.ndarray:
    axis_arr = np.asarray(axis, dtype=float)
    axis_arr /= np.linalg.norm(axis_arr)
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    generator = axis_arr[0] * sx + axis_arr[1] * sy + axis_arr[2] * sz
    return math.cos(angle / 2.0) * np.eye(2, dtype=np.complex128) - 1j * math.sin(angle / 2.0) * generator


def ray_distance(psi_a: np.ndarray, psi_b: np.ndarray) -> float:
    overlap = abs(np.vdot(psi_a, psi_b))
    overlap = min(1.0, max(0.0, float(overlap)))
    return math.sqrt(max(0.0, 2.0 - 2.0 * overlap))


def torus_knot_centerline(p: int = 2, q: int = 3, samples: int = 400, major_radius: float = 2.0, minor_radius: float = 0.7) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    radial = major_radius + minor_radius * np.cos(q * t)
    return np.stack(
        [radial * np.cos(p * t), radial * np.sin(p * t), minor_radius * np.sin(q * t)],
        axis=-1,
    )


def unit_tangents(curve: np.ndarray) -> np.ndarray:
    d = np.roll(curve, -1, axis=0) - np.roll(curve, 1, axis=0)
    norms = np.linalg.norm(d, axis=1)
    if np.any(norms <= 0):
        raise ValueError("Degenerate centerline segment")
    return d / norms[:, None]


def bishop_frame(curve: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Discrete parallel-transport frame around a closed sampled curve."""
    t = unit_tangents(curve)
    reference = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(reference, t[0])) > 0.9:
        reference = np.array([1.0, 0.0, 0.0])
    e1 = np.zeros_like(t)
    e2 = np.zeros_like(t)
    e1[0] = reference - np.dot(reference, t[0]) * t[0]
    e1[0] /= np.linalg.norm(e1[0])
    e2[0] = np.cross(t[0], e1[0])
    for i in range(1, len(curve)):
        candidate = e1[i - 1] - np.dot(e1[i - 1], t[i]) * t[i]
        norm = np.linalg.norm(candidate)
        if norm < 1e-12:
            candidate = e2[i - 1] - np.dot(e2[i - 1], t[i]) * t[i]
            norm = np.linalg.norm(candidate)
        e1[i] = candidate / norm
        e2[i] = np.cross(t[i], e1[i])
    return t, e1, e2


def structured_tube_spinor(
    curve: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
    radial_samples: int,
    angular_samples: int,
    tube_radius: float,
    m: int,
    n: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rho = np.linspace(0.0, tube_radius, radial_samples)
    phi = np.linspace(0.0, 2.0 * np.pi, angular_samples, endpoint=False)
    s_phase = np.linspace(0.0, 2.0 * np.pi, len(curve), endpoint=False)
    positions = np.empty((len(curve), radial_samples, angular_samples, 3), dtype=float)
    psi = np.empty((len(curve), radial_samples, angular_samples, 2), dtype=np.complex128)
    for i in range(len(curve)):
        for j, r in enumerate(rho):
            beta = np.pi * smoothstep01(np.array(r / tube_radius)).item()
            for k, angle in enumerate(phi):
                positions[i, j, k] = curve[i] + r * math.cos(angle) * e1[i] + r * math.sin(angle) * e2[i]
                psi[i, j, k, 0] = math.cos(beta / 2.0) * np.exp(1j * m * s_phase[i])
                psi[i, j, k, 1] = math.sin(beta / 2.0) * np.exp(1j * n * angle)
    return positions, psi, hopf_map(psi)


def polygonal_writhe(curve: np.ndarray, neighbor_exclusion: int = 2) -> float:
    """Midpoint Gauss self-link integral, excluding local neighboring segments."""
    c = np.asarray(curve, dtype=float)
    dc = np.roll(c, -1, axis=0) - c
    mid = 0.5 * (c + np.roll(c, -1, axis=0))
    n = len(c)
    total = 0.0
    for i in range(n):
        j = np.arange(i + 1, n)
        cyclic_distance = np.minimum(j - i, n - (j - i))
        valid_idx = j[cyclic_distance > neighbor_exclusion]
        if len(valid_idx) == 0:
            continue
        diff = mid[i][None, :] - mid[valid_idx]
        distance = np.linalg.norm(diff, axis=1)
        good = distance > 1e-14
        cross = np.cross(dc[i][None, :], dc[valid_idx])
        total += float(np.sum(np.einsum("ij,ij->i", cross[good], diff[good]) / distance[good] ** 3))
    return total / (2.0 * np.pi)


def frame_twist(tangent: np.ndarray, e1: np.ndarray) -> float:
    """Discrete rotation of the material normal around the tangent."""
    total = 0.0
    n = len(tangent)
    for i in range(n):
        j = (i + 1) % n
        transported = e1[i] - np.dot(e1[i], tangent[j]) * tangent[j]
        norm = np.linalg.norm(transported)
        if norm < 1e-14:
            continue
        transported /= norm
        target = e1[j] - np.dot(e1[j], tangent[j]) * tangent[j]
        target /= np.linalg.norm(target)
        sin_angle = np.dot(tangent[j], np.cross(transported, target))
        cos_angle = np.clip(np.dot(transported, target), -1.0, 1.0)
        total += math.atan2(float(sin_angle), float(cos_angle))
    return total / (2.0 * np.pi)

# ---------------------------------------------------------------------------
# Optional C++17/pybind11 acceleration layer (template-compatible).
# Set SST_HOPF_FORCE_PYTHON=1 to keep the original NumPy/Python reference path.
# ---------------------------------------------------------------------------
import os as _os

_NATIVE_BACKEND = None
_NATIVE_ATTEMPTED = False


def _get_native_backend():
    global _NATIVE_BACKEND, _NATIVE_ATTEMPTED
    if _os.environ.get("SST_HOPF_FORCE_PYTHON", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        return None
    if _NATIVE_ATTEMPTED:
        return _NATIVE_BACKEND
    _NATIVE_ATTEMPTED = True
    try:
        from sst_hopf_native import load_native
        _NATIVE_BACKEND = load_native(
            force_build=_os.environ.get("SST_HOPF_FORCE_BUILD", "") == "1",
            verbose=_os.environ.get("SST_HOPF_BUILD_VERBOSE", "") == "1",
        )
    except Exception:
        _NATIVE_BACKEND = None
    return _NATIVE_BACKEND


def backend_info() -> dict[str, Any]:
    mod = _get_native_backend()
    if mod is None:
        return {"backend": "python", "version": "0.1.4", "openmp": False, "threads": 1}
    return dict(mod.backend_info())


# Save the untouched reference implementations for parity testing.
_PYTHON_REFERENCE = {
    "normalize_spinor": normalize_spinor,
    "hopf_map": hopf_map,
    "spinor_norm_residual": spinor_norm_residual,
    "director_norm_residual": director_norm_residual,
    "connection_from_spinor": connection_from_spinor,
    "curl": curl,
    "divergence": divergence,
    "director_curvature_b": director_curvature_b,
    "director_curvature_b_fourth_order": director_curvature_b_fourth_order,
    "hopf_charge": hopf_charge,
    "relative_l2": relative_l2,
    "analytic_hopf_spinor": analytic_hopf_spinor,
    "gauss_linking_number": gauss_linking_number,
    "su2_rotation": su2_rotation,
    "torus_knot_centerline": torus_knot_centerline,
    "bishop_frame": bishop_frame,
    "structured_tube_spinor": structured_tube_spinor,
    "polygonal_writhe": polygonal_writhe,
    "frame_twist": frame_twist,
}


def normalize_spinor(phi: np.ndarray, epsilon: float = 1e-14):
    mod = _get_native_backend()
    if mod is not None:
        return mod.normalize_spinor(np.ascontiguousarray(phi, dtype=np.complex128), epsilon)
    return _PYTHON_REFERENCE["normalize_spinor"](phi, epsilon)


def hopf_map(psi: np.ndarray) -> np.ndarray:
    mod = _get_native_backend()
    if mod is not None:
        return mod.hopf_map(np.ascontiguousarray(psi, dtype=np.complex128))
    return _PYTHON_REFERENCE["hopf_map"](psi)


def spinor_norm_residual(psi: np.ndarray) -> float:
    mod = _get_native_backend()
    if mod is not None and np.asarray(psi).shape[-1] == 2:
        return float(mod.spinor_norm_residual(np.ascontiguousarray(psi, dtype=np.complex128)))
    return _PYTHON_REFERENCE["spinor_norm_residual"](psi)


def director_norm_residual(n_field: np.ndarray) -> float:
    mod = _get_native_backend()
    if mod is not None and np.asarray(n_field).shape[-1] == 3:
        return float(mod.director_norm_residual(np.ascontiguousarray(n_field, dtype=np.float64)))
    return _PYTHON_REFERENCE["director_norm_residual"](n_field)


def analytic_hopf_spinor(x: np.ndarray, y: np.ndarray, z: np.ndarray, scale: float = 1.0) -> np.ndarray:
    mod = _get_native_backend()
    if mod is not None:
        return mod.analytic_hopf_spinor(
            np.ascontiguousarray(x, dtype=np.float64),
            np.ascontiguousarray(y, dtype=np.float64),
            np.ascontiguousarray(z, dtype=np.float64),
            scale,
        )
    return _PYTHON_REFERENCE["analytic_hopf_spinor"](x, y, z, scale)


def connection_from_spinor(psi: np.ndarray, spacing: float) -> np.ndarray:
    mod = _get_native_backend()
    arr = np.asarray(psi)
    if mod is not None and arr.ndim == 4 and arr.shape[-1] == 2:
        return mod.connection_from_spinor(np.ascontiguousarray(arr, dtype=np.complex128), spacing)
    return _PYTHON_REFERENCE["connection_from_spinor"](psi, spacing)


def curl(field: np.ndarray, spacing: float) -> np.ndarray:
    mod = _get_native_backend()
    arr = np.asarray(field)
    if mod is not None and arr.ndim == 4 and arr.shape[-1] == 3:
        return mod.curl(np.ascontiguousarray(arr, dtype=np.float64), spacing)
    return _PYTHON_REFERENCE["curl"](field, spacing)


def divergence(field: np.ndarray, spacing: float) -> np.ndarray:
    mod = _get_native_backend()
    arr = np.asarray(field)
    if mod is not None and arr.ndim == 4 and arr.shape[-1] == 3:
        return mod.divergence(np.ascontiguousarray(arr, dtype=np.float64), spacing)
    return _PYTHON_REFERENCE["divergence"](field, spacing)


def director_curvature_b(n_field: np.ndarray, spacing: float) -> np.ndarray:
    mod = _get_native_backend()
    arr = np.asarray(n_field)
    if mod is not None and arr.ndim == 4 and arr.shape[-1] == 3:
        return mod.director_curvature_b(np.ascontiguousarray(arr, dtype=np.float64), spacing)
    return _PYTHON_REFERENCE["director_curvature_b"](n_field, spacing)


def director_curvature_b_fourth_order(n_field: np.ndarray, spacing: float) -> np.ndarray:
    mod = _get_native_backend()
    arr = np.asarray(n_field)
    if mod is not None and arr.ndim == 4 and arr.shape[-1] == 3 and hasattr(mod, "director_curvature_b_fourth_order"):
        return mod.director_curvature_b_fourth_order(np.ascontiguousarray(arr, dtype=np.float64), spacing)
    return _PYTHON_REFERENCE["director_curvature_b_fourth_order"](n_field, spacing)


def runtime_provenance() -> dict[str, Any]:
    def version_of(name: str) -> str:
        try:
            return importlib_metadata.version(name)
        except Exception:
            return "unavailable"

    info = dict(backend_info())
    info.update({
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy_version": np.__version__,
        "pybind11_version": version_of("pybind11"),
        "setuptools_version": version_of("setuptools"),
        "wheel_version": version_of("wheel"),
    })
    return info


def hopf_charge(a_field: np.ndarray, b_field: np.ndarray, spacing: float) -> float:
    mod = _get_native_backend()
    if mod is not None:
        return float(mod.hopf_charge(
            np.ascontiguousarray(a_field, dtype=np.float64),
            np.ascontiguousarray(b_field, dtype=np.float64),
            spacing,
        ))
    return _PYTHON_REFERENCE["hopf_charge"](a_field, b_field, spacing)


def relative_l2(numerator: np.ndarray, denominator_reference: np.ndarray, epsilon: float = 1e-15) -> float:
    mod = _get_native_backend()
    if mod is not None and not np.iscomplexobj(numerator) and not np.iscomplexobj(denominator_reference):
        return float(mod.relative_l2(
            np.ascontiguousarray(numerator, dtype=np.float64),
            np.ascontiguousarray(denominator_reference, dtype=np.float64),
            epsilon,
        ))
    return _PYTHON_REFERENCE["relative_l2"](numerator, denominator_reference, epsilon)


def gauss_linking_number(curve_a: np.ndarray, curve_b: np.ndarray, epsilon: float = 1e-14) -> float:
    mod = _get_native_backend()
    if mod is not None:
        return float(mod.gauss_linking_number(
            np.ascontiguousarray(curve_a, dtype=np.float64),
            np.ascontiguousarray(curve_b, dtype=np.float64),
            epsilon,
        ))
    return _PYTHON_REFERENCE["gauss_linking_number"](curve_a, curve_b, epsilon)


def su2_rotation(axis: Sequence[float], angle: float) -> np.ndarray:
    mod = _get_native_backend()
    if mod is not None:
        return mod.su2_rotation(np.ascontiguousarray(axis, dtype=np.float64), angle)
    return _PYTHON_REFERENCE["su2_rotation"](axis, angle)


def torus_knot_centerline(p: int = 2, q: int = 3, samples: int = 400, major_radius: float = 2.0, minor_radius: float = 0.7) -> np.ndarray:
    mod = _get_native_backend()
    if mod is not None:
        return mod.torus_knot_centerline(p, q, samples, major_radius, minor_radius)
    return _PYTHON_REFERENCE["torus_knot_centerline"](p, q, samples, major_radius, minor_radius)


def bishop_frame(curve: np.ndarray):
    mod = _get_native_backend()
    if mod is not None:
        return mod.bishop_frame(np.ascontiguousarray(curve, dtype=np.float64))
    return _PYTHON_REFERENCE["bishop_frame"](curve)


def structured_tube_spinor(curve: np.ndarray, e1: np.ndarray, e2: np.ndarray, radial_samples: int, angular_samples: int, tube_radius: float, m: int, n: int):
    mod = _get_native_backend()
    if mod is not None:
        return mod.structured_tube_spinor(
            np.ascontiguousarray(curve, dtype=np.float64),
            np.ascontiguousarray(e1, dtype=np.float64),
            np.ascontiguousarray(e2, dtype=np.float64),
            radial_samples, angular_samples, tube_radius, m, n,
        )
    return _PYTHON_REFERENCE["structured_tube_spinor"](curve, e1, e2, radial_samples, angular_samples, tube_radius, m, n)


def polygonal_writhe(curve: np.ndarray, neighbor_exclusion: int = 2) -> float:
    mod = _get_native_backend()
    if mod is not None:
        return float(mod.polygonal_writhe(np.ascontiguousarray(curve, dtype=np.float64), neighbor_exclusion))
    return _PYTHON_REFERENCE["polygonal_writhe"](curve, neighbor_exclusion)


def frame_twist(tangent: np.ndarray, e1: np.ndarray) -> float:
    mod = _get_native_backend()
    if mod is not None:
        return float(mod.frame_twist(
            np.ascontiguousarray(tangent, dtype=np.float64),
            np.ascontiguousarray(e1, dtype=np.float64),
        ))
    return _PYTHON_REFERENCE["frame_twist"](tangent, e1)

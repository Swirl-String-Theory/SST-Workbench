#!/usr/bin/env python3
"""Dimensionless dynamical-ratio research harness for SST.

This module intentionally avoids CODATA and SST dimensional calibration constants.
It works in nondimensional units with circulation Gamma=1 and a preregistered
normalization protocol. Its purpose is to generate topology-dependent ratios and
falsification diagnostics, not to identify a vortex knot with a particle.

Implemented research diagnostics
--------------------------------
* ring / trefoil / mirror-trefoil / figure-eight centreline generation;
* Brian Gilbert ideal-knot AB-block parser;
* uniform arclength resampling;
* sampled reach, curvature and ropelength diagnostics;
* regularized Biot-Savart velocity with three core kernels;
* best-fit translation + rotation modulo tangential gauge;
* relative-equilibrium residual;
* regularized self-induction energy proxy;
* hydrodynamic impulse and geometric observables;
* RK4 filament evolution with periodic remeshing;
* recurrence error modulo translation, rotation and cyclic parametrization;
* dimensionless rates, energy ratios and convergence campaigns;
* JSON and CSV output with explicit provenance and epistemic status.

The numerics are a research starting point. They do not constitute a finite-core
Euler theorem, a KAM certificate, or a particle prediction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

Array = np.ndarray
TAU = 2.0 * math.pi
SCHEMA_VERSION = "0.2.0"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurveSource:
    knot_id: str
    label: str
    source: str = "ideal_ab"
    generator: str | None = None
    mirror: bool = False


@dataclass(frozen=True)
class BackgroundFlowProtocol:
    """Extern opgelegde achtergrondstroming in dimensieloze eenheden.

    ``infinite_solid_body_vortex`` is de R_bg -> infinity limiet van de
    binnenste Rankine-tak: u_bg = Omega_bg x (x-center), met uniforme
    vorticiteit zeta_bg = 2 Omega_bg. Deze stroming heeft geen eindige
    totale energie op een oneindig domein; zij wordt uitsluitend als lokaal
    opgelegd snelheidsveld gebruikt.
    """

    kind: str = "none"
    dimensionless_vorticity: float = 0.0
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    provenance: str = "none"


@dataclass(frozen=True)
class NumericalProtocol:
    resolution: int = 128
    epsilon: float = 0.08
    kernel: str = "rosenhead"
    circulation: float = 1.0
    normalization: str = "fixed_length"
    target_length: float = TAU
    neighbor_skip: int | None = None
    background_flow: BackgroundFlowProtocol = field(default_factory=BackgroundFlowProtocol)


@dataclass(frozen=True)
class EvolutionProtocol:
    enabled: bool = False
    dt: float = 5.0e-4
    steps: int = 80
    sample_every: int = 4
    remesh_every: int = 1
    remove_tangential: bool = True


@dataclass
class RelativeMotionFit:
    translation: Array
    angular_velocity: Array
    projected_residual: float
    projected_velocity_norm: float
    residual_norm: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "translation": self.translation.tolist(),
            "angular_velocity": self.angular_velocity.tolist(),
            "projected_residual": float(self.projected_residual),
            "projected_velocity_norm": float(self.projected_velocity_norm),
            "residual_norm": float(self.residual_norm),
        }


@dataclass
class StaticDiagnostics:
    label: str
    knot_id: str
    source: str
    protocol: dict[str, Any]
    length: float
    rms_radius: float
    equivalent_ring_radius: float
    sampled_reach: float
    sampled_ropelength: float
    min_curvature_radius: float
    min_nonlocal_distance_half: float
    curvature_mean: float
    curvature_rms: float
    curvature_max: float
    bending_integral: float
    velocity_rms: float
    self_velocity_rms: float
    background_velocity_rms: float
    shape_velocity_rms: float
    rigid_rate: float
    deformation_rate: float
    energy_proxy: float
    impulse_norm: float
    impulse_vector: list[float]
    relative_motion: dict[str, Any]
    ring_lia_speed: float | None
    ring_lia_speed_ratio: float | None
    gates: dict[str, Any]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvolutionDiagnostics:
    times: list[float] = field(default_factory=list)
    lengths: list[float] = field(default_factory=list)
    energies: list[float] = field(default_factory=list)
    curvature_cv: list[float] = field(default_factory=list)
    recurrence_errors: list[float] = field(default_factory=list)
    rigid_rates: list[float] = field(default_factory=list)
    deformation_rates: list[float] = field(default_factory=list)
    dominant_shape_frequency: float | None = None
    final_recurrence_error: float | None = None
    minimum_recurrence_error: float | None = None
    relative_energy_drift: float | None = None
    relative_length_drift: float | None = None
    status: str = "NOT_RUN"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Core geometry utilities
# ---------------------------------------------------------------------------


def _points(a: Any) -> Array:
    p = np.asarray(a, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 8:
        raise ValueError("curve must be an (N,3) array with N >= 8")
    if not np.isfinite(p).all():
        raise ValueError("curve contains non-finite coordinates")
    return p


def center_curve(points: Array) -> Array:
    p = _points(points)
    return p - p.mean(axis=0, keepdims=True)


def segment_vectors(points: Array) -> Array:
    p = _points(points)
    return np.roll(p, -1, axis=0) - p


def segment_lengths(points: Array) -> Array:
    return np.linalg.norm(segment_vectors(points), axis=1)


def curve_length(points: Array) -> float:
    return float(segment_lengths(points).sum())


def equivalent_ring_radius(points: Array) -> float:
    return curve_length(points) / TAU


def rms_radius(points: Array) -> float:
    p = center_curve(points)
    return float(np.sqrt(np.mean(np.sum(p * p, axis=1))))


def unit_tangents(points: Array) -> Array:
    p = _points(points)
    d = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    n = np.linalg.norm(d, axis=1)
    if np.any(n <= 0):
        raise ValueError("degenerate tangent encountered")
    return d / n[:, None]


def uniform_arclength_resample(points: Array, n: int) -> Array:
    """Periodic piecewise-linear arclength resampling."""
    p = _points(points)
    if n < 8:
        raise ValueError("n must be >= 8")
    closed = np.vstack([p, p[0]])
    ds = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    total = float(ds.sum())
    if total <= 0:
        raise ValueError("zero-length curve")
    s = np.concatenate([[0.0], np.cumsum(ds)])
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = np.empty((n, 3), dtype=float)
    for k in range(3):
        out[:, k] = np.interp(targets, s, closed[:, k])
    return out


def normalize_curve(
    points: Array,
    protocol: str,
    target_length: float = TAU,
    target_rms_radius: float = 1.0,
    target_reach: float = 0.1,
    neighbor_skip: int | None = None,
) -> Array:
    """Center and scale a closed curve according to a preregistered protocol."""
    p = center_curve(points)
    if protocol == "fixed_length":
        scale = target_length / curve_length(p)
    elif protocol == "fixed_rms_radius":
        scale = target_rms_radius / rms_radius(p)
    elif protocol == "fixed_sampled_reach":
        reach, _, _ = sampled_reach(p, neighbor_skip=neighbor_skip)
        if reach <= 0 or not math.isfinite(reach):
            raise ValueError("cannot normalize by sampled reach")
        scale = target_reach / reach
    elif protocol == "none":
        scale = 1.0
    else:
        raise ValueError(f"unknown normalization protocol: {protocol}")
    return p * scale


def discrete_curvature(points: Array) -> tuple[Array, Array]:
    """Return vertex curvature and local arclength weights."""
    p = _points(points)
    prev = np.roll(p, 1, axis=0)
    nxt = np.roll(p, -1, axis=0)
    e0 = p - prev
    e1 = nxt - p
    l0 = np.linalg.norm(e0, axis=1)
    l1 = np.linalg.norm(e1, axis=1)
    u0 = e0 / l0[:, None]
    u1 = e1 / l1[:, None]
    cross = np.linalg.norm(np.cross(u0, u1), axis=1)
    dot = np.einsum("ij,ij->i", u0, u1)
    angle = np.arctan2(cross, np.clip(dot, -1.0, 1.0))
    ds = 0.5 * (l0 + l1)
    curvature = 2.0 * np.sin(0.5 * angle) / np.maximum(ds, 1e-15)
    return curvature, ds


def _cyclic_separation(i: Array, j: Array, n: int) -> Array:
    d = np.abs(i - j)
    return np.minimum(d, n - d)


def sampled_reach(points: Array, neighbor_skip: int | None = None) -> tuple[float, float, float]:
    """Approximate reach from curvature radius and sampled doubly-critical chords.

    A pair is retained only when its chord is approximately perpendicular to the
    tangent at both endpoints. This prevents nearby-but-not-critical points on a
    smooth circle from spuriously controlling the reach. The result remains a
    numerical diagnostic, not a certified continuous dcsd solve.
    """
    p = _points(points)
    n = len(p)
    skip = neighbor_skip if neighbor_skip is not None else max(4, n // 24)
    kappa, _ = discrete_curvature(p)
    positive = kappa[kappa > 1e-14]
    min_curv_radius = float(1.0 / positive.max()) if positive.size else math.inf

    tangents = unit_tangents(p)
    chord = p[:, None, :] - p[None, :, :]
    d2 = np.einsum("ijk,ijk->ij", chord, chord)
    dist = np.sqrt(np.maximum(d2, 0.0))
    ii, jj = np.indices((n, n))
    local_mask = _cyclic_separation(ii, jj, n) <= skip
    safe = np.maximum(dist, 1e-15)
    cos_i = np.abs(np.einsum("ijk,ik->ij", chord, tangents)) / safe
    cos_j = np.abs(np.einsum("ijk,jk->ij", chord, tangents)) / safe
    critical_mask = (cos_i <= 0.18) & (cos_j <= 0.18)
    candidate = d2.copy()
    candidate[local_mask | (~critical_mask)] = math.inf
    finite = candidate[np.isfinite(candidate)]
    if finite.size:
        min_nonlocal_half = 0.5 * float(np.sqrt(finite.min()))
    else:
        # Conservative fallback: no sampled doubly-critical chord was resolved.
        min_nonlocal_half = math.inf
    return min(min_curv_radius, min_nonlocal_half), min_curv_radius, min_nonlocal_half


def geometric_diagnostics(points: Array, neighbor_skip: int | None = None) -> dict[str, float]:
    p = _points(points)
    length = curve_length(p)
    reach, min_rk, min_d = sampled_reach(p, neighbor_skip)
    kappa, ds = discrete_curvature(p)
    return {
        "length": length,
        "rms_radius": rms_radius(p),
        "equivalent_ring_radius": length / TAU,
        "sampled_reach": reach,
        "sampled_ropelength": length / reach if reach > 0 else math.inf,
        "min_curvature_radius": min_rk,
        "min_nonlocal_distance_half": min_d,
        "curvature_mean": float(np.average(kappa, weights=ds)),
        "curvature_rms": float(np.sqrt(np.average(kappa * kappa, weights=ds))),
        "curvature_max": float(kappa.max()),
        "bending_integral": float(np.sum(kappa * kappa * ds)),
    }


# ---------------------------------------------------------------------------
# Curve sources
# ---------------------------------------------------------------------------


def generate_ring(n: int) -> Array:
    t = np.linspace(0.0, TAU, n, endpoint=False)
    return np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])


def generate_torus_trefoil(n: int, mirror: bool = False) -> Array:
    t = np.linspace(0.0, TAU, n, endpoint=False)
    # Standard smooth (2,3) torus-knot embedding, used only as a fallback.
    r = 2.0 + 0.72 * np.cos(3.0 * t)
    x = r * np.cos(2.0 * t)
    y = r * np.sin(2.0 * t)
    z = 0.72 * np.sin(3.0 * t)
    if mirror:
        z = -z
    return np.column_stack([x, y, z])


def generate_figure_eight(n: int) -> Array:
    t = np.linspace(0.0, TAU, n, endpoint=False)
    # Smooth standard 4_1 parametrization, fallback only.
    x = (2.0 + np.cos(2.0 * t)) * np.cos(3.0 * t)
    y = (2.0 + np.cos(2.0 * t)) * np.sin(3.0 * t)
    z = np.sin(4.0 * t)
    return np.column_stack([x, y, z])


def parse_ideal_ab_block(text: str, knot_id: str) -> tuple[list[tuple[int, Array, Array]], dict[str, str]]:
    """Parse a single-component Brian Gilbert <AB> block."""
    escaped = re.escape(knot_id)
    match = re.search(
        rf'<AB\s+Id="{escaped}"(?P<attrs>[^>]*)>(?P<body>.*?)</AB>',
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise KeyError(f"ideal AB block not found: {knot_id}")
    body = match.group("body")
    if "<Component" in body:
        raise ValueError(f"multi-component AB block is not supported by this harness: {knot_id}")
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', match.group("attrs")))
    coeffs: list[tuple[int, Array, Array]] = []
    coeff_re = re.compile(
        r'<Coeff\s+I="\s*(?P<i>-?\d+)"\s+A="(?P<a>[^"]+)"\s+B="(?P<b>[^"]+)"\s*/>'
    )
    for cm in coeff_re.finditer(body):
        idx = int(cm.group("i"))
        avec = np.array([float(x.strip()) for x in cm.group("a").split(",")], dtype=float)
        bvec = np.array([float(x.strip()) for x in cm.group("b").split(",")], dtype=float)
        if avec.shape != (3,) or bvec.shape != (3,):
            raise ValueError(f"invalid coefficient vector in {knot_id}, harmonic {idx}")
        coeffs.append((idx, avec, bvec))
    if not coeffs:
        raise ValueError(f"no coefficients found in AB block {knot_id}")
    return coeffs, attrs


def reconstruct_ideal_ab(text: str, knot_id: str, n: int, mirror: bool = False) -> Array:
    coeffs, _ = parse_ideal_ab_block(text, knot_id)
    t = np.linspace(0.0, TAU, n, endpoint=False)
    p = np.zeros((n, 3), dtype=float)
    for idx, avec, bvec in coeffs:
        if idx == 0:
            p += avec
        else:
            p += np.cos(idx * t)[:, None] * avec[None, :]
            p += np.sin(idx * t)[:, None] * bvec[None, :]
    if mirror:
        p[:, 2] *= -1.0
    return p


def load_curve(
    source: CurveSource,
    n: int,
    ideal_file: str | Path | None,
) -> Array:
    if source.source == "ideal_ab":
        if ideal_file is None:
            raise ValueError("ideal_file is required for ideal_ab source")
        text = Path(ideal_file).read_text(encoding="utf-8", errors="replace")
        return reconstruct_ideal_ab(text, source.knot_id, n, mirror=source.mirror)
    if source.source == "generator":
        name = source.generator or source.knot_id
        if name in {"ring", "0_1", "0:1:1"}:
            return generate_ring(n)
        if name in {"trefoil", "3_1", "3:1:1"}:
            return generate_torus_trefoil(n, mirror=source.mirror)
        if name in {"figure8", "figure-eight", "4_1", "4:1:1"}:
            return generate_figure_eight(n)
        raise ValueError(f"unknown generator: {name}")
    raise ValueError(f"unknown curve source: {source.source}")


# ---------------------------------------------------------------------------
# Biot-Savart, energy, impulse and relative-motion fitting
# ---------------------------------------------------------------------------


def _kernel_factor(r2: Array, epsilon: float, kernel: str) -> Array:
    e2 = epsilon * epsilon
    if kernel == "rosenhead":
        return 1.0 / np.power(r2 + e2, 1.5)
    if kernel == "rankine":
        return 1.0 / np.power(np.maximum(r2, e2), 1.5)
    if kernel == "winckelmans":
        return (r2 + 2.5 * e2) / np.power(r2 + e2, 2.5)
    raise ValueError(f"unknown core kernel: {kernel}")


def biot_savart_velocity(
    points: Array,
    epsilon: float,
    circulation: float = 1.0,
    kernel: str = "rosenhead",
) -> Array:
    """Midpoint-segment regularized Biot-Savart velocity at the vertices."""
    p = _points(points)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    dl = segment_vectors(p)
    mid = p + 0.5 * dl
    # r[i,j] = field point i - segment midpoint j
    r = p[:, None, :] - mid[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", r, r)
    factor = _kernel_factor(r2, epsilon, kernel)
    cross = np.cross(dl[None, :, :], r)
    u = circulation / (4.0 * math.pi) * np.sum(cross * factor[:, :, None], axis=1)
    return u


def _unit_vector(values: Sequence[float], name: str) -> Array:
    v = np.asarray(values, dtype=float)
    if v.shape != (3,) or not np.isfinite(v).all():
        raise ValueError(f"{name} must contain three finite numbers")
    n = float(np.linalg.norm(v))
    if n <= 1e-15:
        raise ValueError(f"{name} must be non-zero")
    return v / n


def background_velocity(points: Array, background: BackgroundFlowProtocol) -> Array:
    """Return an externally imposed background velocity at curve vertices.

    For ``infinite_solid_body_vortex``:

        u_bg = Omega_bg x (x - x0),
        Omega_bg = 0.5 * zeta_bg * axis.

    Here ``dimensionless_vorticity`` is zeta_bg in the campaign units.
    """
    p = _points(points)
    if background.kind == "none" or abs(background.dimensionless_vorticity) <= 1e-18:
        return np.zeros_like(p)
    if background.kind != "infinite_solid_body_vortex":
        raise ValueError(f"unknown background flow: {background.kind}")
    axis = _unit_vector(background.axis, "background axis")
    center = np.asarray(background.center, dtype=float)
    if center.shape != (3,) or not np.isfinite(center).all():
        raise ValueError("background center must contain three finite numbers")
    omega = 0.5 * float(background.dimensionless_vorticity) * axis
    return np.cross(np.broadcast_to(omega, p.shape), p - center[None, :])


def total_velocity(points: Array, protocol: NumericalProtocol) -> tuple[Array, Array, Array]:
    u_self = biot_savart_velocity(points, protocol.epsilon, protocol.circulation, protocol.kernel)
    u_bg = background_velocity(points, protocol.background_flow)
    return u_self + u_bg, u_self, u_bg


def projected_shape_velocity(points: Array, velocity: Array) -> Array:
    p = _points(points)
    u = np.asarray(velocity, dtype=float)
    if u.shape != p.shape:
        raise ValueError("velocity shape mismatch")
    t = unit_tangents(p)
    return u - np.einsum("ij,ij->i", u, t)[:, None] * t


def _skew(v: Array) -> Array:
    x, y, z = map(float, v)
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=float)


def fit_relative_motion(points: Array, velocity: Array) -> RelativeMotionFit:
    """Fit u = U + Omega x r modulo independent tangential gauge at each point."""
    p = center_curve(points)
    u = np.asarray(velocity, dtype=float)
    t = unit_tangents(p)
    eye = np.eye(3)
    rows: list[Array] = []
    rhs: list[Array] = []
    projected_u = np.empty_like(u)
    for i in range(len(p)):
        proj = eye - np.outer(t[i], t[i])
        # Omega x r = -[r]_x Omega
        block = np.hstack([proj, proj @ (-_skew(p[i]))])
        rows.append(block)
        projected_u[i] = proj @ u[i]
        rhs.append(projected_u[i])
    a = np.vstack(rows)
    b = np.concatenate(rhs)
    params, *_ = np.linalg.lstsq(a, b, rcond=None)
    translation = params[:3]
    omega = params[3:]
    predicted = translation[None, :] + np.cross(omega[None, :], p)
    residual = projected_shape_velocity(p, u - predicted)
    denom = float(np.linalg.norm(projected_u))
    rnorm = float(np.linalg.norm(residual))
    rel = rnorm / denom if denom > 1e-15 else 0.0
    return RelativeMotionFit(translation, omega, rel, denom, rnorm)


def self_induction_energy_proxy(
    points: Array,
    epsilon: float,
    circulation: float = 1.0,
) -> float:
    """Regularized double-line-integral energy proxy in rho=1 units."""
    p = _points(points)
    dl = segment_vectors(p)
    mid = p + 0.5 * dl
    r = mid[:, None, :] - mid[None, :, :]
    denom = np.sqrt(np.einsum("ijk,ijk->ij", r, r) + epsilon * epsilon)
    dot = dl @ dl.T
    energy = circulation * circulation / (8.0 * math.pi) * np.sum(dot / denom)
    return float(energy)


def hydrodynamic_impulse(points: Array, circulation: float = 1.0) -> Array:
    p = _points(points)
    dl = segment_vectors(p)
    return 0.5 * circulation * np.sum(np.cross(p, dl), axis=0)


def ring_lia_speed(radius: float, epsilon: float, circulation: float = 1.0) -> float | None:
    if radius <= 0 or epsilon <= 0 or 8.0 * radius <= epsilon:
        return None
    return circulation / (4.0 * math.pi * radius) * (math.log(8.0 * radius / epsilon) - 0.25)


def static_diagnostics(
    source: CurveSource,
    points: Array,
    protocol: NumericalProtocol,
) -> StaticDiagnostics:
    p = _points(points)
    g = geometric_diagnostics(p, protocol.neighbor_skip)
    u, u_self, u_bg = total_velocity(p, protocol)
    ushape = projected_shape_velocity(p, u)
    fit = fit_relative_motion(p, u)
    self_projected_norm = float(np.linalg.norm(projected_shape_velocity(p, u_self)))
    intrinsic_residual = (
        fit.residual_norm / self_projected_norm if self_projected_norm > 1e-15 else 0.0
    )
    relative_motion = fit.to_dict()
    relative_motion["projected_residual_total_normalized"] = relative_motion["projected_residual"]
    relative_motion["projected_residual_intrinsic"] = float(intrinsic_residual)
    relative_motion["self_projected_velocity_norm"] = self_projected_norm
    radius = g["equivalent_ring_radius"]
    v_rms = float(np.sqrt(np.mean(np.sum(u * u, axis=1))))
    self_v_rms = float(np.sqrt(np.mean(np.sum(u_self * u_self, axis=1))))
    bg_v_rms = float(np.sqrt(np.mean(np.sum(u_bg * u_bg, axis=1))))
    s_rms = float(np.sqrt(np.mean(np.sum(ushape * ushape, axis=1))))
    rigid_rate = float(
        math.sqrt(
            (np.linalg.norm(fit.translation) / max(radius, 1e-15)) ** 2
            + np.linalg.norm(fit.angular_velocity) ** 2
        )
    )
    deformation_rate = fit.residual_norm / math.sqrt(len(p)) / max(radius, 1e-15)
    energy = self_induction_energy_proxy(p, protocol.epsilon, protocol.circulation)
    impulse = hydrodynamic_impulse(p, protocol.circulation)

    lia = None
    lia_ratio = None
    if source.knot_id in {"0:1:1", "0_1", "ring"} or source.generator == "ring":
        lia = ring_lia_speed(radius, protocol.epsilon, protocol.circulation)
        if lia and lia != 0:
            lia_ratio = float(np.linalg.norm(fit.translation) / lia)

    gates = {
        "relative_equilibrium_5pct": bool(intrinsic_residual <= 0.05),
        "relative_equilibrium_1pct": bool(intrinsic_residual <= 0.01),
        "positive_sampled_reach": bool(g["sampled_reach"] > 0),
        "core_fits_inside_sampled_reach": bool(protocol.epsilon < g["sampled_reach"]),
        "finite_energy": bool(math.isfinite(energy)),
    }
    status = "PASS_RELATIVE_EQUILIBRIUM_GATE" if gates["relative_equilibrium_5pct"] else "FAIL_RELATIVE_EQUILIBRIUM_GATE"
    if not gates["core_fits_inside_sampled_reach"]:
        status = "INVALID_CORE_GEOMETRY"

    return StaticDiagnostics(
        label=source.label,
        knot_id=source.knot_id,
        source=source.source,
        protocol=asdict(protocol),
        length=g["length"],
        rms_radius=g["rms_radius"],
        equivalent_ring_radius=radius,
        sampled_reach=g["sampled_reach"],
        sampled_ropelength=g["sampled_ropelength"],
        min_curvature_radius=g["min_curvature_radius"],
        min_nonlocal_distance_half=g["min_nonlocal_distance_half"],
        curvature_mean=g["curvature_mean"],
        curvature_rms=g["curvature_rms"],
        curvature_max=g["curvature_max"],
        bending_integral=g["bending_integral"],
        velocity_rms=v_rms,
        self_velocity_rms=self_v_rms,
        background_velocity_rms=bg_v_rms,
        shape_velocity_rms=s_rms,
        rigid_rate=rigid_rate,
        deformation_rate=float(deformation_rate),
        energy_proxy=energy,
        impulse_norm=float(np.linalg.norm(impulse)),
        impulse_vector=impulse.tolist(),
        relative_motion=relative_motion,
        ring_lia_speed=lia,
        ring_lia_speed_ratio=lia_ratio,
        gates=gates,
        status=status,
    )


# ---------------------------------------------------------------------------
# Relative recurrence and evolution
# ---------------------------------------------------------------------------


def kabsch_align(reference: Array, moving: Array) -> tuple[Array, Array, float]:
    a = center_curve(reference)
    b = center_curve(moving)
    h = b.T @ a
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1, :] *= -1
        r = vt.T @ u.T
    aligned = b @ r.T
    rmsd = float(np.sqrt(np.mean(np.sum((a - aligned) ** 2, axis=1))))
    return aligned, r, rmsd


def best_cyclic_recurrence(reference: Array, moving: Array, allow_reverse: bool = False) -> dict[str, Any]:
    a = _points(reference)
    b = _points(moving)
    if len(a) != len(b):
        raise ValueError("recurrence curves must have equal point count")
    scale = max(rms_radius(a), 1e-15)
    best = {"normalized_rmsd": math.inf, "shift": 0, "reversed": False, "rotation": np.eye(3)}
    candidates = [(b, False)]
    if allow_reverse:
        candidates.append((b[::-1].copy(), True))
    for candidate, rev in candidates:
        for shift in range(len(a)):
            shifted = np.roll(candidate, shift, axis=0)
            _, rot, rmsd = kabsch_align(a, shifted)
            nr = rmsd / scale
            if nr < best["normalized_rmsd"]:
                best = {"normalized_rmsd": float(nr), "shift": shift, "reversed": rev, "rotation": rot}
    best["rotation"] = np.asarray(best["rotation"]).tolist()
    return best


def _rhs(points: Array, protocol: NumericalProtocol, remove_tangential: bool) -> Array:
    u, _, _ = total_velocity(points, protocol)
    return projected_shape_velocity(points, u) if remove_tangential else u


def rk4_step(points: Array, dt: float, protocol: NumericalProtocol, remove_tangential: bool = True) -> Array:
    p = _points(points)
    k1 = _rhs(p, protocol, remove_tangential)
    k2 = _rhs(p + 0.5 * dt * k1, protocol, remove_tangential)
    k3 = _rhs(p + 0.5 * dt * k2, protocol, remove_tangential)
    k4 = _rhs(p + dt * k3, protocol, remove_tangential)
    return p + dt / 6.0 * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def _dominant_frequency(values: Sequence[float], dt: float) -> float | None:
    x = np.asarray(values, dtype=float)
    # Fewer than 32 samples cannot resolve a defensible spectral peak.
    if len(x) < 32 or dt <= 0:
        return None
    x = x - x.mean()
    if float(np.linalg.norm(x)) < 1e-12:
        return None
    window = np.hanning(len(x))
    spectrum = np.abs(np.fft.rfft(x * window))
    freqs = np.fft.rfftfreq(len(x), d=dt)
    if len(spectrum) <= 1:
        return None
    idx = int(np.argmax(spectrum[1:]) + 1)
    return float(freqs[idx])


def evolve_and_diagnose(
    points: Array,
    protocol: NumericalProtocol,
    evolution: EvolutionProtocol,
) -> tuple[Array, EvolutionDiagnostics]:
    if not evolution.enabled:
        return _points(points).copy(), EvolutionDiagnostics(status="NOT_RUN")
    p = _points(points).copy()
    initial = p.copy()
    initial_length = curve_length(p)
    initial_energy = self_induction_energy_proxy(p, protocol.epsilon, protocol.circulation)
    diag = EvolutionDiagnostics(status="RUNNING")

    def sample(step: int, state: Array) -> None:
        time = step * evolution.dt
        length = curve_length(state)
        energy = self_induction_energy_proxy(state, protocol.epsilon, protocol.circulation)
        kappa, ds = discrete_curvature(state)
        mean_k = float(np.average(kappa, weights=ds))
        cv = float(np.sqrt(np.average((kappa - mean_k) ** 2, weights=ds)) / max(mean_k, 1e-15))
        u, _, _ = total_velocity(state, protocol)
        fit = fit_relative_motion(state, u)
        radius = equivalent_ring_radius(state)
        rigid_rate = math.sqrt(
            (np.linalg.norm(fit.translation) / max(radius, 1e-15)) ** 2
            + np.linalg.norm(fit.angular_velocity) ** 2
        )
        deform_rate = fit.residual_norm / math.sqrt(len(state)) / max(radius, 1e-15)
        rec = best_cyclic_recurrence(initial, state, allow_reverse=False)
        diag.times.append(float(time))
        diag.lengths.append(float(length))
        diag.energies.append(float(energy))
        diag.curvature_cv.append(cv)
        diag.recurrence_errors.append(float(rec["normalized_rmsd"]))
        diag.rigid_rates.append(float(rigid_rate))
        diag.deformation_rates.append(float(deform_rate))

    sample(0, p)
    for step in range(1, evolution.steps + 1):
        p = rk4_step(p, evolution.dt, protocol, evolution.remove_tangential)
        if evolution.remesh_every > 0 and step % evolution.remesh_every == 0:
            p = uniform_arclength_resample(p, protocol.resolution)
        if step % evolution.sample_every == 0 or step == evolution.steps:
            sample(step, p)

    sample_dt = evolution.dt * evolution.sample_every
    diag.dominant_shape_frequency = _dominant_frequency(diag.curvature_cv, sample_dt)
    diag.final_recurrence_error = diag.recurrence_errors[-1]
    diag.minimum_recurrence_error = min(diag.recurrence_errors[1:], default=diag.recurrence_errors[0])
    diag.relative_energy_drift = (diag.energies[-1] - initial_energy) / max(abs(initial_energy), 1e-15)
    diag.relative_length_drift = (diag.lengths[-1] - initial_length) / max(abs(initial_length), 1e-15)
    diag.status = "COMPLETE"
    return p, diag


# ---------------------------------------------------------------------------
# Campaign orchestration and outputs
# ---------------------------------------------------------------------------


def default_sources() -> list[CurveSource]:
    return [
        CurveSource("0:1:1", "ring", "ideal_ab"),
        CurveSource("3:1:1", "trefoil", "ideal_ab"),
        CurveSource("3:1:1", "mirror_trefoil", "ideal_ab", mirror=True),
        CurveSource("4:1:1", "figure_eight", "ideal_ab"),
    ]


def _sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _parse_vector3(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if isinstance(value, str):
        parts = [x.strip() for x in value.split(",")]
        value = [float(x) for x in parts]
    if not isinstance(value, Sequence) or len(value) != 3:
        raise ValueError("expected a three-component vector")
    return tuple(float(x) for x in value)


def _make_background(config: Mapping[str, Any], vorticity: float | None = None) -> BackgroundFlowProtocol:
    bg = config.get("background_flow", {}) or {}
    kind = str(bg.get("type", bg.get("kind", "none")))
    if vorticity is None:
        vorticity = float(bg.get("dimensionless_vorticity", 0.0))
    return BackgroundFlowProtocol(
        kind=kind,
        dimensionless_vorticity=float(vorticity),
        axis=_parse_vector3(bg.get("axis"), (0.0, 0.0, 1.0)),
        center=_parse_vector3(bg.get("center"), (0.0, 0.0, 0.0)),
        provenance=str(bg.get("provenance", "user_config")),
    )


def _make_protocol(config: Mapping[str, Any], resolution: int, epsilon: float, kernel: str, background_vorticity: float = 0.0) -> NumericalProtocol:
    return NumericalProtocol(
        resolution=int(resolution),
        epsilon=float(epsilon),
        kernel=str(kernel),
        circulation=float(config.get("circulation", 1.0)),
        normalization=str(config.get("normalization", "fixed_length")),
        target_length=float(config.get("target_length", TAU)),
        neighbor_skip=config.get("neighbor_skip"),
        background_flow=_make_background(config, background_vorticity),
    )


def _make_evolution(config: Mapping[str, Any]) -> EvolutionProtocol:
    return EvolutionProtocol(
        enabled=bool(config.get("enabled", False)),
        dt=float(config.get("dt", 5e-4)),
        steps=int(config.get("steps", 80)),
        sample_every=int(config.get("sample_every", 4)),
        remesh_every=int(config.get("remesh_every", 1)),
        remove_tangential=bool(config.get("remove_tangential", True)),
    )


def _source_from_dict(d: Mapping[str, Any]) -> CurveSource:
    return CurveSource(
        knot_id=str(d["knot_id"]),
        label=str(d.get("label", d["knot_id"])),
        source=str(d.get("source", "ideal_ab")),
        generator=d.get("generator"),
        mirror=bool(d.get("mirror", False)),
    )


def ratio_or_none(value: float | None, reference: float | None) -> float | None:
    # A symmetry-protected or numerically zero reference cannot define a ratio.
    if value is None or reference is None or abs(reference) <= 1e-10:
        return None
    return float(value / reference)


def compute_group_ratios(rows: list[dict[str, Any]], reference_label: str) -> None:
    reference = next((r for r in rows if r["static"]["label"] == reference_label), None)
    if reference is None:
        for row in rows:
            row["ratios"] = {"status": "NO_REFERENCE"}
        return
    sref = reference["static"]
    eref = reference["evolution"]
    metrics = [
        "energy_proxy",
        "rigid_rate",
        "deformation_rate",
        "velocity_rms",
        "shape_velocity_rms",
        "impulse_norm",
        "bending_integral",
        "sampled_ropelength",
    ]
    for row in rows:
        s = row["static"]
        e = row["evolution"]
        ratios = {f"{m}_ratio": ratio_or_none(s.get(m), sref.get(m)) for m in metrics}
        ratios["dominant_shape_frequency_ratio"] = ratio_or_none(
            e.get("dominant_shape_frequency"), eref.get("dominant_shape_frequency")
        )
        ratios["reference_label"] = reference_label
        ratios["status"] = "COMPUTED"
        row["ratios"] = ratios


def run_campaign(config: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    ideal_file = config.get("ideal_file")
    if ideal_file is not None:
        ideal_file = str(Path(ideal_file).resolve())
    sources = [_source_from_dict(x) for x in config.get("cases", [])] or default_sources()
    resolutions = [int(x) for x in config.get("resolutions", [96, 128])]
    epsilons = [float(x) for x in config.get("epsilons", [0.06, 0.08, 0.10])]
    kernels = [str(x) for x in config.get("kernels", ["rosenhead", "winckelmans"])]
    bg_cfg = config.get("background_flow", {}) or {}
    background_vorticities = [float(x) for x in bg_cfg.get(
        "dimensionless_vorticities",
        [bg_cfg.get("dimensionless_vorticity", 0.0)],
    )]
    evolution = _make_evolution(config.get("evolution", {}))
    reference_label = str(config.get("reference_label", "ring"))

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "epistemic_status": "RESEARCH_TRACK_NUMERICAL_HARNESS",
        "claim_guard": (
            "Dimensionless topology diagnostics only. Background SST constants are used "
            "only to motivate the preregistered dimensionless vorticity 1/pi; no particle "
            "identification, finite-core Euler theorem, or KAM certification is claimed."
        ),
        "dependency_exclusion": ["alpha", "electron_mass", "Newton_G", "Planck_length", "Bohr_radius"],
        "config": dict(config),
        "source_provenance": {
            "ideal_file": ideal_file,
            "ideal_file_sha256": _sha256(ideal_file) if ideal_file else None,
        },
        "groups": [],
    }

    for resolution in resolutions:
        for epsilon in epsilons:
            for kernel in kernels:
                for background_vorticity in background_vorticities:
                    protocol = _make_protocol(config, resolution, epsilon, kernel, background_vorticity)
                    group_rows: list[dict[str, Any]] = []
                    for source in sources:
                        raw = load_curve(source, max(resolution * 4, 512), ideal_file)
                        raw = uniform_arclength_resample(raw, resolution)
                        p = normalize_curve(
                            raw,
                            protocol.normalization,
                            target_length=protocol.target_length,
                            neighbor_skip=protocol.neighbor_skip,
                        )
                        p = uniform_arclength_resample(p, resolution)
                        static = static_diagnostics(source, p, protocol)
                        final_points, dynamic = evolve_and_diagnose(p, protocol, evolution)
                        row = {
                            "static": static.to_dict(),
                            "evolution": dynamic.to_dict(),
                            "final_points": final_points.tolist() if config.get("save_final_points", False) else None,
                        }
                        group_rows.append(row)
                    compute_group_ratios(group_rows, reference_label)
                    result["groups"].append(
                        {
                            "protocol": asdict(protocol),
                            "evolution_protocol": asdict(evolution),
                            "rows": group_rows,
                        }
                    )
    write_json(output / "campaign_results.json", result)
    write_campaign_csv(output / "campaign_summary.csv", result)
    write_convergence_csv(output / "convergence_summary.csv", result, reference_label)
    return result


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _flatten_row(group: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    p = group["protocol"]
    s = row["static"]
    e = row["evolution"]
    r = row.get("ratios", {})
    flat: dict[str, Any] = {
        "resolution": p["resolution"],
        "epsilon": p["epsilon"],
        "kernel": p["kernel"],
        "normalization": p["normalization"],
        "background_type": p.get("background_flow", {}).get("kind", "none"),
        "background_vorticity": p.get("background_flow", {}).get("dimensionless_vorticity", 0.0),
        "label": s["label"],
        "knot_id": s["knot_id"],
        "status": s["status"],
        "relative_equilibrium_residual": s["relative_motion"].get(
            "projected_residual_intrinsic", s["relative_motion"]["projected_residual"]
        ),
        "total_normalized_residual": s["relative_motion"]["projected_residual"],
        "length": s["length"],
        "sampled_reach": s["sampled_reach"],
        "sampled_ropelength": s["sampled_ropelength"],
        "energy_proxy": s["energy_proxy"],
        "self_velocity_rms": s.get("self_velocity_rms"),
        "background_velocity_rms": s.get("background_velocity_rms"),
        "rigid_rate": s["rigid_rate"],
        "deformation_rate": s["deformation_rate"],
        "impulse_norm": s["impulse_norm"],
        "bending_integral": s["bending_integral"],
        "dominant_shape_frequency": e.get("dominant_shape_frequency"),
        "final_recurrence_error": e.get("final_recurrence_error"),
        "minimum_recurrence_error": e.get("minimum_recurrence_error"),
        "relative_energy_drift": e.get("relative_energy_drift"),
        "relative_length_drift": e.get("relative_length_drift"),
    }
    flat.update(r)
    return flat


def write_campaign_csv(path: str | Path, campaign: Mapping[str, Any]) -> None:
    rows = [_flatten_row(group, row) for group in campaign["groups"] for row in group["rows"]]
    if not rows:
        return
    fields = sorted({k for row in rows for k in row})
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_convergence_csv(path: str | Path, campaign: Mapping[str, Any], reference_label: str) -> None:
    rows: list[dict[str, Any]] = []
    for group in campaign["groups"]:
        p = group["protocol"]
        for row in group["rows"]:
            s = row["static"]
            ratios = row.get("ratios", {})
            rows.append(
                {
                    "resolution": p["resolution"],
                    "epsilon": p["epsilon"],
                    "kernel": p["kernel"],
                    "background_type": p.get("background_flow", {}).get("kind", "none"),
                    "background_vorticity": p.get("background_flow", {}).get("dimensionless_vorticity", 0.0),
                    "label": s["label"],
                    "reference": reference_label,
                    "relative_equilibrium_residual": s["relative_motion"].get(
                        "projected_residual_intrinsic", s["relative_motion"]["projected_residual"]
                    ),
                    "total_normalized_residual": s["relative_motion"]["projected_residual"],
                    "energy_ratio": ratios.get("energy_proxy_ratio"),
                    "rigid_rate_ratio": ratios.get("rigid_rate_ratio"),
                    "deformation_rate_ratio": ratios.get("deformation_rate_ratio"),
                    "impulse_ratio": ratios.get("impulse_norm_ratio"),
                }
            )
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load_config(path: str | Path) -> dict[str, Any]:
    cfg_path = Path(path).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if "ideal_file" in cfg and cfg["ideal_file"] is not None:
        candidate = Path(cfg["ideal_file"])
        if not candidate.is_absolute():
            cfg["ideal_file"] = str((cfg_path.parent / candidate).resolve())
    return cfg


def command_campaign(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    result = run_campaign(config, args.output)
    print(json.dumps({
        "status": "complete",
        "groups": len(result["groups"]),
        "output": str(Path(args.output).resolve()),
    }, indent=2))
    return 0


def command_diagnose(args: argparse.Namespace) -> int:
    source = CurveSource(args.knot_id, args.label or args.knot_id, args.source, args.generator, args.mirror)
    protocol = NumericalProtocol(
        resolution=args.resolution,
        epsilon=args.epsilon,
        kernel=args.kernel,
        normalization=args.normalization,
        target_length=args.target_length,
        background_flow=BackgroundFlowProtocol(
            kind=args.background_type,
            dimensionless_vorticity=args.background_vorticity,
            axis=_parse_vector3(args.background_axis, (0.0, 0.0, 1.0)),
            center=_parse_vector3(args.background_center, (0.0, 0.0, 0.0)),
            provenance="cli",
        ),
    )
    raw = load_curve(source, max(args.resolution * 4, 512), args.ideal_file)
    p = uniform_arclength_resample(raw, args.resolution)
    p = normalize_curve(p, protocol.normalization, target_length=protocol.target_length)
    p = uniform_arclength_resample(p, args.resolution)
    result = static_diagnostics(source, p, protocol).to_dict()
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_evolve(args: argparse.Namespace) -> int:
    source = CurveSource(args.knot_id, args.label or args.knot_id, args.source, args.generator, args.mirror)
    protocol = NumericalProtocol(
        resolution=args.resolution,
        epsilon=args.epsilon,
        kernel=args.kernel,
        normalization=args.normalization,
        target_length=args.target_length,
        background_flow=BackgroundFlowProtocol(
            kind=args.background_type,
            dimensionless_vorticity=args.background_vorticity,
            axis=_parse_vector3(args.background_axis, (0.0, 0.0, 1.0)),
            center=_parse_vector3(args.background_center, (0.0, 0.0, 0.0)),
            provenance="cli",
        ),
    )
    evolution = EvolutionProtocol(
        enabled=True,
        dt=args.dt,
        steps=args.steps,
        sample_every=args.sample_every,
        remesh_every=args.remesh_every,
        remove_tangential=not args.keep_tangential,
    )
    raw = load_curve(source, max(args.resolution * 4, 512), args.ideal_file)
    p = uniform_arclength_resample(raw, args.resolution)
    p = normalize_curve(p, protocol.normalization, target_length=protocol.target_length)
    p = uniform_arclength_resample(p, args.resolution)
    static = static_diagnostics(source, p, protocol)
    final, dynamic = evolve_and_diagnose(p, protocol, evolution)
    payload = {
        "static": static.to_dict(),
        "evolution": dynamic.to_dict(),
        "final_points": final.tolist() if args.save_points else None,
    }
    if args.output:
        write_json(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_selftest(_: argparse.Namespace) -> int:
    ring = normalize_curve(generate_ring(96), "fixed_length", target_length=TAU)
    protocol = NumericalProtocol(resolution=96, epsilon=0.08)
    source = CurveSource("ring", "ring", "generator", "ring")
    diag = static_diagnostics(source, ring, protocol)
    bg_protocol = NumericalProtocol(
        resolution=96,
        epsilon=0.08,
        background_flow=BackgroundFlowProtocol(
            kind="infinite_solid_body_vortex",
            dimensionless_vorticity=1.0 / math.pi,
            provenance="sst_gamma0_over_pi",
        ),
    )
    bg_diag = static_diagnostics(source, ring, bg_protocol)
    checks = {
        "length_is_2pi": abs(diag.length - TAU) < 5e-3,
        "ring_residual_below_2pct": diag.relative_motion["projected_residual_intrinsic"] < 0.02,
        "finite_energy": math.isfinite(diag.energy_proxy),
        "positive_reach": diag.sampled_reach > 0,
        "solid_body_residual_invariant": abs(
            bg_diag.relative_motion["projected_residual_intrinsic"]
            - diag.relative_motion["projected_residual_intrinsic"]
        ) < 1e-10,
    }
    print(json.dumps({
        "checks": checks,
        "diagnostics": diag.to_dict(),
        "solid_body_background_diagnostics": bg_diag.to_dict(),
    }, indent=2))
    return 0 if all(checks.values()) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SST research-track harness for dimensionless dynamical knot ratios."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("campaign", help="run a JSON-configured convergence campaign")
    pc.add_argument("--config", required=True)
    pc.add_argument("--output", required=True)
    pc.set_defaults(func=command_campaign)

    def add_curve_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--knot-id", required=True)
        p.add_argument("--label")
        p.add_argument("--source", choices=["ideal_ab", "generator"], default="ideal_ab")
        p.add_argument("--generator")
        p.add_argument("--ideal-file")
        p.add_argument("--mirror", action="store_true")
        p.add_argument("--resolution", type=int, default=128)
        p.add_argument("--epsilon", type=float, default=0.08)
        p.add_argument("--kernel", choices=["rosenhead", "rankine", "winckelmans"], default="rosenhead")
        p.add_argument(
            "--normalization",
            choices=["fixed_length", "fixed_rms_radius", "fixed_sampled_reach", "none"],
            default="fixed_length",
        )
        p.add_argument("--target-length", type=float, default=TAU)
        p.add_argument(
            "--background-type",
            choices=["none", "infinite_solid_body_vortex"],
            default="none",
        )
        p.add_argument("--background-vorticity", type=float, default=0.0)
        p.add_argument("--background-axis", default="0,0,1")
        p.add_argument("--background-center", default="0,0,0")
        p.add_argument("--output")

    pd = sub.add_parser("diagnose", help="compute static dimensionless diagnostics")
    add_curve_args(pd)
    pd.set_defaults(func=command_diagnose)

    pe = sub.add_parser("evolve", help="evolve one curve and compute recurrence diagnostics")
    add_curve_args(pe)
    pe.add_argument("--dt", type=float, default=5e-4)
    pe.add_argument("--steps", type=int, default=80)
    pe.add_argument("--sample-every", type=int, default=4)
    pe.add_argument("--remesh-every", type=int, default=1)
    pe.add_argument("--keep-tangential", action="store_true")
    pe.add_argument("--save-points", action="store_true")
    pe.set_defaults(func=command_evolve)

    ps = sub.add_parser("selftest", help="run an internal ring sanity check")
    ps.set_defaults(func=command_selftest)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

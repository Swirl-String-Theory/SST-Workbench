#!/usr/bin/env python3
"""Finite-radius axial vortex-bundle tests for SST research track.

This module extends the dimensionless knot harness with an externally imposed
bundle of infinite straight vortex tubes parallel to a chosen axis.  The bundle
radius is tied to the free central aperture of the knot unless an absolute
radius is preregistered.

Two physically distinct modes are kept separate:

* ``physical_tubes``: circulation per tube is fixed. Increasing tube count
  increases total background circulation and therefore changes the physics.
* ``numerical_discretization``: total bundle circulation is fixed. Increasing
  tube count only refines a discrete representation of a continuum Rankine
  bundle and should converge to that reference.

The tubes are frozen, straight and infinite in this release. Full 3-D mutual
backreaction and tube bending are an explicit open gate, not silently assumed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from sst_dimensionless_ratios import (
    CurveSource,
    EvolutionProtocol,
    NumericalProtocol,
    best_cyclic_recurrence,
    biot_savart_velocity,
    center_curve,
    curve_length,
    default_sources,
    discrete_curvature,
    equivalent_ring_radius,
    fit_relative_motion,
    geometric_diagnostics,
    hydrodynamic_impulse,
    load_curve,
    normalize_curve,
    projected_shape_velocity,
    self_induction_energy_proxy,
    uniform_arclength_resample,
)

Array = np.ndarray
TAU = 2.0 * math.pi
SCHEMA_VERSION = "0.3.1"


@dataclass(frozen=True)
class BundleProtocol:
    kind: str = "none"  # none | continuum_rankine | discrete_axial_tubes
    mode: str = "none"  # continuum | physical_tubes | numerical_discretization
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    radius_ratio_to_hole: float = 1.0
    absolute_radius: float | None = None
    strength_basis: str = "total_circulation"  # total_circulation | mean_vorticity | mode_default
    total_circulation: float = 1.0
    mean_vorticity: float = 0.0
    tube_count: int = 1
    tube_circulation: float = 1.0
    circulation_sign: float = 1.0
    tube_kernel: str = "rankine"  # rankine | rosenhead
    tube_core_radius_ratio: float = 0.0
    packing_fraction: float = 0.35
    layout: str = "hex_disk"
    clock_observation_time: float = 1.0
    frozen_tubes: bool = True
    require_bundle_inside_hole: bool = True
    provenance: str = "user_config"
    ladder_gate: str = "UNSPECIFIED"


@dataclass
class ResolvedBundle:
    protocol: BundleProtocol
    centerline_hole_radius: float
    free_hole_radius: float
    bundle_radius: float
    tube_core_radius: float
    tube_count: int
    circulation_per_tube: float
    total_circulation: float
    mean_vorticity: float
    clock_omega: float
    clock_period: float | None
    clock_phase: float
    clock_cycles: float
    tube_centers: Array = field(repr=False)
    valid_geometry: bool = True
    validity_reason: str = "OK"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tube_centers"] = self.tube_centers.tolist()
        return d


def _unit(v: Sequence[float]) -> Array:
    a = np.asarray(v, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError("axis must be a finite 3-vector")
    n = float(np.linalg.norm(a))
    if n <= 1e-15:
        raise ValueError("axis must be nonzero")
    return a / n


def _transverse_vectors(points: Array, axis: Array, center: Array) -> Array:
    rel = np.asarray(points, dtype=float) - center[None, :]
    return rel - np.outer(rel @ axis, axis)


def central_aperture(points: Array, axis: Sequence[float], center: Sequence[float], knot_core_radius: float) -> tuple[float, float]:
    ahat = _unit(axis)
    c = np.asarray(center, dtype=float)
    rho = np.linalg.norm(_transverse_vectors(points, ahat, c), axis=1)
    centerline = float(np.min(rho))
    free = centerline - float(knot_core_radius)
    return centerline, free


def _hex_disk_points(n: int) -> Array:
    """Deterministic near-hexagonal points in a unit disk."""
    if n < 1:
        raise ValueError("tube_count must be >= 1")
    if n == 1:
        return np.zeros((1, 2), dtype=float)
    shell = 1
    candidates: list[tuple[float, float]] = [(0.0, 0.0)]
    while len(candidates) < max(n * 3, n + 12):
        candidates = []
        for q in range(-shell, shell + 1):
            for r in range(-shell, shell + 1):
                x = q + 0.5 * r
                y = (math.sqrt(3.0) / 2.0) * r
                if x * x + y * y <= shell * shell + 1e-12:
                    candidates.append((x, y))
        shell += 1
    candidates.sort(key=lambda xy: (xy[0] ** 2 + xy[1] ** 2, math.atan2(xy[1], xy[0])))
    pts = np.asarray(candidates[:n], dtype=float)
    rmax = float(np.max(np.linalg.norm(pts, axis=1)))
    if rmax > 0:
        pts /= rmax
    return pts


def _axis_basis(axis: Array) -> tuple[Array, Array]:
    trial = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(axis, trial)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    return e1, e2


def _tube_centers_3d(n: int, radius: float, core_radius: float, axis: Array, center: Array) -> Array:
    uv = _hex_disk_points(n)
    usable = max(radius - core_radius, 0.0)
    uv = uv * usable
    e1, e2 = _axis_basis(axis)
    return center[None, :] + uv[:, 0, None] * e1[None, :] + uv[:, 1, None] * e2[None, :]


def resolve_bundle(points: Array, knot_core_radius: float, protocol: BundleProtocol) -> ResolvedBundle:
    axis = _unit(protocol.axis)
    center = np.asarray(protocol.center, dtype=float)
    centerline_hole, free_hole = central_aperture(points, axis, center, knot_core_radius)
    if protocol.kind == "none":
        return ResolvedBundle(
            protocol=protocol,
            centerline_hole_radius=centerline_hole,
            free_hole_radius=free_hole,
            bundle_radius=0.0,
            tube_core_radius=0.0,
            tube_count=0,
            circulation_per_tube=0.0,
            total_circulation=0.0,
            mean_vorticity=0.0,
            clock_omega=0.0,
            clock_period=None,
            clock_phase=0.0,
            clock_cycles=0.0,
            tube_centers=np.empty((0, 3), dtype=float),
            valid_geometry=free_hole > 0,
            validity_reason="OK" if free_hole > 0 else "KNOT_CORE_CLOSES_CENTRAL_APERTURE",
        )

    if free_hole <= 0:
        return ResolvedBundle(
            protocol=protocol,
            centerline_hole_radius=centerline_hole,
            free_hole_radius=free_hole,
            bundle_radius=0.0,
            tube_core_radius=0.0,
            tube_count=max(1, protocol.tube_count),
            circulation_per_tube=0.0,
            total_circulation=0.0,
            mean_vorticity=0.0,
            clock_omega=0.0,
            clock_period=None,
            clock_phase=0.0,
            clock_cycles=0.0,
            tube_centers=np.empty((0, 3), dtype=float),
            valid_geometry=False,
            validity_reason="KNOT_CORE_CLOSES_CENTRAL_APERTURE",
        )

    radius = float(protocol.absolute_radius) if protocol.absolute_radius is not None else float(protocol.radius_ratio_to_hole) * free_hole
    if radius <= 0:
        raise ValueError("bundle radius must be positive")

    n = max(1, int(protocol.tube_count))
    sign = 1.0 if protocol.circulation_sign >= 0 else -1.0
    mode = protocol.mode

    if protocol.kind == "continuum_rankine" or mode == "continuum":
        if protocol.strength_basis == "mean_vorticity":
            mean_vorticity = sign * abs(float(protocol.mean_vorticity))
            total = mean_vorticity * math.pi * radius * radius
        else:
            total = sign * abs(float(protocol.total_circulation))
            mean_vorticity = total / (math.pi * radius * radius)
        n = 0
        per_tube = 0.0
        core = 0.0
        centers = np.empty((0, 3), dtype=float)
    elif protocol.kind == "discrete_axial_tubes":
        if mode == "physical_tubes":
            per_tube = sign * abs(float(protocol.tube_circulation))
            total = n * per_tube
        elif mode == "numerical_discretization":
            total = sign * abs(float(protocol.total_circulation))
            per_tube = total / n
        else:
            raise ValueError(f"unknown discrete bundle mode: {mode}")
        mean_vorticity = total / (math.pi * radius * radius)
        if protocol.tube_core_radius_ratio > 0:
            core = protocol.tube_core_radius_ratio * radius
        else:
            core = radius * math.sqrt(max(protocol.packing_fraction, 1e-6) / n)
        raw = _hex_disk_points(n)
        if n > 1:
            d = np.linalg.norm(raw[:, None, :] - raw[None, :, :], axis=2)
            d[d <= 1e-12] = np.inf
            min_spacing_unit = float(np.min(d))
            core = min(core, 0.42 * min_spacing_unit * radius)
        core = max(core, 1e-6 * radius)
        centers = _tube_centers_3d(n, radius, core, axis, np.asarray(protocol.center, dtype=float))
    else:
        raise ValueError(f"unknown bundle kind: {protocol.kind}")

    omega = total / (2.0 * math.pi * radius * radius)
    period = TAU / abs(omega) if abs(omega) > 1e-15 else None
    phase = omega * float(protocol.clock_observation_time)
    cycles = phase / TAU
    geometry_ok = True
    if protocol.require_bundle_inside_hole:
        geometry_ok = radius <= free_hole + 1e-12
        if protocol.kind == "discrete_axial_tubes":
            # bundle_radius is defined as the outer edge of the packed tube bundle;
            # tube centres are already restricted to radius-core.
            geometry_ok = geometry_ok and (radius <= free_hole + 1e-12)
    reason = "OK" if geometry_ok else "BUNDLE_OR_TUBE_CORE_INTERSECTS_KNOT_CORE"

    return ResolvedBundle(
        protocol=protocol,
        centerline_hole_radius=centerline_hole,
        free_hole_radius=free_hole,
        bundle_radius=radius,
        tube_core_radius=core,
        tube_count=n,
        circulation_per_tube=per_tube,
        total_circulation=total,
        mean_vorticity=mean_vorticity,
        clock_omega=omega,
        clock_period=period,
        clock_phase=phase,
        clock_cycles=cycles,
        tube_centers=centers,
        valid_geometry=geometry_ok,
        validity_reason=reason,
    )


def _continuum_rankine_velocity(points: Array, resolved: ResolvedBundle) -> Array:
    p = np.asarray(points, dtype=float)
    axis = _unit(resolved.protocol.axis)
    center = np.asarray(resolved.protocol.center, dtype=float)
    rho_vec = _transverse_vectors(p, axis, center)
    rho = np.linalg.norm(rho_vec, axis=1)
    cross = np.cross(axis[None, :], rho_vec)
    r2 = resolved.bundle_radius ** 2
    factors = np.empty(len(p), dtype=float)
    inside = rho <= resolved.bundle_radius
    factors[inside] = resolved.total_circulation / (2.0 * math.pi * r2)
    factors[~inside] = resolved.total_circulation / (2.0 * math.pi * np.maximum(rho[~inside] ** 2, 1e-30))
    return factors[:, None] * cross


def _single_tube_velocity(points: Array, center: Array, axis: Array, gamma: float, core: float, kernel: str) -> Array:
    rho_vec = _transverse_vectors(points, axis, center)
    rho2 = np.einsum("ij,ij->i", rho_vec, rho_vec)
    cross = np.cross(axis[None, :], rho_vec)
    if kernel == "rankine":
        factors = np.where(
            rho2 <= core * core,
            gamma / (2.0 * math.pi * core * core),
            gamma / (2.0 * math.pi * np.maximum(rho2, 1e-30)),
        )
    elif kernel == "rosenhead":
        factors = gamma / (2.0 * math.pi * (rho2 + core * core))
    else:
        raise ValueError(f"unknown tube kernel: {kernel}")
    return factors[:, None] * cross


def bundle_velocity(points: Array, resolved: ResolvedBundle) -> Array:
    if resolved.protocol.kind == "none" or abs(resolved.total_circulation) <= 1e-18:
        return np.zeros_like(points, dtype=float)
    if resolved.protocol.kind == "continuum_rankine" or resolved.protocol.mode == "continuum":
        return _continuum_rankine_velocity(points, resolved)
    axis = _unit(resolved.protocol.axis)
    out = np.zeros_like(points, dtype=float)
    for center in resolved.tube_centers:
        out += _single_tube_velocity(
            points,
            center,
            axis,
            resolved.circulation_per_tube,
            resolved.tube_core_radius,
            resolved.protocol.tube_kernel,
        )
    return out


def static_bundle_diagnostics(source: CurveSource, points: Array, base: NumericalProtocol, bundle: BundleProtocol) -> dict[str, Any]:
    p = np.asarray(points, dtype=float)
    resolved = resolve_bundle(p, base.epsilon, bundle)
    geom = geometric_diagnostics(p, base.neighbor_skip)
    u_self = biot_savart_velocity(p, base.epsilon, base.circulation, base.kernel)
    u_bg = bundle_velocity(p, resolved)
    u_total = u_self + u_bg
    fit_total = fit_relative_motion(p, u_total)
    fit_self = fit_relative_motion(p, u_self)
    fit_bg = fit_relative_motion(p, u_bg) if np.linalg.norm(u_bg) > 1e-15 else None
    self_proj_norm = float(np.linalg.norm(projected_shape_velocity(p, u_self)))
    total_proj_norm = float(np.linalg.norm(projected_shape_velocity(p, u_total)))
    intrinsic = fit_total.residual_norm / self_proj_norm if self_proj_norm > 1e-15 else 0.0
    total_normalized = fit_total.residual_norm / total_proj_norm if total_proj_norm > 1e-15 else 0.0
    baseline_intrinsic = fit_self.residual_norm / self_proj_norm if self_proj_norm > 1e-15 else 0.0
    radius = equivalent_ring_radius(p)
    energy = self_induction_energy_proxy(p, base.epsilon, base.circulation)
    impulse = hydrodynamic_impulse(p, base.circulation)
    bg_rms = float(np.sqrt(np.mean(np.sum(u_bg * u_bg, axis=1))))
    total_rms = float(np.sqrt(np.mean(np.sum(u_total * u_total, axis=1))))
    self_rms = float(np.sqrt(np.mean(np.sum(u_self * u_self, axis=1))))
    deformation_rate = fit_total.residual_norm / math.sqrt(len(p)) / max(radius, 1e-15)
    background_nonrigid_rate = 0.0
    if fit_bg is not None:
        background_nonrigid_rate = fit_bg.residual_norm / math.sqrt(len(p)) / max(radius, 1e-15)
    gates = {
        "positive_free_hole": resolved.free_hole_radius > 0,
        "bundle_geometry_valid": resolved.valid_geometry,
        "relative_equilibrium_5pct": intrinsic <= 0.05,
        "relative_equilibrium_1pct": intrinsic <= 0.01,
        "finite_energy": math.isfinite(energy),
        "frozen_tube_model_only": bool(bundle.frozen_tubes),
        "full_3d_backreaction_certified": False,
    }
    status = "PASS_RELATIVE_EQUILIBRIUM_GATE" if gates["relative_equilibrium_5pct"] else "FAIL_RELATIVE_EQUILIBRIUM_GATE"
    if not resolved.valid_geometry:
        status = "INVALID_BUNDLE_GEOMETRY"
    return {
        "label": source.label,
        "knot_id": source.knot_id,
        "source": source.source,
        "base_protocol": asdict(base),
        "bundle_protocol": asdict(bundle),
        "resolved_bundle": resolved.to_dict(),
        "length": geom["length"],
        "rms_radius": geom["rms_radius"],
        "sampled_reach": geom["sampled_reach"],
        "sampled_ropelength": geom["sampled_ropelength"],
        "central_hole_radius": resolved.centerline_hole_radius,
        "free_hole_radius": resolved.free_hole_radius,
        "energy_proxy": energy,
        "impulse_norm": float(np.linalg.norm(impulse)),
        "impulse_vector": impulse.tolist(),
        "self_velocity_rms": self_rms,
        "background_velocity_rms": bg_rms,
        "total_velocity_rms": total_rms,
        "background_nonrigid_rate": background_nonrigid_rate,
        "deformation_rate": deformation_rate,
        "relative_motion": {
            **fit_total.to_dict(),
            "intrinsic_self_normalized_residual": float(intrinsic),
            "total_normalized_residual": float(total_normalized),
            "isolated_baseline_residual": float(baseline_intrinsic),
            "residual_reduction_fraction": float(1.0 - intrinsic / baseline_intrinsic) if baseline_intrinsic > 1e-15 else None,
            "self_projected_velocity_norm": self_proj_norm,
            "total_projected_velocity_norm": total_proj_norm,
        },
        "clock": {
            "omega_gamma": resolved.clock_omega,
            "period_gamma": resolved.clock_period,
            "observation_time": bundle.clock_observation_time,
            "phase_gamma": resolved.clock_phase,
            "cycle_count": resolved.clock_cycles,
            "status": "CLOCK_CARRIER_DIAGNOSTIC_ONLY",
        },
        "gates": gates,
        "status": status,
    }


def _rhs(points: Array, base: NumericalProtocol, resolved: ResolvedBundle, remove_tangential: bool) -> Array:
    u = biot_savart_velocity(points, base.epsilon, base.circulation, base.kernel) + bundle_velocity(points, resolved)
    return projected_shape_velocity(points, u) if remove_tangential else u


def _rk4(points: Array, dt: float, base: NumericalProtocol, resolved: ResolvedBundle, remove_tangential: bool) -> Array:
    k1 = _rhs(points, base, resolved, remove_tangential)
    k2 = _rhs(points + 0.5 * dt * k1, base, resolved, remove_tangential)
    k3 = _rhs(points + 0.5 * dt * k2, base, resolved, remove_tangential)
    k4 = _rhs(points + dt * k3, base, resolved, remove_tangential)
    return points + dt * (k1 + 2*k2 + 2*k3 + k4) / 6.0


def evolve_bundle(points: Array, base: NumericalProtocol, bundle: BundleProtocol, evolution: EvolutionProtocol) -> tuple[Array, dict[str, Any]]:
    if not evolution.enabled:
        return np.asarray(points, dtype=float).copy(), {"status": "NOT_RUN"}
    p = np.asarray(points, dtype=float).copy()
    initial = p.copy()
    resolved = resolve_bundle(initial, base.epsilon, bundle)
    e0 = self_induction_energy_proxy(p, base.epsilon, base.circulation)
    l0 = curve_length(p)
    out: dict[str, Any] = {
        "status": "RUNNING",
        "times": [], "energies": [], "lengths": [], "recurrence_errors": [],
        "intrinsic_residuals": [], "clock_phases": [], "clock_cycles": [],
    }

    def sample(step: int) -> None:
        t = step * evolution.dt
        u_self = biot_savart_velocity(p, base.epsilon, base.circulation, base.kernel)
        u_total = u_self + bundle_velocity(p, resolved)
        fit = fit_relative_motion(p, u_total)
        self_norm = float(np.linalg.norm(projected_shape_velocity(p, u_self)))
        intrinsic = fit.residual_norm / self_norm if self_norm > 1e-15 else 0.0
        rec = best_cyclic_recurrence(initial, p, allow_reverse=False)["normalized_rmsd"]
        out["times"].append(float(t))
        out["energies"].append(float(self_induction_energy_proxy(p, base.epsilon, base.circulation)))
        out["lengths"].append(float(curve_length(p)))
        out["recurrence_errors"].append(float(rec))
        out["intrinsic_residuals"].append(float(intrinsic))
        phase = resolved.clock_omega * t
        out["clock_phases"].append(float(phase))
        out["clock_cycles"].append(float(phase / TAU))

    sample(0)
    for step in range(1, evolution.steps + 1):
        p = _rk4(p, evolution.dt, base, resolved, evolution.remove_tangential)
        if evolution.remesh_every > 0 and step % evolution.remesh_every == 0:
            p = uniform_arclength_resample(p, base.resolution)
        if step % evolution.sample_every == 0 or step == evolution.steps:
            sample(step)
    out["final_recurrence_error"] = out["recurrence_errors"][-1]
    out["minimum_nontrivial_recurrence_error"] = min(out["recurrence_errors"][1:], default=None)
    out["relative_energy_drift"] = (out["energies"][-1] - e0) / max(abs(e0), 1e-15)
    out["relative_length_drift"] = (out["lengths"][-1] - l0) / max(abs(l0), 1e-15)
    out["final_clock_phase"] = out["clock_phases"][-1]
    out["final_clock_cycles"] = out["clock_cycles"][-1]
    out["status"] = "COMPLETE_FROZEN_TUBES"
    return p, out


def _parse_vec(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if isinstance(value, str):
        value = [float(x.strip()) for x in value.split(",")]
    if len(value) != 3:
        raise ValueError("expected a 3-vector")
    return tuple(float(x) for x in value)


def _source(d: Mapping[str, Any]) -> CurveSource:
    return CurveSource(
        knot_id=str(d["knot_id"]),
        label=str(d.get("label", d["knot_id"])),
        source=str(d.get("source", "ideal_ab")),
        generator=d.get("generator"),
        mirror=bool(d.get("mirror", False)),
    )


def _base_protocol(config: Mapping[str, Any], resolution: int, epsilon: float, kernel: str) -> NumericalProtocol:
    return NumericalProtocol(
        resolution=resolution,
        epsilon=epsilon,
        kernel=kernel,
        circulation=float(config.get("circulation", 1.0)),
        normalization=str(config.get("normalization", "fixed_sampled_reach")),
        target_length=float(config.get("target_length", TAU)),
        neighbor_skip=config.get("neighbor_skip"),
    )


def expand_bundle_protocols(config: Mapping[str, Any]) -> list[BundleProtocol]:
    b = config.get("bundle", {}) or {}
    kind = str(b.get("kind", "none"))
    gate = str(config.get("ladder_gate", b.get("ladder_gate", "UNSPECIFIED")))
    common = dict(
        axis=_parse_vec(b.get("axis"), (0.0, 0.0, 1.0)),
        center=_parse_vec(b.get("center"), (0.0, 0.0, 0.0)),
        tube_kernel=str(b.get("tube_kernel", "rankine")),
        tube_core_radius_ratio=float(b.get("tube_core_radius_ratio", 0.0)),
        packing_fraction=float(b.get("packing_fraction", 0.35)),
        layout=str(b.get("layout", "hex_disk")),
        clock_observation_time=float(b.get("clock_observation_time", 1.0)),
        frozen_tubes=bool(b.get("frozen_tubes", True)),
        require_bundle_inside_hole=bool(b.get("require_bundle_inside_hole", True)),
        provenance=str(b.get("provenance", "user_config")),
        ladder_gate=gate,
    )
    if kind == "none":
        return [BundleProtocol(kind="none", mode="none", **common)]

    radius_ratios = [float(x) for x in b.get("radius_ratios", [b.get("radius_ratio_to_hole", 1.0)])]
    signs = [float(x) for x in b.get("circulation_signs", [b.get("circulation_sign", 1.0)])]
    modes = [str(x) for x in b.get("modes", [b.get("mode", "continuum")])]
    protocols: list[BundleProtocol] = []
    for mode in modes:
        if mode == "continuum":
            basis = str(b.get("strength_basis", "total_circulation"))
            values = b.get("mean_vorticities", [b.get("mean_vorticity", 0.0)]) if basis == "mean_vorticity" else b.get("total_circulations", [b.get("total_circulation", 1.0)])
            for rr in radius_ratios:
                for sign in signs:
                    for value in values:
                        protocols.append(BundleProtocol(
                            kind="continuum_rankine", mode="continuum",
                            radius_ratio_to_hole=rr,
                            absolute_radius=b.get("absolute_radius"),
                            strength_basis=basis,
                            total_circulation=float(value) if basis != "mean_vorticity" else 0.0,
                            mean_vorticity=float(value) if basis == "mean_vorticity" else 0.0,
                            circulation_sign=sign,
                            **common,
                        ))
        elif mode == "physical_tubes":
            counts = [int(x) for x in b.get("tube_counts", [1, 7, 19, 37])]
            gammas = [float(x) for x in b.get("tube_circulations", [b.get("tube_circulation", 1.0)])]
            for rr in radius_ratios:
                for sign in signs:
                    for n in counts:
                        for gamma in gammas:
                            protocols.append(BundleProtocol(
                                kind="discrete_axial_tubes", mode=mode,
                                radius_ratio_to_hole=rr, tube_count=n,
                                tube_circulation=gamma, circulation_sign=sign,
                                strength_basis="mode_default", **common,
                            ))
        elif mode == "numerical_discretization":
            counts = [int(x) for x in b.get("tube_counts", [1, 7, 19, 37, 61])]
            totals = [float(x) for x in b.get("total_circulations", [b.get("total_circulation", 1.0)])]
            for rr in radius_ratios:
                for sign in signs:
                    for n in counts:
                        for total in totals:
                            protocols.append(BundleProtocol(
                                kind="discrete_axial_tubes", mode=mode,
                                radius_ratio_to_hole=rr, tube_count=n,
                                total_circulation=total, circulation_sign=sign,
                                strength_basis="mode_default", **common,
                            ))
            if bool(b.get("include_continuum_reference", False)):
                for rr in radius_ratios:
                    for sign in signs:
                        for total in totals:
                            protocols.append(BundleProtocol(
                                kind="continuum_rankine", mode="continuum",
                                radius_ratio_to_hole=rr,
                                total_circulation=total, circulation_sign=sign,
                                strength_basis="total_circulation", **common,
                            ))
        else:
            raise ValueError(f"unknown bundle mode: {mode}")
    return protocols


def _ratio(value: float | None, ref: float | None) -> float | None:
    if value is None or ref is None or abs(ref) < 1e-14:
        return None
    return float(value / ref)


def _add_ratios(rows: list[dict[str, Any]], reference_label: str) -> None:
    ref = next((r for r in rows if r["static"]["label"] == reference_label), None)
    for row in rows:
        if ref is None:
            row["ratios"] = {"status": "NO_REFERENCE"}
            continue
        s, sr = row["static"], ref["static"]
        row["ratios"] = {
            "status": "COMPUTED",
            "reference_label": reference_label,
            "energy_ratio": _ratio(s["energy_proxy"], sr["energy_proxy"]),
            "impulse_ratio": _ratio(s["impulse_norm"], sr["impulse_norm"]),
            "intrinsic_residual_ratio": _ratio(s["relative_motion"]["intrinsic_self_normalized_residual"], sr["relative_motion"]["intrinsic_self_normalized_residual"]),
            "clock_omega_ratio": _ratio(s["clock"]["omega_gamma"], sr["clock"]["omega_gamma"]),
        }


def run_campaign(config: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    ideal_file = config.get("ideal_file")
    if ideal_file:
        ideal_file = str(Path(ideal_file).resolve())
    sources = [_source(x) for x in config.get("cases", [])] or default_sources()
    resolutions = [int(x) for x in config.get("resolutions", [96])]
    epsilons = [float(x) for x in config.get("epsilons", [0.05])]
    kernels = [str(x) for x in config.get("kernels", ["rosenhead"])]
    bundles = expand_bundle_protocols(config)
    evo_cfg = config.get("evolution", {}) or {}
    evolution = EvolutionProtocol(
        enabled=bool(evo_cfg.get("enabled", False)),
        dt=float(evo_cfg.get("dt", 2.5e-4)),
        steps=int(evo_cfg.get("steps", 200)),
        sample_every=int(evo_cfg.get("sample_every", 10)),
        remesh_every=int(evo_cfg.get("remesh_every", 1)),
        remove_tangential=bool(evo_cfg.get("remove_tangential", True)),
    )
    reference_label = str(config.get("reference_label", "ring"))
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "epistemic_status": "RESEARCH_TRACK_FROZEN_AXIAL_BUNDLE_HARNESS",
        "claim_guard": (
            "Infinite straight tubes are frozen external defects. Physical-tube and numerical-"
            "discretization modes are not interchangeable. No full 3-D tube backreaction, finite-core "
            "Euler existence theorem, particle identification, or proper-time derivation is claimed."
        ),
        "test_ladder_gate": config.get("ladder_gate", "UNSPECIFIED"),
        "config": dict(config),
        "groups": [],
    }
    for resolution in resolutions:
        for epsilon in epsilons:
            for kernel in kernels:
                base = _base_protocol(config, resolution, epsilon, kernel)
                for bundle in bundles:
                    rows: list[dict[str, Any]] = []
                    for source in sources:
                        raw = load_curve(source, max(resolution * 4, 512), ideal_file)
                        p = uniform_arclength_resample(raw, resolution)
                        p = normalize_curve(
                            p,
                            base.normalization,
                            target_length=base.target_length,
                            target_reach=float(config.get("target_reach", 0.1)),
                            neighbor_skip=base.neighbor_skip,
                        )
                        p = uniform_arclength_resample(p, resolution)
                        static = static_bundle_diagnostics(source, p, base, bundle)
                        final, dynamic = evolve_bundle(p, base, bundle, evolution)
                        rows.append({
                            "static": static,
                            "evolution": dynamic,
                            "final_points": final.tolist() if config.get("save_final_points", False) else None,
                        })
                    _add_ratios(rows, reference_label)
                    result["groups"].append({
                        "base_protocol": asdict(base),
                        "bundle_protocol": asdict(bundle),
                        "evolution_protocol": asdict(evolution),
                        "rows": rows,
                    })
    (output / "campaign_results.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(output / "campaign_summary.csv", result)
    write_csv(output / "convergence_summary.csv", result)
    return result


def _flat(group: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    s = row["static"]
    rb = s["resolved_bundle"]
    rel = s["relative_motion"]
    evo = row["evolution"]
    return {
        "ladder_gate": group["bundle_protocol"].get("ladder_gate"),
        "resolution": group["base_protocol"]["resolution"],
        "epsilon": group["base_protocol"]["epsilon"],
        "kernel": group["base_protocol"]["kernel"],
        "normalization": group["base_protocol"]["normalization"],
        "label": s["label"],
        "knot_id": s["knot_id"],
        "bundle_kind": rb["protocol"]["kind"],
        "bundle_mode": rb["protocol"]["mode"],
        "radius_ratio_to_hole": rb["protocol"]["radius_ratio_to_hole"],
        "centerline_hole_radius": rb["centerline_hole_radius"],
        "free_hole_radius": rb["free_hole_radius"],
        "bundle_radius": rb["bundle_radius"],
        "tube_count": rb["tube_count"],
        "tube_core_radius": rb["tube_core_radius"],
        "circulation_per_tube": rb["circulation_per_tube"],
        "total_circulation": rb["total_circulation"],
        "mean_vorticity": rb["mean_vorticity"],
        "clock_omega": rb["clock_omega"],
        "clock_period": rb["clock_period"],
        "clock_phase": rb["clock_phase"],
        "clock_cycles": rb["clock_cycles"],
        "valid_geometry": rb["valid_geometry"],
        "status": s["status"],
        "intrinsic_residual": rel["intrinsic_self_normalized_residual"],
        "total_normalized_residual": rel["total_normalized_residual"],
        "isolated_baseline_residual": rel["isolated_baseline_residual"],
        "residual_reduction_fraction": rel["residual_reduction_fraction"],
        "deformation_rate": s["deformation_rate"],
        "background_nonrigid_rate": s["background_nonrigid_rate"],
        "background_velocity_rms": s["background_velocity_rms"],
        "energy_proxy": s["energy_proxy"],
        "impulse_norm": s["impulse_norm"],
        "final_recurrence_error": evo.get("final_recurrence_error"),
        "relative_energy_drift": evo.get("relative_energy_drift"),
        "relative_length_drift": evo.get("relative_length_drift"),
        "final_clock_phase": evo.get("final_clock_phase"),
        "final_clock_cycles": evo.get("final_clock_cycles"),
    }


def write_csv(path: Path, result: Mapping[str, Any]) -> None:
    rows = [_flat(group, row) for group in result["groups"] for row in group["rows"]]
    if not rows:
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _load_config(path: str | Path) -> dict[str, Any]:
    p = Path(path).resolve()
    cfg = json.loads(p.read_text(encoding="utf-8"))
    if cfg.get("ideal_file"):
        candidate = Path(cfg["ideal_file"])
        if not candidate.is_absolute():
            cfg["ideal_file"] = str((p.parent / candidate).resolve())
    return cfg


def command_campaign(args: argparse.Namespace) -> int:
    result = run_campaign(_load_config(args.config), args.output)
    print(json.dumps({"status": "complete", "groups": len(result["groups"]), "output": str(Path(args.output).resolve())}, indent=2))
    return 0


def command_selftest(_: argparse.Namespace) -> int:
    config = {
        "ladder_gate": "SELFTEST",
        "ideal_file": str((Path(__file__).resolve().parents[1] / "data" / "ideal_favorites.txt")),
        "cases": [{"knot_id": "3:1:1", "label": "trefoil", "source": "ideal_ab"}],
        "resolutions": [96], "epsilons": [0.05], "kernels": ["rosenhead"],
        "normalization": "fixed_sampled_reach", "target_reach": 0.2,
        "bundle": {
            "kind": "discrete_axial_tubes", "modes": ["numerical_discretization"],
            "radius_ratios": [1.0], "tube_counts": [7], "total_circulations": [1.0],
            "include_continuum_reference": True, "tube_kernel": "rankine",
        },
        "evolution": {"enabled": False},
    }
    tmp = Path.cwd() / "_bundle_selftest_output"
    result = run_campaign(config, tmp)
    rows = [_flat(g, r) for g in result["groups"] for r in g["rows"]]
    checks = {
        "two_modes_present": {r["bundle_mode"] for r in rows} == {"numerical_discretization", "continuum"},
        "finite_metrics": all(math.isfinite(float(r["intrinsic_residual"])) for r in rows),
        "clock_relation": all(abs(r["clock_omega"] - r["total_circulation"]/(2*math.pi*r["bundle_radius"]**2)) < 1e-10 for r in rows),
        "numerical_total_flux_fixed": all(abs(r["total_circulation"] - 1.0) < 1e-12 for r in rows),
    }
    print(json.dumps({"checks": checks, "rows": rows}, indent=2))
    return 0 if all(checks.values()) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SST finite axial vortex-bundle research harness")
    sub = p.add_subparsers(dest="command", required=True)
    pc = sub.add_parser("campaign")
    pc.add_argument("--config", required=True)
    pc.add_argument("--output", required=True)
    pc.set_defaults(func=command_campaign)
    ps = sub.add_parser("selftest")
    ps.set_defaults(func=command_selftest)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

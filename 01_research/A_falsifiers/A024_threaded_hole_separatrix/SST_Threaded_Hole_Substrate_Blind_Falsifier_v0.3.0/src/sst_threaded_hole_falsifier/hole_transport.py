from __future__ import annotations

"""Kelvin/M'Farlane central-hole transport and persistence diagnostics.

The module is deliberately identity-blind: every quantity is computed from the
anonymous geometry, circulations, and preregistered numerical settings supplied
to the blind runner.  It never reads carrier names, family labels, active/null
labels, or SST target values.

The central question is operationalized as follows:

    Is the centerline-visible passage also a persistent Lagrangian transport
    structure in the carrier's co-moving frame?

A visual gap is therefore not enough.  A candidate must exhibit a coherent
open through-channel or a coherent captured atmosphere, survive a finite
carrier evolution, and remain qualitatively stable under preregistered normal
perturbations.
"""

from dataclasses import dataclass
import math
from typing import Dict, Iterable, Tuple

import numpy as np

from .model import CurveSet
from .geometry import (
    deformation_basis,
    kabsch,
    resample_closed,
    shape_velocity,
)
from .native import field_velocity, vortex_velocity

PI = math.pi
EPS = 1.0e-14
CORE_DELTAS = {"hollow": 0.5, "rankine": 0.25, "gp": 0.615}
ROBUST_BASE_CLASSES = {"OPEN_CHANNEL", "CAPTURED_ATMOSPHERE"}


# ---------------------------------------------------------------------------
# Kelvin--M'Farlane analytic oracle
# ---------------------------------------------------------------------------

def kelvin_point_vortex_pair_velocity(xy: np.ndarray, a: float = 1.0, gamma: float = 1.0) -> np.ndarray:
    """Velocity of two parallel, opposite point vortices in their 2-D section.

    +Gamma sits at (-a,0), -Gamma at (+a,0).  The pair translates in +y with
    U = Gamma/(4*pi*a).  Output is the inertial-frame induced velocity.
    """
    q = np.asarray(xy, dtype=float)
    if q.ndim == 1:
        q = q[None, :]
    if q.shape[1] != 2:
        raise ValueError("xy must have shape (N,2)")
    out = np.zeros_like(q)
    for x0, g in ((-float(a), float(gamma)), (float(a), -float(gamma))):
        r = q - np.array([x0, 0.0])
        r2 = np.sum(r * r, axis=1)
        r2 = np.maximum(r2, 1.0e-30)
        out[:, 0] += g * (-r[:, 1]) / (2.0 * PI * r2)
        out[:, 1] += g * ( r[:, 0]) / (2.0 * PI * r2)
    return out


def kelvin_pair_translation(a: float = 1.0, gamma: float = 1.0) -> float:
    return float(gamma) / (4.0 * PI * float(a))


def kelvin_streamline_residual(x: np.ndarray, y: np.ndarray, a: float = 1.0, b: float = 0.0) -> np.ndarray:
    """Residual of Kelvin/M'Farlane's implicit streamline relation.

        ln N = (x+b)/a,
        N = ((x+a)^2+y^2)/((x-a)^2+y^2).
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    aa = float(a)
    num = (x + aa) ** 2 + y ** 2
    den = (x - aa) ** 2 + y ** 2
    return np.log(np.maximum(num, 1.0e-300) / np.maximum(den, 1.0e-300)) - (x + float(b)) / aa


def _coth(z: np.ndarray | float) -> np.ndarray:
    z = np.asarray(z, float)
    # Stable local series avoids a removable 0/0 at the b=0 symmetry plane.
    out = np.empty_like(z)
    small = np.abs(z) < 1.0e-5
    zs = z[small]
    loc = np.empty_like(zs)
    zero = zs == 0.0
    loc[zero] = np.inf
    nz = ~zero
    q = zs[nz]
    loc[nz] = 1.0 / q + q / 3.0 - q ** 3 / 45.0 + 2.0 * q ** 5 / 945.0
    out[small] = loc
    out[~small] = 1.0 / np.tanh(z[~small])
    return out


def kelvin_mcfarlane_y2_over_a2(X: np.ndarray | float, B: float = 0.0) -> np.ndarray:
    """Explicit dimensionless Kelvin/M'Farlane curve.

        Y^2 = 2 X coth((X+B)/2) - 1 - X^2.

    For B=0 the X=0 singularity is removable and the exact limit is Y^2=3.
    The removable branch is evaluated before coth, so the analytic oracle runs
    without divide-by-zero warnings.
    """
    xin = np.asarray(X, float)
    shape = xin.shape
    xx = np.atleast_1d(xin).astype(float, copy=False)
    y2 = np.empty_like(xx)
    removable = (abs(float(B)) < 1.0e-15) & (np.abs(xx) < 1.0e-7)
    if np.any(removable):
        q = xx[removable]
        # Series: 3 - 2 X^2/3 - X^4/180 + O(X^6).
        y2[removable] = 3.0 - (2.0 / 3.0) * q * q - q ** 4 / 180.0
    rest = ~removable
    if np.any(rest):
        xr = xx[rest]
        z = 0.5 * (xr + float(B))
        y2[rest] = 2.0 * xr * _coth(z) - 1.0 - xr * xr
    return y2.reshape(shape) if shape else np.asarray(y2[0])


def _bisect(fn, lo: float, hi: float, n: int = 90) -> float:
    flo, fhi = float(fn(lo)), float(fn(hi))
    if flo == 0.0:
        return float(lo)
    if fhi == 0.0:
        return float(hi)
    if flo * fhi > 0.0:
        raise ValueError("bisection interval does not bracket a root")
    a, b = float(lo), float(hi)
    for _ in range(int(n)):
        m = 0.5 * (a + b)
        fm = float(fn(m))
        if flo * fm <= 0.0:
            b, fhi = m, fm
        else:
            a, flo = m, fm
    return 0.5 * (a + b)


def kelvin_oracle() -> Dict[str, float | bool | str]:
    """Numerically validate the detector against Kelvin's analytic dipole case."""
    a = 1.0
    gamma = 1.0
    U = kelvin_pair_translation(a, gamma)

    def vy_rel(y: float) -> float:
        v = kelvin_point_vortex_pair_velocity(np.array([[0.0, y]]), a, gamma)[0]
        return float(v[1] - U)

    ystag = _bisect(vy_rel, 0.05, 4.0)
    ystag_exact = math.sqrt(3.0)

    def edge_fn(x: float) -> float:
        return float(kelvin_mcfarlane_y2_over_a2(np.array([x]), 0.0)[0])

    xedge = _bisect(edge_fn, 1.05, 3.0)
    xedge_ref = 2.087253791

    # Verify that the explicit curve satisfies the original implicit equation.
    xs = np.linspace(-0.98 * xedge, 0.98 * xedge, 121)
    y2 = kelvin_mcfarlane_y2_over_a2(xs, 0.0)
    ok = y2 >= -1.0e-12
    ys = np.sqrt(np.maximum(y2[ok], 0.0))
    residual = kelvin_streamline_residual(xs[ok], ys, 1.0, 0.0)
    max_res = float(np.max(np.abs(residual))) if residual.size else float("inf")

    pass_flag = (
        abs(ystag - ystag_exact) < 2.0e-10
        and abs(xedge - xedge_ref) < 2.0e-8
        and max_res < 5.0e-10
    )
    return {
        "oracle": "Kelvin-McFarlane opposite-vortex carried-fluid separatrix",
        "translation_U": U,
        "stagnation_y_over_a_numeric": ystag,
        "stagnation_y_over_a_exact": ystag_exact,
        "stagnation_abs_error": abs(ystag - ystag_exact),
        "separatrix_x_edge_over_a_numeric": xedge,
        "separatrix_x_edge_reference": xedge_ref,
        "separatrix_x_edge_abs_error": abs(xedge - xedge_ref),
        "max_implicit_streamline_residual": max_res,
        "status": "PASS" if pass_flag else "FAIL",
        "pass": bool(pass_flag),
    }


# ---------------------------------------------------------------------------
# Geometry-only hole axis and co-moving field
# ---------------------------------------------------------------------------

def _canonical_axis_sign(axis: np.ndarray) -> np.ndarray:
    a = np.asarray(axis, float)
    a /= max(float(np.linalg.norm(a)), EPS)
    j = int(np.argmax(np.abs(a)))
    if a[j] < 0.0:
        a = -a
    return a


def _fibonacci_directions(n: int) -> np.ndarray:
    n = max(int(n), 12)
    ga = PI * (3.0 - math.sqrt(5.0))
    out = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        p = i * ga
        out.append((r * math.cos(p), r * math.sin(p), z))
    return np.asarray(out, float)


def estimate_hole_axis(carrier: CurveSet, n_dirs: int = 160, clearance_quantile: float = 0.02) -> Dict[str, object]:
    """Find the widest straight central passage using carrier geometry only.

    This deliberately does not inspect the private carrier label or the thread
    geometry.  The axis is the direction through the carrier centroid that
    maximizes a low quantile of perpendicular centerline distance.
    """
    x = np.asarray(carrier.points, float)
    center = np.mean(x, axis=0)
    q = float(np.clip(clearance_quantile, 0.0, 0.20))
    rel = x - center
    best_axis = None
    best_clear = -np.inf
    best_min = -np.inf
    for axis in _fibonacci_directions(n_dirs):
        proj = rel @ axis
        radial = rel - np.outer(proj, axis)
        d = np.linalg.norm(radial, axis=1)
        clear = float(np.quantile(d, q))
        dmin = float(np.min(d))
        # Quantile is robust to one discretization vertex grazing the axis;
        # minimum is a deterministic tie breaker.
        if (clear, dmin) > (best_clear, best_min):
            best_clear, best_min = clear, dmin
            best_axis = axis.copy()
    axis = _canonical_axis_sign(best_axis if best_axis is not None else np.array([0.0, 0.0, 1.0]))
    scale = float(np.sqrt(np.mean(np.sum(rel * rel, axis=1))))
    return {
        "center": center,
        "axis": axis,
        "clearance_quantile": best_clear,
        "clearance_min": best_min,
        "scale_rms": scale,
        "n_dirs": int(n_dirs),
        "quantile": q,
    }


def _orthobasis(axis: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    ez = _canonical_axis_sign(axis)
    seed = np.array([1.0, 0.0, 0.0]) if abs(ez[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
    e1 = seed - ez * float(np.dot(seed, ez))
    e1 /= max(float(np.linalg.norm(e1)), EPS)
    e2 = np.cross(ez, e1)
    return e1, e2, ez


def _sunflower_disk(center: np.ndarray, axis: np.ndarray, radius: float, n: int) -> np.ndarray:
    e1, e2, _ = _orthobasis(axis)
    n = max(int(n), 1)
    ga = PI * (3.0 - math.sqrt(5.0))
    pts = []
    for i in range(n):
        rr = float(radius) * math.sqrt((i + 0.35) / n)
        ph = i * ga
        pts.append(np.asarray(center, float) + rr * (math.cos(ph) * e1 + math.sin(ph) * e2))
    return np.asarray(pts, float)


def _carrier_view(cs: CurveSet, nc: int) -> CurveSet:
    return CurveSet.from_components(cs.components()[: int(nc)])


def _rigid_frame(cs: CurveSet, gammas: np.ndarray, nc: int, core: float, core_model: str, c0: float):
    carrier = _carrier_view(cs, nc)
    vv = vortex_velocity(
        cs.points,
        cs.offsets,
        np.asarray(gammas, float),
        float(core),
        CORE_DELTAS.get(str(core_model).lower(), 0.615),
        float(c0),
    )
    vc = np.asarray(vv[: carrier.points.shape[0]], float)
    _w, U, Om = shape_velocity(carrier, vc)
    vrms = float(np.sqrt(np.mean(np.sum(vc * vc, axis=1))))
    return carrier, np.asarray(U, float), np.asarray(Om, float), vrms


def _relative_field(samples: np.ndarray, cs: CurveSet, gammas: np.ndarray, core: float, center: np.ndarray, U: np.ndarray, Om: np.ndarray) -> np.ndarray:
    x = np.asarray(samples, float)
    u = field_velocity(x, cs.points, cs.offsets, np.asarray(gammas, float), float(core))
    rigid = U[None, :] + np.cross(np.broadcast_to(Om, x.shape), x - center[None, :])
    return np.asarray(u, float) - rigid


def _axis_stagnation_scan(cs: CurveSet, gammas: np.ndarray, core: float, center: np.ndarray, axis: np.ndarray, U: np.ndarray, Om: np.ndarray, extent: float, n: int) -> Dict[str, object]:
    n = max(int(n), 9)
    z = np.linspace(-float(extent), float(extent), n)
    pts = center[None, :] + z[:, None] * axis[None, :]
    vel = _relative_field(pts, cs, gammas, core, center, U, Om)
    f = vel @ axis
    roots = []
    for i in range(n - 1):
        if f[i] == 0.0:
            roots.append(float(z[i]))
        elif f[i] * f[i + 1] < 0.0:
            # Linear interpolation is only a diagnostic locator; the sign-change
            # count itself is the robust observable.
            zz = z[i] - f[i] * (z[i + 1] - z[i]) / (f[i + 1] - f[i])
            roots.append(float(zz))
    return {
        "axis_z": z.tolist(),
        "axis_u_parallel": f.tolist(),
        "stagnation_count": int(len(roots)),
        "stagnation_z": roots,
    }


def _integrate_frozen(
    seeds: np.ndarray,
    cs: CurveSet,
    gammas: np.ndarray,
    core: float,
    center: np.ndarray,
    axis: np.ndarray,
    U: np.ndarray,
    Om: np.ndarray,
    path_horizon: float,
    ds_max: float,
    radius_scale: float,
    gate_extent: float,
    direction: float,
    mode: str,
) -> Dict[str, object]:
    """Integrate frozen *streamline geometry* using arclength parameterization.

    For a steady co-moving field, material trajectories and streamlines have the
    same geometric curves wherever |u_rel| != 0.  Reparameterizing by arclength,

        dx/ds = u_rel / |u_rel|,

    makes the connectivity test independent of an arbitrary observation time and
    remains well conditioned when the through-flow is slow.  True/near stagnation
    is detected separately by the axial scan and by a speed floor here.
    """
    x = np.asarray(seeds, float).copy()
    n = len(x)
    active = np.ones(n, dtype=bool)
    through = np.zeros(n, dtype=bool)
    side = np.zeros(n, dtype=bool)
    upstream = np.zeros(n, dtype=bool)
    stalled = np.zeros(n, dtype=bool)
    s_path = 0.0
    steps = 0
    side_radius = 1.35 * max(float(radius_scale), EPS)
    max_steps = 12000
    speed_floor = 1.0e-11

    while s_path < path_horizon - 1.0e-15 and np.any(active):
        ids = np.where(active)[0]
        xa = x[ids]
        v1 = _relative_field(xa, cs, gammas, core, center, U, Om)
        sp1 = np.linalg.norm(v1, axis=1)
        stall1 = sp1 <= speed_floor
        if np.any(stall1):
            stalled[ids[stall1]] = True
            active[ids[stall1]] = False
        ids = ids[~stall1]
        if not len(ids):
            break
        xa = x[ids]
        v1 = v1[~stall1]
        sp1 = sp1[~stall1]
        d1 = v1 / sp1[:, None]
        ds = min(float(ds_max), float(path_horizon - s_path))
        mid = xa + 0.5 * ds * d1
        v2 = _relative_field(mid, cs, gammas, core, center, U, Om)
        sp2 = np.linalg.norm(v2, axis=1)
        stall2 = sp2 <= speed_floor
        safe = np.maximum(sp2, speed_floor)
        d2 = v2 / safe[:, None]
        x[ids] = xa + ds * d2
        if np.any(stall2):
            stalled[ids[stall2]] = True
            active[ids[stall2]] = False

        rel = x[ids] - center[None, :]
        z = rel @ axis
        radial = np.linalg.norm(rel - np.outer(z, axis), axis=1)
        side_now = radial > side_radius
        if mode == "through":
            signed_z = direction * z
            through_now = signed_z >= gate_extent
            upstream_now = signed_z <= -1.20 * gate_extent
        else:
            through_now = np.abs(z) >= gate_extent
            upstream_now = np.zeros_like(through_now)
        side[ids[side_now]] = True
        through[ids[through_now]] = True
        upstream[ids[upstream_now]] = True
        done = side_now | through_now | upstream_now | stall2
        active[ids[done]] = False
        s_path += ds
        steps += 1
        if steps >= max_steps:
            break

    rel = x - center[None, :]
    z = rel @ axis
    radial = np.linalg.norm(rel - np.outer(z, axis), axis=1)
    resident = (~side) & (~through) & (np.abs(z) < gate_extent) & (radial <= side_radius)
    return {
        "through_fraction": float(np.mean(through)) if n else float("nan"),
        "side_escape_fraction": float(np.mean(side)) if n else float("nan"),
        "upstream_return_fraction": float(np.mean(upstream)) if n else float("nan"),
        "resident_fraction": float(np.mean(resident)) if n else float("nan"),
        "stalled_fraction": float(np.mean(stalled)) if n else float("nan"),
        "steps": int(steps),
        "actual_arclength": float(s_path),
        "target_arclength": float(path_horizon),
        "final_mean_abs_z": float(np.mean(np.abs(z))) if n else float("nan"),
        "final_mean_radius": float(np.mean(radial)) if n else float("nan"),
    }

def frozen_hole_metrics(cs: CurveSet, gammas: np.ndarray, nc: int, cfg: dict, *, reduced: bool = False) -> Dict[str, object]:
    core = float(cfg["core"])
    model = str(cfg.get("core_model", "gp"))
    c0 = float(cfg.get("vortexlab_c0", 0.1395))
    carrier, U, Om, vrms = _rigid_frame(cs, gammas, nc, core, model, c0)
    geo = estimate_hole_axis(
        carrier,
        int(cfg.get("hole_axis_directions_reduced" if reduced else "hole_axis_directions", 72 if reduced else 160)),
        float(cfg.get("hole_axis_clearance_quantile", 0.02)),
    )
    center = np.asarray(geo["center"], float)
    axis = np.asarray(geo["axis"], float)
    clearance = max(float(geo["clearance_quantile"]), 0.20 * core)
    scale = max(float(geo["scale_rms"]), core)
    radius = min(
        float(cfg.get("hole_seed_radius_fraction", 0.58)) * clearance,
        float(cfg.get("hole_seed_radius_scale_cap", 0.38)) * scale,
    )
    gate_extent = float(cfg.get("hole_gate_extent_scale", 1.15)) * scale
    nseed = int(cfg.get("hole_tracer_seeds_reduced" if reduced else "hole_tracer_seeds", 7 if reduced else 19))
    # Frozen topology is a streamline-connectivity question.  Parameterize by
    # arclength rather than arbitrary physical observation time.
    path_scale = float(cfg.get("hole_streamline_arclength_scale_reduced" if reduced else "hole_streamline_arclength_scale", 5.0 if reduced else 8.0))
    path_horizon = path_scale * scale
    ds_fraction = float(cfg.get("hole_streamline_ds_fraction_reduced" if reduced else "hole_streamline_ds_fraction", 0.04 if reduced else 0.025))
    ds_max = ds_fraction * max(min(clearance, scale), 0.25 * core)

    mid = _sunflower_disk(center, axis, radius, nseed)
    u_mid = _relative_field(mid, cs, gammas, core, center, U, Om)
    upar = u_mid @ axis
    mean_abs = float(np.mean(np.abs(upar))) if len(upar) else 0.0
    coherence = abs(float(np.mean(upar))) / max(mean_abs, 1.0e-14)
    center_u = _relative_field(center[None, :], cs, gammas, core, center, U, Om)[0]
    center_upar = float(np.dot(center_u, axis))
    direction = 1.0 if float(np.mean(upar)) >= 0.0 else -1.0

    entry_center = center - direction * 0.82 * gate_extent * axis
    entry = _sunflower_disk(entry_center, axis, radius, nseed)
    through = _integrate_frozen(
        entry, cs, gammas, core, center, axis, U, Om,
        path_horizon, ds_max, clearance, gate_extent, direction, "through",
    )
    resident = _integrate_frozen(
        mid, cs, gammas, core, center, axis, U, Om,
        path_horizon, ds_max, clearance, gate_extent, direction, "resident",
    )
    stag = _axis_stagnation_scan(
        cs, gammas, core, center, axis, U, Om, gate_extent,
        int(cfg.get("hole_axis_stagnation_samples_reduced" if reduced else "hole_axis_stagnation_samples", 25 if reduced else 61)),
    )

    through_frac = float(through["through_fraction"])
    resident_frac = float(resident["resident_fraction"])
    side_frac = 0.5 * (float(through["side_escape_fraction"]) + float(resident["side_escape_fraction"]))
    through_pass = float(cfg.get("hole_through_fraction_pass", 0.50))
    resident_pass = float(cfg.get("hole_resident_fraction_pass", 0.72))
    side_max = float(cfg.get("hole_side_escape_max", 0.35))
    pinch_norm = abs(center_upar) / max(vrms, 1.0e-14)
    pinch_cut = float(cfg.get("hole_pinch_center_speed_fraction", 0.035))

    if through_frac >= through_pass and side_frac <= side_max:
        cls = "OPEN_CHANNEL"
    elif resident_frac >= resident_pass and side_frac <= side_max:
        cls = "CAPTURED_ATMOSPHERE"
    elif pinch_norm <= pinch_cut and (int(stag["stagnation_count"]) >= 1 or coherence >= float(cfg.get("hole_pinch_coherence_min", 0.50))):
        # At the topology-changing point a pair of axial stagnation points may
        # coalesce into a double root, so a sign-change counter can legitimately
        # return zero.  Near-zero center speed plus coherent axial flow catches
        # that degenerate pinch without requiring a target Kelvin critical value.
        cls = "TRANSITIONAL_PINCH"
    else:
        cls = "VISUAL_ONLY_OR_INCOHERENT"

    Upar = float(np.dot(U, axis))
    chi_valid = abs(Upar) >= float(cfg.get("hole_chi_min_translation_fraction", 0.05)) * max(vrms, 1.0e-14)
    # Generic diagnostic only.  It reduces to Kelvin's u_c/U order parameter
    # only when a single meaningful translation axis exists.
    induced_center_upar = float(np.dot(field_velocity(center[None, :], cs.points, cs.offsets, np.asarray(gammas, float), core)[0], axis))
    chi = induced_center_upar / Upar if chi_valid else float("nan")

    support = max(through_frac, resident_frac)
    support *= max(0.0, 1.0 - 0.5 * side_frac)
    return {
        "transport_class": cls,
        "hole_axis": axis.tolist(),
        "hole_center": center.tolist(),
        "hole_clearance": float(clearance),
        "hole_clearance_min": float(geo["clearance_min"]),
        "carrier_scale_rms": float(scale),
        "hole_radius_seed": float(radius),
        "gate_extent": float(gate_extent),
        "rigid_U": U.tolist(),
        "rigid_Omega": Om.tolist(),
        "carrier_velocity_rms": float(vrms),
        "center_relative_u_parallel": center_upar,
        "midplane_axial_coherence": float(coherence),
        "through": through,
        "resident": resident,
        "support_fraction": float(support),
        "mean_side_escape_fraction": float(side_frac),
        "axis_stagnation": stag,
        "chi_hole_generic": float(chi),
        "chi_hole_generic_valid": bool(chi_valid),
        "chi_guard": "Generic u_center/U diagnostic; Kelvin u_c/U interpretation is valid only for a single coherent translation axis.",
    }


# ---------------------------------------------------------------------------
# Finite carrier evolution and perturbation persistence
# ---------------------------------------------------------------------------

def _align_full_to_reference(final_cs: CurveSet, initial_carrier: CurveSet, nc: int) -> CurveSet:
    final_carrier = _carrier_view(final_cs, nc)
    R, tr = kabsch(final_carrier.points, initial_carrier.points)
    return CurveSet(final_cs.points @ R.T + tr, final_cs.offsets.copy())


def _evolve_snapshot(cs: CurveSet, gammas: np.ndarray, nc: int, cfg: dict) -> Tuple[CurveSet, Dict[str, object]]:
    # Local imports avoid a module cycle: dynamics optionally calls us.
    from .dynamics import cfl_dt, physical_gap, rk4

    core = float(cfg["core"])
    model = str(cfg.get("core_model", "gp"))
    c0 = float(cfg.get("vortexlab_c0", 0.1395))
    nC = int(cfg["carrier_n"])
    nT = int(cfg["thread_n"])
    gamma0 = max(abs(float(np.asarray(gammas, float)[0])), 1.0e-14)
    tau_end = float(cfg.get("hole_dynamic_tau", 0.055))
    t_end = tau_end / gamma0
    x = CurveSet(cs.points.copy(), cs.offsets.copy())
    t = 0.0
    steps = 0
    contact = False
    threshold = float(cfg.get("contact_core_multiple", 2.05)) * core
    max_steps = int(cfg.get("hole_dynamic_max_steps", 4500))
    while t < t_end - 1.0e-15:
        if physical_gap(x, gammas, int(cfg.get("contact_adjacency", 3))) < threshold:
            contact = True
            break
        dt = min(
            cfl_dt(x, gammas, core, model, c0, float(cfg.get("cfl_safety", 0.32)), float(cfg.get("hole_dynamic_dt_max", cfg.get("dt_max", 0.008)))),
            t_end - t,
        )
        if dt < float(cfg.get("dt_min", 1.0e-7)):
            break
        x = rk4(x, gammas, core, dt, nc, nC, nT, model, c0)
        t += dt
        steps += 1
        if steps >= max_steps:
            break
    full = (not contact) and t >= t_end * (1.0 - 1.0e-9)
    status = "PASS_FULL_HORIZON" if full else ("FAIL_CONTACT" if contact else "FAIL_TRUNCATED")
    return x, {
        "dynamic_status": status,
        "actual_tau_end": float(t * gamma0),
        "target_tau_end": float(tau_end),
        "steps": int(steps),
        "contact_stop": bool(contact),
    }


def _perturbed_curve(cs: CurveSet, nc: int, delta_flat: np.ndarray) -> CurveSet:
    carrier = _carrier_view(cs, nc)
    ncp = carrier.points.shape[0]
    pts = cs.points.copy()
    pts[:ncp] += np.asarray(delta_flat, float).reshape(ncp, 3)
    return CurveSet(pts, cs.offsets.copy())


def analyze_hole_transport(cs: CurveSet, gammas: np.ndarray, nc: int, cfg: dict) -> Dict[str, object]:
    initial_carrier = _carrier_view(cs, nc)
    initial = frozen_hole_metrics(cs, gammas, nc, cfg, reduced=False)

    evolved, dyn = _evolve_snapshot(cs, gammas, nc, cfg)
    aligned = _align_full_to_reference(evolved, initial_carrier, nc)
    final = frozen_hole_metrics(aligned, gammas, nc, cfg, reduced=False) if dyn["dynamic_status"] == "PASS_FULL_HORIZON" else None

    clearance0 = max(float(initial["hole_clearance"]), EPS)
    if final is not None:
        clearance_ratio = float(final["hole_clearance"]) / clearance0
        class_persist = float(final["transport_class"] == initial["transport_class"])
        final_support = float(final["support_fraction"])
        final_side = float(final["mean_side_escape_fraction"])
    else:
        clearance_ratio = 0.0
        class_persist = 0.0
        final_support = 0.0
        final_side = 1.0

    # Preregistered normal-mode perturbations.  The geometry is perturbed before
    # any class is known; no favorable sign or mode is selected post hoc.
    B, labels = deformation_basis(
        initial_carrier,
        int(cfg.get("hole_perturb_mode_m_min", 2)),
        int(cfg.get("hole_perturb_mode_m_max", 4)),
        int(cfg.get("hole_perturb_modes", 3)),
    )
    eps = float(cfg.get("hole_perturb_eps", cfg.get("mode_eps", 0.005)))
    perturb = []
    same = 0
    robust = 0
    total = 0
    for j in range(B.shape[1]):
        for sign in (-1.0, 1.0):
            total += 1
            pert = _perturbed_curve(cs, nc, sign * eps * B[:, j])
            try:
                m = frozen_hole_metrics(pert, gammas, nc, cfg, reduced=True)
                same_flag = m["transport_class"] == initial["transport_class"]
                robust_flag = m["transport_class"] in ROBUST_BASE_CLASSES
                same += int(same_flag)
                robust += int(robust_flag)
                perturb.append({
                    "mode": labels[j],
                    "sign": int(sign),
                    "transport_class": m["transport_class"],
                    "support_fraction": float(m["support_fraction"]),
                    "hole_clearance": float(m["hole_clearance"]),
                    "same_class": bool(same_flag),
                    "robust_class": bool(robust_flag),
                    "status": "OK",
                })
            except Exception as exc:
                perturb.append({"mode": labels[j], "sign": int(sign), "status": "ERROR", "error": repr(exc)})
    same_frac = float(same / total) if total else float("nan")
    robust_frac = float(robust / total) if total else float("nan")

    initial_support = float(initial["support_fraction"])
    clearance_support = float(np.clip(clearance_ratio, 0.0, 1.0))
    perturb_support = robust_frac if np.isfinite(robust_frac) else 0.0
    same_support = same_frac if np.isfinite(same_frac) else 0.0
    # Score components are dimensionless and target-independent.  The weights
    # are preregistered in code/config and fixed before identity reveal.
    score = (
        0.22 * initial_support
        + 0.22 * final_support
        + 0.18 * clearance_support
        + 0.18 * perturb_support
        + 0.10 * same_support
        + 0.10 * class_persist
    )
    mean_side = 0.5 * (float(initial["mean_side_escape_fraction"]) + final_side)
    score *= max(0.0, 1.0 - 0.45 * mean_side)
    score = float(np.clip(score, 0.0, 1.0))
    cost = max(1.0e-8, 1.0 - score)

    robust_min_pert = float(cfg.get("hole_perturb_robust_fraction_pass", 0.66))
    same_min_pert = float(cfg.get("hole_perturb_same_class_fraction_pass", robust_min_pert))
    clear_min = float(cfg.get("hole_dynamic_clearance_ratio_pass", 0.70))
    init_class = str(initial["transport_class"])
    final_class = str(final["transport_class"]) if final is not None else "NO_FINAL_CLASS"
    if (
        init_class == "OPEN_CHANNEL"
        and final_class == "OPEN_CHANNEL"
        and perturb_support >= robust_min_pert
        and same_support >= same_min_pert
        and clearance_ratio >= clear_min
        and dyn["dynamic_status"] == "PASS_FULL_HORIZON"
    ):
        verdict = "ROBUST_OPEN_THREADED_CHANNEL"
    elif (
        init_class == "CAPTURED_ATMOSPHERE"
        and final_class == "CAPTURED_ATMOSPHERE"
        and perturb_support >= robust_min_pert
        and same_support >= same_min_pert
        and clearance_ratio >= clear_min
        and dyn["dynamic_status"] == "PASS_FULL_HORIZON"
    ):
        verdict = "ROBUST_CAPTURED_VORTEX_ATMOSPHERE"
    elif init_class == "TRANSITIONAL_PINCH" or final_class == "TRANSITIONAL_PINCH" or (final is not None and init_class != final_class):
        verdict = "CRITICAL_OR_TOPOLOGY_SWITCHING"
    else:
        verdict = "VISUAL_HOLE_NOT_DYNAMICALLY_ESTABLISHED"

    return {
        "question": "Is the central threaded hole a robust dynamical structure or only a visual centerline gap?",
        "identity_blind": True,
        "initial": initial,
        "final": final,
        "dynamic": dyn,
        "perturbations": perturb,
        "initial_transport_class": init_class,
        "final_transport_class": final_class,
        "clearance_ratio_final_over_initial": float(clearance_ratio),
        "class_persistence": float(class_persist),
        "perturb_same_class_fraction": float(same_frac),
        "perturb_robust_class_fraction": float(robust_frac),
        "hole_robustness_score": score,
        "hole_robustness_cost": float(cost),
        "hole_geometry_collapse_cost": float(max(0.0, 1.0 - min(clearance_ratio, 1.0))),
        "hole_class_instability_cost": float(max(0.0, 1.0 - 0.5 * (class_persist + same_support))),
        "hole_lagrangian_incoherence_cost": float(max(0.0, 1.0 - 0.5 * (initial_support + final_support))),
        "verdict": verdict,
        "interpretation_guard": (
            "A positive geometric clearance is not evidence of a dynamical hole. "
            "Only Lagrangian transport class, finite-evolution persistence, and preregistered perturbation persistence enter the robustness verdict."
        ),
    }

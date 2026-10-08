from __future__ import annotations
import math
import numpy as np
from .geometry import tangents, vector_area, bounding_radius

PI = math.pi


def _segments(p: np.ndarray):
    p = np.asarray(p, dtype=np.float64)
    q = np.roll(p, -1, axis=0)
    dl = q - p
    mid = 0.5 * (p + q)
    return mid, dl


def biot_savart(source: np.ndarray, query: np.ndarray, gamma: float = 1.0, core: float = 0.0, chunk: int = 256) -> np.ndarray:
    mid, dl = _segments(source)
    query = np.asarray(query, dtype=np.float64)
    out = np.zeros_like(query)
    a2 = float(core) ** 2
    scale = float(gamma) / (4.0 * PI)
    for i0 in range(0, len(query), chunk):
        x = query[i0:i0 + chunk]
        r = x[:, None, :] - mid[None, :, :]
        r2 = np.einsum("ijk,ijk->ij", r, r)
        if core == 0.0:
            den = np.maximum(r2, 1e-300) ** 1.5
            den[r2 < 1e-28] = np.inf
        else:
            den = (r2 + a2) ** 1.5
        cr = np.cross(dl[None, :, :], r)
        out[i0:i0 + chunk] = scale * np.sum(cr / den[:, :, None], axis=1)
    return out


def total_velocity(comps: list[np.ndarray], queries: np.ndarray | None = None, core: float = 0.0) -> list[np.ndarray] | np.ndarray:
    if queries is None:
        outs = []
        for q in comps:
            v = np.zeros_like(q)
            for src in comps:
                v += biot_savart(src, q, 1.0, core)
            outs.append(v)
        return outs
    q = np.asarray(queries, dtype=np.float64)
    v = np.zeros_like(q)
    for src in comps:
        v += biot_savart(src, q, 1.0, core)
    return v


def interaction_energy(a: np.ndarray, b: np.ndarray, core: float) -> float:
    ma, dla = _segments(a)
    mb, dlb = _segments(b)
    r = ma[:, None, :] - mb[None, :, :]
    den = np.sqrt(np.einsum("ijk,ijk->ij", r, r) + float(core) ** 2)
    dot = np.einsum("ik,jk->ij", dla, dlb)
    return float(np.sum(dot / np.maximum(den, 1e-300)) / (4.0 * PI))


def total_energy_length(comps: list[np.ndarray], core: float) -> float:
    s = 0.0
    for a in comps:
        for b in comps:
            s += interaction_energy(a, b, core)
    return 0.5 * s


def relative_equilibrium(comps: list[np.ndarray], vels: list[np.ndarray]) -> dict:
    pts = np.vstack(comps)
    vv = np.vstack(vels)
    tt = np.vstack([tangents(p) for p in comps])
    c = pts.mean(axis=0)
    rows = []
    rhs = []
    for x, v, t in zip(pts, vv, tt):
        P = np.eye(3) - np.outer(t, t)
        r = x - c
        S = np.array([[0, -r[2], r[1]], [r[2], 0, -r[0]], [-r[1], r[0], 0]], dtype=float)
        rows.append(np.hstack([P, -P @ S]))
        rhs.append(P @ v)
    A = np.vstack(rows)
    b = np.concatenate(rhs)
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    U = coef[:3]
    Om = coef[3:]
    res = []
    base = []
    for x, v, t in zip(pts, vv, tt):
        P = np.eye(3) - np.outer(t, t)
        rig = U + np.cross(Om, x - c)
        res.append(P @ (v - rig))
        base.append(P @ v)
    res = np.vstack(res)
    base = np.vstack(base)
    den = np.linalg.norm(base)
    return {
        "normal_nrmse": float(np.linalg.norm(res) / max(float(den), 1e-300)),
        "translation": U.tolist(),
        "omega": Om.tolist(),
        "normal_velocity_rms": float(np.sqrt(np.mean(np.sum(base * base, axis=1)))),
        "residual_rms": float(np.sqrt(np.mean(np.sum(res * res, axis=1)))),
    }


def orientation_symmetry(comps: list[np.ndarray], core: float) -> float:
    v = total_velocity(comps, None, core)
    rev = [p[::-1].copy() for p in comps]
    vr = total_velocity(rev, None, core)
    num = 0.0
    den = 0.0
    for a, b in zip(v, vr):
        num += float(np.sum((b[::-1] + a) ** 2))
        den += float(np.sum(a * a))
    return float(np.sqrt(num / max(den, 1e-300)))


def mirror_symmetry(comps: list[np.ndarray], core: float) -> float:
    M = np.diag([-1.0, 1.0, 1.0])
    v = total_velocity(comps, None, core)
    mir = [p @ M.T for p in comps]
    vm = total_velocity(mir, None, core)
    num = 0.0
    den = 0.0
    for a, b in zip(v, vm):
        target = -(a @ M.T)
        num += float(np.sum((b - target) ** 2))
        den += float(np.sum(target * target))
    return float(np.sqrt(num / max(den, 1e-300)))


def gauss_linking(a: np.ndarray, b: np.ndarray) -> float:
    ma, dla = _segments(a)
    mb, dlb = _segments(b)
    r = ma[:, None, :] - mb[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", r, r)
    cross = np.cross(dla[:, None, :], dlb[None, :, :])
    num = np.einsum("ijk,ijk->ij", cross, r)
    den = np.maximum(r2, 1e-300) ** 1.5
    num = np.where(r2 < 1e-28, 0.0, num)
    return float(np.sum(num / den) / (4.0 * PI))


def _frame(t: np.ndarray):
    axes = np.eye(3)
    ref = axes[np.argmin(np.abs(axes @ t))]
    n1 = np.cross(t, ref)
    n1 /= np.linalg.norm(n1)
    n2 = np.cross(t, n1)
    return n1, n2


def meridian_loop(p: np.ndarray, idx: int, radius: float, npts: int) -> np.ndarray:
    t = tangents(p)[idx]
    n1, n2 = _frame(t)
    ang = np.linspace(0.0, 2.0 * PI, int(npts), endpoint=False)
    return p[idx] + radius * (np.cos(ang)[:, None] * n1 + np.sin(ang)[:, None] * n2)


def holonomy_metrics(comps: list[np.ndarray], thickness: float, stations_per_component: int, loop_points: int, loop_radius_fraction: float) -> list[dict]:
    rows = []
    rad = loop_radius_fraction * thickness
    for ci, p in enumerate(comps):
        ids = np.linspace(0, len(p) - 1, stations_per_component, endpoint=False, dtype=int)
        for idx in ids:
            loop = meridian_loop(p, int(idx), rad, loop_points)
            q = np.roll(loop, -1, axis=0)
            mid = 0.5 * (loop + q)
            dl = q - loop
            v = total_velocity(comps, mid, 0.0)
            h = float(np.sum(v * dl))
            lk = sum(gauss_linking(src, loop) for src in comps)
            nearest = int(np.rint(lk))
            rows.append({
                "component": int(ci),
                "station": int(idx),
                "holonomy_over_Gamma": h,
                "gauss_linking": float(lk),
                "nearest_integer": nearest,
                "integer_abs_error": float(abs(h - nearest)),
            })
    return rows


def fibonacci_sphere(n: int) -> np.ndarray:
    n = int(n)
    i = np.arange(n, dtype=float)
    z = 1.0 - 2.0 * (i + 0.5) / n
    phi = (math.pi * (3.0 - math.sqrt(5.0))) * i
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    return np.column_stack([r * np.cos(phi), r * np.sin(phi), z])


def exterior_differential_metrics(comps: list[np.ndarray], radius_factor: float, n_dirs: int, fd_fraction: float) -> dict:
    c, R0 = bounding_radius(comps)
    R = max(radius_factor * R0, 1e-8)
    dirs = fibonacci_sphere(n_dirs)
    q = c + R * dirs
    h = max(fd_fraction * R, 1e-8)
    base = total_velocity(comps, q, 0.0)
    deriv = np.empty((len(q), 3, 3), dtype=float)  # d u_component / d x_axis
    for ax in range(3):
        d = np.zeros(3); d[ax] = h
        vp = total_velocity(comps, q + d, 0.0)
        vm = total_velocity(comps, q - d, 0.0)
        deriv[:, :, ax] = (vp - vm) / (2.0 * h)
    div = deriv[:, 0, 0] + deriv[:, 1, 1] + deriv[:, 2, 2]
    curl = np.column_stack([
        deriv[:, 2, 1] - deriv[:, 1, 2],
        deriv[:, 0, 2] - deriv[:, 2, 0],
        deriv[:, 1, 0] - deriv[:, 0, 1],
    ])
    speed = np.linalg.norm(base, axis=1)
    scale = np.maximum(speed / R, 1e-14)
    div_nd = np.abs(div) / scale
    curl_nd = np.linalg.norm(curl, axis=1) / scale
    valid = np.isfinite(div_nd) & np.isfinite(curl_nd) & np.isfinite(speed)
    return {
        "radius": float(R),
        "fd_step": float(h),
        "n_points": int(len(q)),
        "n_valid": int(np.count_nonzero(valid)),
        "median_speed": float(np.median(speed[valid])) if np.any(valid) else float("nan"),
        "max_div_dimensionless": float(np.max(div_nd[valid])) if np.any(valid) else float("inf"),
        "max_curl_dimensionless": float(np.max(curl_nd[valid])) if np.any(valid) else float("inf"),
        "median_div_dimensionless": float(np.median(div_nd[valid])) if np.any(valid) else float("inf"),
        "median_curl_dimensionless": float(np.median(curl_nd[valid])) if np.any(valid) else float("inf"),
    }


def _halton_sequence(n: int, base: int) -> np.ndarray:
    out = np.empty(n, dtype=float)
    for i in range(n):
        f = 1.0
        r = 0.0
        x = i + 1
        while x > 0:
            f /= base
            r += f * (x % base)
            x //= base
        out[i] = r
    return out


def halton_ball(n: int) -> np.ndarray:
    u = _halton_sequence(n, 2)
    v = _halton_sequence(n, 3)
    w = _halton_sequence(n, 5)
    r = u ** (1.0 / 3.0)
    z = 1.0 - 2.0 * v
    phi = 2.0 * PI * w
    xy = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    return np.column_stack([r * xy * np.cos(phi), r * xy * np.sin(phi), r * z])


def min_point_distance_to_centerlines(comps: list[np.ndarray], q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, float)
    best = np.full(len(q), np.inf)
    for p in comps:
        # midpoint-distance proxy is deterministic and sufficient for the registered source-zone mask.
        mid, _ = _segments(p)
        for i0 in range(0, len(q), 256):
            r = q[i0:i0 + 256, None, :] - mid[None, :, :]
            d = np.sqrt(np.min(np.einsum("ijk,ijk->ij", r, r), axis=1))
            best[i0:i0 + len(d)] = np.minimum(best[i0:i0 + len(d)], d)
    return best


def energy_partition(comps: list[np.ndarray], core: float, n_samples: int, domain_radius_factor: float, source_zone_core_multiples: float) -> dict:
    c, R0 = bounding_radius(comps)
    R = max(domain_radius_factor * R0, 1e-8)
    q = c + R * halton_ball(n_samples)
    v = total_velocity(comps, q, core)
    e = 0.5 * np.einsum("ij,ij->i", v, v)
    d = min_point_distance_to_centerlines(comps, q)
    source_mask = d <= source_zone_core_multiples * core
    ext = ~source_mask
    total = float(np.sum(e))
    ext_e = float(np.sum(e[ext]))
    return {
        "n_samples": int(n_samples),
        "domain_radius": float(R),
        "source_zone_radius": float(source_zone_core_multiples * core),
        "source_sample_fraction": float(np.mean(source_mask)),
        "exterior_energy_fraction": float(ext_e / max(total, 1e-300)),
        "mean_energy_density_proxy": float(np.mean(e)),
        "median_exterior_speed": float(np.median(np.linalg.norm(v[ext], axis=1))) if np.any(ext) else 0.0,
    }


def far_field_decay(comps: list[np.ndarray], radius_factors: list[float], n_dirs: int) -> dict:
    c, R0 = bounding_radius(comps)
    dirs = fibonacci_sphere(n_dirs)
    radii = np.asarray(radius_factors, dtype=float) * max(R0, 1e-12)
    rms = []
    for R in radii:
        q = c + R * dirs
        v = total_velocity(comps, q, 0.0)
        rms.append(float(np.sqrt(np.mean(np.sum(v * v, axis=1)))))
    rms = np.asarray(rms)
    ok = np.isfinite(rms) & (rms > 0) & np.isfinite(radii) & (radii > 0)
    if np.count_nonzero(ok) < 3:
        return {"eligible": False, "reason": "insufficient finite far-field samples", "radii": radii.tolist(), "rms_speed": rms.tolist()}
    x = np.log(radii[ok]); y = np.log(rms[ok])
    slope, intercept = np.polyfit(x, y, 1)
    yhat = slope * x + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, 1e-300)
    A = vector_area(comps)
    L = sum(float(np.sum(np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1))) for p in comps)
    area_ratio = float(np.linalg.norm(A) / max(L * L, 1e-300))
    return {
        "eligible": bool(area_ratio > 1e-5),
        "vector_area": A.tolist(),
        "vector_area_over_L2": area_ratio,
        "radii": radii.tolist(),
        "rms_speed": rms.tolist(),
        "velocity_decay_exponent": float(-slope),
        "fit_r2": float(r2),
        "derived_pressure_decay_exponent": float(-2.0 * slope),
        "derived_pressure_gradient_decay_exponent": float(-2.0 * slope + 1.0),
    }

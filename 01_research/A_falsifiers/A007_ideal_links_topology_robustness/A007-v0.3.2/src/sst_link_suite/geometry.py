from __future__ import annotations
import numpy as np
from scipy.optimize import minimize_scalar
from .models import SampledComponent, FourierComponent
from .fourier import coefficient_power, evaluate


def periodic_integral(values: np.ndarray) -> np.ndarray:
    return np.mean(values, axis=0) * (2.0 * np.pi)


def _curvature_at(component: FourierComponent, t: float) -> float:
    tt = np.array([np.mod(t, 2*np.pi)])
    d1 = evaluate(component, tt, 1)[0]
    d2 = evaluate(component, tt, 2)[0]
    return float(np.linalg.norm(np.cross(d1, d2)) / max(np.linalg.norm(d1)**3, 1e-300))


def refine_curvature_maximum(
    sample: SampledComponent,
    sampled_curvature: np.ndarray,
    peak_count: int = 16,
) -> dict:
    n = len(sample.t)
    power = coefficient_power(sample.component)
    active = np.flatnonzero(power > max(float(power.max())*1e-14, 1e-30))
    active_mode = int(active.max()) if active.size else 1
    search_n = max(n, min(8192, 8*max(active_mode, 1)))
    dense_t = np.arange(search_n, dtype=float)*(2*np.pi/search_n)
    dense_d1 = evaluate(sample.component, dense_t, 1)
    dense_d2 = evaluate(sample.component, dense_t, 2)
    dense_speed = np.linalg.norm(dense_d1, axis=1)
    dense_curvature = np.linalg.norm(np.cross(dense_d1, dense_d2), axis=1) / np.maximum(dense_speed**3, 1e-300)
    dt = 2*np.pi/search_n
    local = np.flatnonzero(
        (dense_curvature >= np.roll(dense_curvature, 1))
        & (dense_curvature >= np.roll(dense_curvature, -1))
    )
    if local.size == 0:
        local = np.array([int(np.argmax(dense_curvature))])
    local = local[np.argsort(dense_curvature[local])[::-1][:max(1, peak_count)]]
    candidates = []
    for idx in local:
        center = float(dense_t[idx])
        result = minimize_scalar(
            lambda x: -_curvature_at(sample.component, x),
            bounds=(center-dt, center+dt), method="bounded",
            options={"xatol": dt*1e-11, "maxiter": 200},
        )
        candidates.append((-float(result.fun), float(np.mod(result.x, 2*np.pi)), bool(result.success)))
    value, t, success = max(candidates, key=lambda row: row[0])
    sampled = float(np.max(sampled_curvature))
    return {
        "sampled_curvature_max_Dinv": sampled,
        "refined_curvature_max_Dinv": value,
        "refined_curvature_t_rad": t,
        "refined_curvature_gain_fraction": float((value-sampled)/max(abs(sampled), 1e-300)),
        "curvature_refinement_success": success,
        "curvature_refined_peak_seed_count": len(candidates),
        "curvature_search_grid_n": search_n,
        "curvature_active_mode_max": active_mode,
    }


def component_geometry(
    s: SampledComponent,
    curvature_refine_peaks: int = 16,
) -> dict:
    speed = np.linalg.norm(s.d1, axis=1)
    safe_speed = np.maximum(speed, 1e-15)
    cross = np.cross(s.d1, s.d2)
    cross_norm = np.linalg.norm(cross, axis=1)
    curvature = cross_norm / safe_speed**3
    torsion = np.einsum("ij,ij->i", cross, s.d3) / np.maximum(cross_norm**2, 1e-30)
    curvature_refined = refine_curvature_maximum(s, curvature, curvature_refine_peaks)
    ds_weight = speed
    length = float(periodic_integral(speed))
    centroid = periodic_integral(s.r * ds_weight[:, None]) / max(length, 1e-30)
    q = s.r - centroid
    inertia = periodic_integral(
        (np.sum(q*q, axis=1)[:, None, None] * np.eye(3)[None, :, :]
         - q[:, :, None] * q[:, None, :]) * ds_weight[:, None, None]
    ) / max(length, 1e-30)
    eigvals = np.linalg.eigvalsh(inertia)
    area_vector = 0.5 * periodic_integral(np.cross(s.r, s.d1))
    power = coefficient_power(s.component)
    nonzero = power[1:]
    p = nonzero / max(float(nonzero.sum()), 1e-30)
    spectral_entropy = float(-np.sum(p[p > 0] * np.log(p[p > 0])) / np.log(max(len(p), 2)))
    tail_start = max(2, int(np.ceil(0.8 * len(power))))
    tail_fraction = (
        float(power[tail_start:].sum() / max(power[1:].sum(), 1e-30))
        if tail_start < len(power) else 0.0
    )
    declared = s.component.declared_length
    return {
        "component": s.component.index,
        "declared_length_D": declared,
        "numerical_length_D": length,
        "standard_ropelength_radius": 2.0 * length,
        "length_relative_error": (length - declared) / max(abs(declared), 1e-30),
        "speed_min": float(speed.min()),
        "speed_max": float(speed.max()),
        "speed_cv": float(speed.std() / max(speed.mean(), 1e-30)),
        "curvature_min_Dinv": float(np.nanmin(curvature)),
        "curvature_mean_Dinv": float(np.average(curvature, weights=ds_weight)),
        "curvature_max_Dinv": curvature_refined["refined_curvature_max_Dinv"],
        "curvature_q95_Dinv": float(np.quantile(curvature, 0.95)),
        "curvature_q99_Dinv": float(np.quantile(curvature, 0.99)),
        **curvature_refined,
        "total_curvature": float(periodic_integral(curvature * ds_weight)),
        "bending_integral_Dinv": float(periodic_integral(curvature**2 * ds_weight)),
        "torsion_mean_Dinv": float(np.average(torsion, weights=ds_weight)),
        "torsion_abs_integral": float(periodic_integral(np.abs(torsion) * ds_weight)),
        "torsion_q99_abs_Dinv": float(np.quantile(np.abs(torsion), 0.99)),
        "centroid": centroid,
        "inertia_eigenvalues": eigvals,
        "planarity_ratio": float(eigvals[0] / max(eigvals.sum(), 1e-30)),
        "axisymmetry_gap": float(abs(eigvals[2] - eigvals[1]) / max(eigvals[2], 1e-30)),
        "area_vector_D2": area_vector,
        "spectral_entropy": spectral_entropy,
        "spectral_tail_fraction": tail_fraction,
        "active_mode_max": int(np.max(np.flatnonzero(power > max(power.max()*1e-14, 1e-30)))),
    }


def aggregate_geometry(component_results: list[dict], diameter: float) -> dict:
    lengths = np.asarray([x["numerical_length_D"] for x in component_results])
    declared = np.asarray([x["declared_length_D"] for x in component_results])
    return {
        "component_count": len(component_results),
        "declared_total_length_D": float(declared.sum()),
        "numerical_total_length_D": float(lengths.sum()),
        "standard_total_ropelength_radius": float(2.0 * lengths.sum() / diameter),
        "length_imbalance_cv": float(lengths.std() / max(lengths.mean(), 1e-30)),
        "max_curvature_Dinv": float(max(x["refined_curvature_max_Dinv"] for x in component_results)),
        "max_sampled_curvature_Dinv": float(max(x["sampled_curvature_max_Dinv"] for x in component_results)),
        "max_curvature_refinement_gain_fraction": float(max(x["refined_curvature_gain_fraction"] for x in component_results)),
        "total_bending_integral_Dinv": float(sum(x["bending_integral_Dinv"] for x in component_results)),
        "mean_spectral_entropy": float(np.mean([x["spectral_entropy"] for x in component_results])),
        "max_spectral_tail_fraction": float(max(x["spectral_tail_fraction"] for x in component_results)),
    }


def sst_scale_lift(aggregate: dict, component_results: list[dict], cfg: dict) -> dict:
    if not cfg.get("enabled", False):
        return {"enabled": False}
    rc = float(cfg["r_c_m"])
    vs = float(cfg["v_swirl_m_s"])
    Dm = float(cfg.get("diameter_m", 2.0 * rc))
    gamma0 = 2.0 * np.pi * rc * vs
    total_L_m = aggregate["numerical_total_length_D"] * Dm
    tube_volume = np.pi * (Dm/2.0)**2 * total_L_m
    return {
        "enabled": True,
        "diameter_m": Dm,
        "total_centerline_length_m": total_L_m,
        "tube_volume_m3": tube_volume,
        "characteristic_time_D_over_v_s": Dm / vs,
        "Gamma0_m2_s": gamma0,
        "Gamma0_over_area_sinv": gamma0 / (np.pi * (Dm/2.0)**2),
        "component_lengths_m": [x["numerical_length_D"] * Dm for x in component_results],
        "status": "Research-Track dimensional lift; geometry itself is dimensionless.",
    }

from __future__ import annotations
import numpy as np
from .models import SampledComponent
from .fourier import coefficient_power

def periodic_integral(values: np.ndarray) -> np.ndarray:
    return np.mean(values, axis=0) * (2.0 * np.pi)

def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Arclength-weighted quantile.

    np.quantile weights every parameter sample equally; for a non-uniform
    speed |gamma'(t)| that is not a quantile with respect to arclength.
    """
    order = np.argsort(values)
    v = np.asarray(values)[order]
    w = np.asarray(weights)[order]
    total = w.sum()
    if total <= 0:
        return float("nan")
    cdf = (np.cumsum(w) - 0.5 * w) / total
    return float(np.interp(q, cdf, v))

def curvature_spectral_tail(component, cutoff_fraction: float = 0.8) -> float:
    """n^4-weighted spectral tail fraction.

    Curvature depends on gamma'', so the truncation error in kappa is
    governed by sum n^4 |c_n|^2, not by the unweighted coefficient power.
    The unweighted tail can be O(1e-8) while the curvature is not yet
    converged by two orders of magnitude.
    """
    power = coefficient_power(component)
    n = np.arange(len(power), dtype=float)
    w = power * n**4
    if len(w) < 8:
        return 0.0
    start = max(1, int(cutoff_fraction * len(w)))
    denom = float(w[1:].sum())
    return float(w[start:].sum() / max(denom, 1e-30))

def component_geometry(s: SampledComponent, diameter: float = 1.0) -> dict:
    speed = np.linalg.norm(s.d1, axis=1)
    safe_speed = np.maximum(speed, 1e-15)
    cross = np.cross(s.d1, s.d2)
    cross_norm = np.linalg.norm(cross, axis=1)
    curvature = cross_norm / safe_speed**3
    torsion = np.einsum("ij,ij->i", cross, s.d3) / np.maximum(cross_norm**2, 1e-30)
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
    tail_start = max(1, int(0.8 * len(power)))
    tail_fraction = float(power[tail_start:].sum() / max(power[1:].sum(), 1e-30))
    declared = s.component.declared_length
    return {
        "component": s.component.index,
        "declared_length_D": declared,
        "numerical_length_D": length,
        "standard_ropelength_radius": 2.0 * length / max(diameter, 1e-30),
        "length_relative_error": (length - declared) / max(abs(declared), 1e-30),
        "speed_min": float(speed.min()),
        "speed_max": float(speed.max()),
        "speed_cv": float(speed.std() / max(speed.mean(), 1e-30)),
        "curvature_min_Dinv": float(np.nanmin(curvature)),
        "curvature_mean_Dinv": float(np.average(curvature, weights=ds_weight)),
        "curvature_max_Dinv": float(np.nanmax(curvature)),
        "curvature_q95_Dinv": weighted_quantile(curvature, ds_weight, 0.95),
        "curvature_q99_Dinv": weighted_quantile(curvature, ds_weight, 0.99),
        "total_curvature": float(periodic_integral(curvature * ds_weight)),
        "bending_integral_Dinv": float(periodic_integral(curvature**2 * ds_weight)),
        "torsion_mean_Dinv": float(np.average(torsion, weights=ds_weight)),
        "torsion_abs_integral": float(periodic_integral(np.abs(torsion) * ds_weight)),
        "torsion_q99_abs_Dinv": weighted_quantile(np.abs(torsion), ds_weight, 0.99),
        "centroid": centroid,
        "inertia_eigenvalues": eigvals,
        "planarity_ratio": float(eigvals[0] / max(eigvals.sum(), 1e-30)),
        "axisymmetry_gap": float(abs(eigvals[2] - eigvals[1]) / max(eigvals[2], 1e-30)),
        "area_vector_D2": area_vector,
        "spectral_entropy": spectral_entropy,
        "spectral_tail_fraction": tail_fraction,
        "curvature_spectral_tail_fraction": curvature_spectral_tail(s.component),
        "arclength_fraction_over_curvature_bound": float(
            (ds_weight * (curvature * diameter > 2.0)).sum() / max(ds_weight.sum(), 1e-30)
        ),
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
        "max_curvature_Dinv": float(max(x["curvature_max_Dinv"] for x in component_results)),
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

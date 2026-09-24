from __future__ import annotations
import numpy as np
from .geometry import length, curvature_stats, min_nonlocal_distance, rz, segment_stats


def curve_relative_error(A: np.ndarray, B: np.ndarray) -> float:
    return float(np.linalg.norm(A-B)/(np.linalg.norm(B)+1e-30))


def equivariance_residual(X_a: np.ndarray, X_b: np.ndarray, theta: float) -> float:
    target = X_a @ rz(theta).T
    target = target - target.mean(axis=0)
    X_b = X_b - X_b.mean(axis=0)
    return curve_relative_error(X_b, target)


def shape_metrics(X0: np.ndarray, X1: np.ndarray) -> dict:
    L0, L1 = length(X0), length(X1)
    kmean, krms = curvature_stats(X1)
    ds_mean, ds_cv = segment_stats(X1)
    return {
        "length_initial": L0,
        "length_final": L1,
        "length_rel_drift": (L1-L0)/(L0+1e-30),
        "curvature_mean_final": kmean,
        "curvature_rms_final": krms,
        "mean_segment_final": ds_mean,
        "segment_cv_final": ds_cv,
        "min_nonlocal_distance_final": min_nonlocal_distance(X1),
        "centroid_shift_norm": float(np.linalg.norm(X1.mean(axis=0)-X0.mean(axis=0))),
    }

from __future__ import annotations

import json
import math
from functools import lru_cache
from importlib.resources import files
from typing import Any, Iterable

import numpy as np

DEFAULT_KNOT_IDS: tuple[str, ...] = ("0_1", "3_1", "4_1", "5_2")


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    path = files("fermat_ext").joinpath("data/ideal_knots_subset.json")
    return json.loads(path.read_text(encoding="utf-8"))


def available_knots() -> tuple[str, ...]:
    catalog = load_catalog()
    return tuple(k for k in DEFAULT_KNOT_IDS if k in catalog["knots"])


def knot_metadata(knot_id: str) -> dict[str, Any]:
    catalog = load_catalog()
    try:
        entry = catalog["knots"][knot_id]
    except KeyError as exc:
        raise ValueError(
            f"unknown knot_id={knot_id!r}; available={', '.join(available_knots())}"
        ) from exc
    return {
        "knot_id": knot_id,
        "source_file": catalog["source_file"],
        "source_title": catalog["source_title"],
        "source_author": catalog["source_author"],
        "source_date": catalog["source_date"],
        **{k: v for k, v in entry.items() if k != "coefficients"},
    }


def _fourier_coefficients(knot_id: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    entry = load_catalog()["knots"].get(knot_id)
    if entry is None:
        raise ValueError(f"unknown knot_id={knot_id!r}")
    rows = entry["coefficients"]
    modes = np.asarray([row["i"] for row in rows], dtype=float)
    a = np.asarray([row["A"] for row in rows], dtype=float)
    b = np.asarray([row["B"] for row in rows], dtype=float)
    return modes, a, b


def evaluate_fourier_knot(knot_id: str, t: np.ndarray) -> np.ndarray:
    """Evaluate the uploaded ideal-knot Fourier series at parameter values t."""
    t = np.asarray(t, dtype=float)
    if t.ndim != 1:
        raise ValueError("t must be one-dimensional")
    modes, a, b = _fourier_coefficients(knot_id)
    phases = np.outer(t, modes)
    return np.cos(phases) @ a + np.sin(phases) @ b


def polygon_length(curve: np.ndarray) -> float:
    curve = np.asarray(curve, dtype=float)
    return float(np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1).sum())


def resample_closed_curve_uniform_arclength(curve: np.ndarray, n: int) -> np.ndarray:
    curve = np.asarray(curve, dtype=float)
    if curve.ndim != 2 or curve.shape[1] != 3 or len(curve) < 4:
        raise ValueError("curve must have shape (N,3), N>=4")
    if n < 16:
        raise ValueError("n>=16 required")
    closed = np.vstack((curve, curve[0]))
    ds = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    if np.any(ds <= 1e-15):
        keep = np.concatenate(([True], ds[:-1] > 1e-15))
        curve = curve[keep]
        closed = np.vstack((curve, curve[0]))
        ds = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    s = np.concatenate(([0.0], np.cumsum(ds)))
    total = float(s[-1])
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("degenerate curve length")
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = np.column_stack([np.interp(targets, s, closed[:, j]) for j in range(3)])
    return out


def sample_ideal_knot(
    knot_id: str,
    n: int = 512,
    *,
    scale_over_rc: float = 1.0,
    uniform_arclength: bool = True,
    oversample_factor: int = 8,
) -> np.ndarray:
    """
    Sample one of the four bundled ideal-knot centerlines.

    The uploaded source normalization has D=1. ``scale_over_rc`` uniformly
    multiplies those coordinates; no physical core radius is inferred here.
    """
    if scale_over_rc <= 0.0:
        raise ValueError("scale_over_rc must be positive")
    if n < 16:
        raise ValueError("n>=16 required")
    dense_n = max(4096, n * max(2, oversample_factor)) if uniform_arclength else n
    t = np.linspace(0.0, 2.0 * math.pi, dense_n, endpoint=False)
    curve = evaluate_fourier_knot(knot_id, t)
    curve -= curve.mean(axis=0, keepdims=True)
    if uniform_arclength:
        curve = resample_closed_curve_uniform_arclength(curve, n)
    curve *= scale_over_rc
    return curve


def centerline_summary(curve: np.ndarray, knot_id: str | None = None) -> dict[str, Any]:
    curve = np.asarray(curve, dtype=float)
    edges = np.roll(curve, -1, axis=0) - curve
    lengths = np.linalg.norm(edges, axis=1)
    centroid = curve.mean(axis=0)
    bbox_min = curve.min(axis=0)
    bbox_max = curve.max(axis=0)
    out: dict[str, Any] = {
        "point_count": int(len(curve)),
        "polygon_length_over_rc": float(lengths.sum()),
        "edge_length_mean_over_rc": float(lengths.mean()),
        "edge_length_cv": float(lengths.std() / lengths.mean()),
        "centroid_norm_over_rc": float(np.linalg.norm(centroid)),
        "bbox_min_over_rc": bbox_min.tolist(),
        "bbox_max_over_rc": bbox_max.tolist(),
        "bbox_extent_over_rc": (bbox_max - bbox_min).tolist(),
        "implicit_closure_edge_over_rc": float(lengths[-1]),
    }
    if knot_id is not None:
        meta = knot_metadata(knot_id)
        scale_estimate = float(np.mean(np.linalg.norm(curve, axis=1)))
        source_length = float(meta["source_length_L"])
        # Since the curve may be uniformly scaled, infer the applied scale from
        # its coordinate norm relative to a reference sample rather than claim D.
        ref = sample_ideal_knot(knot_id, n=max(1024, len(curve)), scale_over_rc=1.0)
        ref_length = polygon_length(ref)
        inferred_scale = out["polygon_length_over_rc"] / ref_length
        expected_length = source_length * inferred_scale
        out.update({
            "source_length_L": source_length,
            "source_diameter_D": float(meta["source_diameter_D"]),
            "inferred_uniform_scale_over_rc": inferred_scale,
            "source_length_expected_over_rc": expected_length,
            "source_length_relative_error": (
                abs(out["polygon_length_over_rc"] - expected_length) / max(expected_length, 1e-30)
            ),
            "mean_radius_over_rc": scale_estimate,
        })
    return out


def validate_knot_ids(knot_ids: Iterable[str]) -> tuple[str, ...]:
    requested = tuple(knot_ids)
    if not requested:
        raise ValueError("at least one knot id is required")
    known = set(available_knots())
    missing = [k for k in requested if k not in known]
    if missing:
        raise ValueError(f"unknown knots: {missing}; available={sorted(known)}")
    return requested

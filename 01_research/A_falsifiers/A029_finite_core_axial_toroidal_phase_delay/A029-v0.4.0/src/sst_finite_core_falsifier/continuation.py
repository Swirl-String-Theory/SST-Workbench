"""Thin same-branch continuation reuse of eigen.track_mode / vector_overlap."""

from __future__ import annotations

from typing import Any, Callable

from .eigen import track_mode, vector_overlap

AMBIGUOUS = "DISPERSION_BRANCH_AMBIGUOUS"


def continue_same_branch(
    mode_ref: dict[str, Any] | None,
    spec_closed: dict[str, Any],
    *,
    min_overlap: float,
    max_residual: float = 1e-7,
    tracker: Callable = track_mode,
) -> dict[str, Any]:
    tracked = tracker(mode_ref, spec_closed, min_overlap, max_residual)
    overlap = vector_overlap(mode_ref, tracked) if tracked is not None else 0.0
    if tracked is None or overlap < float(min_overlap):
        return {
            "status": AMBIGUOUS,
            "ambiguity_status": AMBIGUOUS,
            "branch_overlap": float(overlap),
            "mode": None,
        }
    return {
        "status": "unique",
        "ambiguity_status": "unique",
        "branch_overlap": float(overlap),
        "mode": tracked,
    }


def b_overlap(q_j: Any, q_jp: Any, B=None) -> float:
    """Normalized adjacent overlap. If B is None, use the Euclidean inner product."""
    import numpy as np

    x = np.asarray(q_j)
    y = np.asarray(q_jp)
    if B is None:
        return float(abs(np.vdot(x, y)) / max(np.linalg.norm(x) * np.linalg.norm(y), 1e-30))
    Bx = B @ x
    By = B @ y
    return float(abs(np.vdot(x, By)) / max(np.sqrt(abs(np.vdot(x, Bx)) * abs(np.vdot(y, By))), 1e-30))

from __future__ import annotations

import math
from typing import Any

from .knot_catalog import knot_metadata


def _round_up(value: int, multiple: int) -> int:
    if multiple <= 0:
        raise ValueError("multiple must be positive")
    return int(math.ceil(value / multiple) * multiple)


def resolution_plan(
    knot_id: str,
    *,
    epsilon: float,
    scale_over_rc: float = 1.0,
    target_ds_over_epsilon: float = 1.0,
    min_points: int = 128,
    max_points: int = 8192,
    round_to: int = 16,
) -> dict[str, Any]:
    """Plan centerline resolution from the source length and softening scale.

    The target is a discretization diagnostic, not a proof of convergence:

        mean(Delta s) / epsilon <= target_ds_over_epsilon.
    """
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    if scale_over_rc <= 0.0:
        raise ValueError("scale_over_rc must be positive")
    if target_ds_over_epsilon <= 0.0:
        raise ValueError("target_ds_over_epsilon must be positive")
    if min_points < 16 or max_points < min_points:
        raise ValueError("require 16<=min_points<=max_points")

    meta = knot_metadata(knot_id)
    expected_length = float(meta["source_length_L"]) * scale_over_rc
    required_raw = int(math.ceil(expected_length / (epsilon * target_ds_over_epsilon)))
    required_rounded = max(min_points, _round_up(required_raw, round_to))
    selected = min(required_rounded, max_points)
    expected_ratio = expected_length / (selected * epsilon)
    target_met = selected >= required_rounded

    return {
        "knot_id": knot_id,
        "source_length_expected_over_rc": expected_length,
        "epsilon_over_rc": epsilon,
        "target_ds_over_epsilon": target_ds_over_epsilon,
        "required_points_uncapped": required_raw,
        "required_points_rounded": required_rounded,
        "selected_points": selected,
        "max_points": max_points,
        "expected_mean_ds_over_epsilon": expected_ratio,
        "target_met_by_plan": target_met,
        "classification": "TARGET_MET_BY_PLAN" if target_met else "CAPPED_UNDERRESOLVED_BY_PLAN",
    }
